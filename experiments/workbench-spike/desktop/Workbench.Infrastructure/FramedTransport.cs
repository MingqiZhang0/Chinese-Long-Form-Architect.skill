using System.Buffers.Binary;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Workbench.Protocol;

namespace Workbench.Infrastructure;
public sealed class EngineException(string code,string message) : Exception(message) { public string Code { get; }=code; }
public sealed class FramedTransport : IAsyncDisposable
{
    const int Max=8*1024*1024;
    readonly Stream input,output;
    readonly SchemaBoundary schema;
    readonly SemaphoreSlim writer=new(1),capacity=new(128);
    readonly CancellationTokenSource closed=new();
    readonly ConcurrentDictionary<string,TaskCompletionSource<JsonElement>> pending=new();
    readonly Task reader;
    public event Action<SnapshotEvent>? Event;
    public event Action<string>? Failed;
    public event Action<RequestMetadata>? Completed;
    public FramedTransport(Stream input,Stream output,SchemaBoundary schema)
    {this.input=input;this.output=output;this.schema=schema;reader=Task.Run(ReadLoop);}
    public static async Task<byte[]?> ReadFrameAsync(Stream input,CancellationToken ct)
    {
        var header=new byte[4];var count=await input.ReadAsync(header.AsMemory(0,4),ct);
        if(count==0)return null;
        await input.ReadExactlyAsync(header.AsMemory(count),ct);
        uint size=BinaryPrimitives.ReadUInt32BigEndian(header);
        if(size==0 || size>Max)throw new InvalidDataException("Invalid frame length");
        var body=new byte[(int)size];await input.ReadExactlyAsync(body,ct);
        // JSON parser alone may replace invalid UTF-8; explicitly fail closed first.
        new UTF8Encoding(false,true).GetString(body);
        return body;
    }
    async Task ReadLoop()
    {
        try
        {
            while(!closed.IsCancellationRequested)
            {
                var bytes=await ReadFrameAsync(input,closed.Token) ?? throw new EndOfStreamException("Engine EOF");
                var value=JsonDocument.Parse(bytes).RootElement.Clone();
                if(value.TryGetProperty("event",out _)){schema.Validate(value,"SnapshotEvent");Event?.Invoke(WireJson.Decode<SnapshotEvent>(value));continue;}
                schema.Validate(value,value.TryGetProperty("error",out _)?"ErrorResponse":"SuccessResponse");
                if(pending.TryRemove(value.GetProperty("request_id").GetString()!,out var promise))promise.TrySetResult(value);
            }
        }
        catch(Exception ex)
        { foreach(var p in pending.Values)p.TrySetException(new EngineException("ENGINE_UNAVAILABLE",ex.Message));pending.Clear();Failed?.Invoke(ex.Message);closed.Cancel(); }
    }
    async Task SendAsync(byte[] bytes,CancellationToken ct)
    {
        if(bytes.Length>Max)throw new InvalidDataException("Oversize request");
        await writer.WaitAsync(ct);
        try
        {
            var header=new byte[4];BinaryPrimitives.WriteUInt32BigEndian(header,(uint)bytes.Length);
            // Once the header begins, cancellation must not truncate an active frame.
            await output.WriteAsync(header,closed.Token);await output.WriteAsync(bytes,closed.Token);await output.FlushAsync(closed.Token);
        }
        finally{writer.Release();}
    }
    public async Task<T> CallAsync<T>(string method,object parameters,CancellationToken ct)
    {
        var requestId=new RequestId(Guid.NewGuid().ToString("N"));string id=requestId.Value;var clock=Stopwatch.StartNew();
        var envelope=new {protocol_version="1.0.0",request_id=requestId,correlation_id=id,method,@params=parameters};
        var bytes=JsonSerializer.SerializeToUtf8Bytes(envelope,WireJson.Options);
        var request=JsonDocument.Parse(bytes).RootElement;schema.Validate(request,"Request");
        await capacity.WaitAsync(ct);
        var promise=new TaskCompletionSource<JsonElement>(TaskCreationOptions.RunContinuationsAsynchronously);
        try
        {
            if(closed.IsCancellationRequested)throw new EngineException("ENGINE_UNAVAILABLE","Transport closed");
            pending[id]=promise;await SendAsync(bytes,ct);
            using var registration=ct.Register(()=>{if(promise.TrySetCanceled(ct))_ = CancelAsync(id);});
            var response=await promise.Task.WaitAsync(TimeSpan.FromSeconds(10),ct);
            if(response.GetProperty("correlation_id").GetString()!=id)throw new JsonException("Correlation mismatch");
            if(response.TryGetProperty("error",out var error))throw new EngineException(error.GetProperty("code").GetString()!,error.GetProperty("message").GetString()!);
            var result=response.GetProperty("result");
            if(result.GetProperty("kind").GetString()!=typeof(T).Name)throw new JsonException("Method/result kind mismatch");
            var snapshot=result.TryGetProperty("snapshot_id",out var sid)?sid.GetString()!:result.TryGetProperty("after_snapshot_id",out var after)?after.GetString()!:"";
            if(request.GetProperty("params").TryGetProperty("snapshot_id",out var requested) && requested.GetString()!=snapshot)throw new JsonException("Snapshot mismatch");
            Completed?.Invoke(new(id,method,clock.Elapsed.TotalMilliseconds,bytes.Length+Encoding.UTF8.GetByteCount(response.GetRawText()),snapshot));
            return WireJson.Decode<T>(result);
        }
        finally{pending.TryRemove(id,out _);capacity.Release();}
    }
    async Task CancelAsync(string target)
    {try{await CallAsync<ControlAck>("request.cancel",new {target_request_id=target},closed.Token);}catch(Exception ex) when(ex is OperationCanceledException or EngineException or IOException){}}
    public async ValueTask DisposeAsync()
    {closed.Cancel();await input.DisposeAsync();await output.DisposeAsync();try{await reader;}catch(OperationCanceledException){}closed.Dispose();}
}
