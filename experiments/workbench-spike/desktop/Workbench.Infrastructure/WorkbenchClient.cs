using Workbench.Protocol;
namespace Workbench.Infrastructure;
public sealed class WorkbenchClient(string root,string python,string? frozen=null,string? testDelays=null,double startupDelay=0) : IWorkbenchClient
{
    readonly ProcessSupervisor supervisor=new();FramedTransport? transport;
    public event Action<SnapshotEvent>? SnapshotPublished;
    public event Action<string>? Unavailable;
    public event Action<RequestMetadata>? RequestCompleted;
    public Hello? Hello {get;private set;}
    public long EngineWorkingSet { get { if(Hello?.ServerProcessId is int pid){using var engine=System.Diagnostics.Process.GetProcessById(pid);engine.Refresh();return engine.WorkingSet64;}return supervisor.WorkingSet;} }
    public void KillForTest()=>supervisor.KillForTest();
    public async Task StartAsync(CancellationToken ct)
    {
        var args=new List<string>();
        if(frozen==null)args.AddRange(["-B",Path.Combine(root,"experiments/workbench-spike/service/host.py")]);
        if(testDelays!=null)args.AddRange(["--test-delays",testDelays]);
        if(startupDelay>0)args.AddRange(["--startup-delay",startupDelay.ToString(System.Globalization.CultureInfo.InvariantCulture)]);
        var process=supervisor.Launch(frozen??python,args,root);
        var schemaPath=Path.Combine(root,"docs/workbench/contracts/workbench-wire.schema.json");
        transport=new(process.StandardOutput.BaseStream,process.StandardInput.BaseStream,new(schemaPath));
        transport.Event+=e=>SnapshotPublished?.Invoke(e);transport.Failed+=e=>Unavailable?.Invoke(e);transport.Completed+=e=>
        {
            System.Diagnostics.Trace.WriteLine(System.Text.Json.JsonSerializer.Serialize(new{timestamp=DateTimeOffset.UtcNow,component="WorkbenchClient",severity="info",@event="request_terminal",request_id=e.RequestId,correlation_id=e.RequestId,snapshot_id=e.SnapshotId,engine_instance=Hello?.ServerInstanceId,method=e.Method,duration_ms=e.DurationMs,payload_bytes=e.PayloadBytes}));
            RequestCompleted?.Invoke(e);
        };
        using var timeout=CancellationTokenSource.CreateLinkedTokenSource(ct);timeout.CancelAfter(TimeSpan.FromSeconds(10));
        try
        {
            Hello=await transport.CallAsync<Hello>("hello",new{supported_versions=new[]{"1.0.0"},client_version="spike-1",max_frame_bytes=8*1024*1024},timeout.Token);
            if(Hello.SelectedVersion!="1.0.0" || Hello.SchemaDigest!=ContractIdentity.Digest)throw new InvalidDataException("Schema/version mismatch");
        }
        catch{await DisposeAsync();throw;}
    }
    public Task<ProjectInfo> OpenAsync(string path,CancellationToken ct)=>QueryAsync<ProjectInfo>("session.open",new{project_root=path},ct);
    public async Task<SnapshotLease> PinAsync(ProjectToken p,SnapshotId? s,CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        // Lease creation is an atomic control operation: always receive its ID so a cancelled navigation can release it.
        var lease=await QueryAsync<SnapshotLease>("snapshot.pin",new{project_token=p,requested_snapshot_id=s},CancellationToken.None);
        if(ct.IsCancellationRequested){await ReleaseAsync(p,lease.LeaseId);ct.ThrowIfCancellationRequested();}
        return lease;
    }
    public Task<T> QueryAsync<T>(string method,object parameters,CancellationToken ct)=>transport?.CallAsync<T>(method,parameters,ct)??Task.FromException<T>(new EngineException("ENGINE_UNAVAILABLE","Start engine first"));
    public async Task ReleaseAsync(ProjectToken p,LeaseId lease)=>await QueryAsync<ControlAck>("snapshot.release",new{project_token=p,lease_id=lease},CancellationToken.None);
    public async ValueTask DisposeAsync()
    {
        if(transport!=null)
        {
            try{await transport.CallAsync<ControlAck>("service.shutdown",new{},CancellationToken.None).WaitAsync(TimeSpan.FromSeconds(2));}catch(Exception ex) when(ex is IOException or EngineException or TimeoutException or OperationCanceledException){}
            await transport.DisposeAsync();transport=null;
        }
        await supervisor.DisposeAsync();
    }
}
