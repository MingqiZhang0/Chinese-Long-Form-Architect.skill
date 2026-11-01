using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace Workbench.Protocol;
public interface IWireId<T> { string Value { get; } static abstract T Create(string value); }
public sealed class IdConverter<T> : JsonConverter<T> where T : IWireId<T>
{
    public override T Read(ref Utf8JsonReader reader, Type type, JsonSerializerOptions options)
    {
        var value=reader.GetString();
        if(string.IsNullOrEmpty(value)) throw new JsonException("Empty nominal ID");
        return T.Create(value);
    }
    public override void Write(Utf8JsonWriter writer,T value,JsonSerializerOptions options)
    { if(string.IsNullOrEmpty(value.Value)) throw new JsonException("Empty nominal ID");writer.WriteStringValue(value.Value); }
}
public static class WireJson
{
    public static readonly JsonSerializerOptions Options = new() { Converters={new JsonStringEnumConverter(allowIntegerValues:false)} };
    public static T Decode<T>(JsonElement element) => element.Deserialize<T>(Options) ?? throw new JsonException("Missing result");
}
// Deliberately limited to the keywords used by this pinned schema; unsupported keywords fail at construction.
public sealed class SchemaBoundary
{
    readonly JsonElement root;
    public SchemaBoundary(string path) { root=JsonDocument.Parse(File.ReadAllBytes(path)).RootElement.Clone();CheckKeywords(root); }
    static void CheckKeywords(JsonElement schema)
    {
        var supported=new HashSet<string>{"$schema","$id","$ref","$defs","title","description","x-id-type","type","oneOf","anyOf","const","enum","properties","required","additionalProperties","items","minItems","minLength","pattern","minimum","maximum"};
        foreach(var p in schema.EnumerateObject())
        {
            if(!supported.Contains(p.Name))throw new JsonException("Unsupported schema keyword: "+p.Name);
            if(p.Name is "$defs" or "properties")foreach(var item in p.Value.EnumerateObject())CheckKeywords(item.Value);
            if(p.Name is "oneOf" or "anyOf")foreach(var item in p.Value.EnumerateArray())CheckKeywords(item);
            if(p.Name=="items")CheckKeywords(p.Value);
        }
    }
    public void Validate(JsonElement value,string definition)
    { if(!Valid(root.GetProperty("$defs").GetProperty(definition),value)) throw new JsonException($"Invalid {definition} contract"); }
    public bool Valid(JsonElement schema,JsonElement value)
    {
        if(schema.TryGetProperty("$ref",out var reference)) return Valid(root.GetProperty("$defs").GetProperty(reference.GetString()!.Split('/').Last()),value);
        if(schema.TryGetProperty("oneOf",out var one) && one.EnumerateArray().Count(x=>Valid(x,value))!=1)return false;
        if(schema.TryGetProperty("anyOf",out var any) && !any.EnumerateArray().Any(x=>Valid(x,value)))return false;
        if(schema.TryGetProperty("const",out var constant) && !JsonElement.DeepEquals(constant,value))return false;
        if(schema.TryGetProperty("enum",out var values) && !values.EnumerateArray().Any(x=>JsonElement.DeepEquals(x,value)))return false;
        if(schema.TryGetProperty("type",out var type))
        {
            bool correct=type.GetString() switch {"object"=>value.ValueKind==JsonValueKind.Object,"array"=>value.ValueKind==JsonValueKind.Array,"string"=>value.ValueKind==JsonValueKind.String,"integer"=>value.ValueKind==JsonValueKind.Number && value.TryGetInt64(out _),"number"=>value.ValueKind==JsonValueKind.Number,"boolean"=>value.ValueKind is JsonValueKind.True or JsonValueKind.False,"null"=>value.ValueKind==JsonValueKind.Null,_=>throw new JsonException("Unsupported schema type")};
            if(!correct)return false;
        }
        if(value.ValueKind==JsonValueKind.Object)
        {
            if(schema.TryGetProperty("required",out var required) && required.EnumerateArray().Any(x=>!value.TryGetProperty(x.GetString()!,out _)))return false;
            if(schema.TryGetProperty("properties",out var props)) foreach(var p in value.EnumerateObject())
            { if(props.TryGetProperty(p.Name,out var s)){if(!Valid(s,p.Value))return false;}else if(schema.TryGetProperty("additionalProperties",out var extra) && extra.ValueKind==JsonValueKind.False)return false; }
        }
        if(value.ValueKind==JsonValueKind.Array)
        {
            if(schema.TryGetProperty("minItems",out var min) && value.GetArrayLength()<min.GetInt32())return false;
            if(schema.TryGetProperty("items",out var items) && value.EnumerateArray().Any(x=>!Valid(items,x)))return false;
        }
        if(value.ValueKind==JsonValueKind.String)
        {
            var text=value.GetString()!;
            if(schema.TryGetProperty("minLength",out var min) && text.EnumerateRunes().Count()<min.GetInt32())return false;
            if(schema.TryGetProperty("pattern",out var pattern) && !Regex.IsMatch(text,pattern.GetString()!,RegexOptions.CultureInvariant,TimeSpan.FromMilliseconds(100)))return false;
        }
        if(value.ValueKind==JsonValueKind.Number)
        {
            if(schema.TryGetProperty("minimum",out var min) && value.GetDouble()<min.GetDouble())return false;
            if(schema.TryGetProperty("maximum",out var max) && value.GetDouble()>max.GetDouble())return false;
        }
        return true;
    }
}
public static class UnicodeOffsets
{
    public static int ToUtf16(string text,int scalar)
    {
        if(scalar<0)throw new ArgumentOutOfRangeException(nameof(scalar));
        int count=0,index=0;
        foreach(var rune in text.EnumerateRunes()){if(count==scalar)return index;index+=rune.Utf16SequenceLength;count++;}
        if(count==scalar)return index;
        throw new ArgumentOutOfRangeException(nameof(scalar));
    }
}
public sealed record QuerySelection(CharacterId Character,FactId Fact,NarrativePosition Position);
public interface IWorkbenchClient : IAsyncDisposable
{
    event Action<SnapshotEvent>? SnapshotPublished;
    event Action<string>? Unavailable;
    event Action<RequestMetadata>? RequestCompleted;
    Hello? Hello { get; }
    Task StartAsync(CancellationToken cancellationToken);
    Task<ProjectInfo> OpenAsync(string project,CancellationToken cancellationToken);
    Task<SnapshotLease> PinAsync(ProjectToken project,SnapshotId? snapshot,CancellationToken cancellationToken);
    Task<T> QueryAsync<T>(string method,object parameters,CancellationToken cancellationToken);
    Task ReleaseAsync(ProjectToken project,LeaseId lease);
}
public sealed record RequestMetadata(string RequestId,string Method,double DurationMs,int PayloadBytes,string SnapshotId);
