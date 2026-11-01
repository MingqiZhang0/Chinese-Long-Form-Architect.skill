using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Text.Json;
using Workbench.Protocol;
namespace Workbench.Infrastructure;
public sealed record Presentation(SnapshotLease Lease,KnowledgeResult Knowledge,TraceResult Trace,EvidenceResult? Evidence,ManuscriptPage Page,IssuePage Issues,SemanticDiff? Diff);
public sealed class PresentationModel(IWorkbenchClient client,string projectPath) : INotifyPropertyChanged
{
    ProjectInfo? project; CancellationTokenSource? queryCancel;
    long epoch;QuerySelection? selected;
    public event PropertyChangedEventHandler? PropertyChanged;
    public event Action<Presentation>? Changed;
    public Presentation? Current {get;private set;}
    string status="STARTING";
    public string Status {get=>status;private set{status=value;Notify();}}
    public bool Developer {get;set;}
    public List<RequestMetadata> Metadata {get;}=[];
    void Notify([CallerMemberName]string? name=null)=>PropertyChanged?.Invoke(this,new(name));
    public async Task StartAsync(CancellationToken ct)
    {
        client.Unavailable+=message=>{Interlocked.Increment(ref epoch);Status="ENGINE_UNAVAILABLE: "+message;};
        client.RequestCompleted+=m=>{lock(Metadata){Metadata.Add(m);if(Metadata.Count>100)Metadata.RemoveAt(0);}};
        client.SnapshotPublished+=e=>{if(project?.ProjectId==e.ProjectId && selected!=null)_=SelectAsync(selected,e.SnapshotId);};
        try
        {
            Status="NEGOTIATING";await client.StartAsync(ct);Status="PROJECT_LOADING";project=await client.OpenAsync(projectPath,ct);
            await client.QueryAsync<ControlAck>("observation.subscribe",new{project_token=project.ProjectToken},ct);Status="READY";
        }
        catch(Exception ex){Status="ENGINE_UNAVAILABLE: "+ex.Message;throw;}
    }
    public async Task SelectAsync(QuerySelection selection,SnapshotId? snapshot=null)
    {
        selected=selection;long own=Interlocked.Increment(ref epoch);
        queryCancel?.Cancel();queryCancel=new();var ct=queryCancel.Token;SnapshotLease? candidate=null;
        try
        {
            if(project==null)throw new EngineException("ENGINE_UNAVAILABLE","Project unavailable");
            Status="UPDATING";
            candidate=await client.PinAsync(project.ProjectToken,snapshot,ct);
            var query=await client.QueryAsync<KnowledgeResult>("state.query",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,domain="actor_epistemic",character_id=selection.Character,fact_id=selection.Fact,position=selection.Position},ct);
            var trace=await client.QueryAsync<TraceResult>("trace.query",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,node_id=query.KnowledgeId.Length>0?query.KnowledgeId:"missing"},ct);
            EvidenceResult? evidence=null;
            if(query.EvidenceRefs.Count>0)evidence=await client.QueryAsync<EvidenceResult>("source.resolve",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,evidence_id=query.EvidenceRefs[0]},ct);
            var page=await client.QueryAsync<ManuscriptPage>("manuscript.page",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,start_block=0,limit=20,anchor_id=""},ct);
            var issues=await client.QueryAsync<IssuePage>("issue.page",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,offset=0,limit=1000,filter=""},ct);
            SemanticDiff? diff=null;
            var old=Current;
            if(old!=null && old.Lease.SnapshotId!=candidate.SnapshotId)diff=await client.QueryAsync<SemanticDiff>("snapshot.compare",new{project_token=project.ProjectToken,snapshot_id=candidate.SnapshotId,lease_id=candidate.LeaseId,before_snapshot_id=old.Lease.SnapshotId,before_lease_id=old.Lease.LeaseId},ct);
            if(own!=Interlocked.Read(ref epoch) || ct.IsCancellationRequested)return;
            // One immutable context becomes visible. Every panel consumes exactly this object.
            Current=new(candidate,query,trace,evidence,page,issues,diff);candidate=null;
            Status=query.Freshness==Freshness.STALE?"STALE_ANALYSIS":"UP_TO_DATE";Changed?.Invoke(Current);
            if(old!=null)await client.ReleaseAsync(project.ProjectToken,old.Lease.LeaseId);
        }
        catch(OperationCanceledException){}
        catch(Exception ex){if(own==Interlocked.Read(ref epoch))Status="ERROR: "+ex.Message;}
        finally
        {
            if(candidate!=null && project!=null)try{await client.ReleaseAsync(project.ProjectToken,candidate.LeaseId);}catch(EngineException){}
        }
    }
    public async Task PageAsync(int start,bool evidence=false)
    {
        var context=Current;if(context==null || project==null)return;
        var own=Interlocked.Read(ref epoch);
        try
        {
            var page=await client.QueryAsync<ManuscriptPage>("manuscript.page",new{project_token=project.ProjectToken,snapshot_id=context.Lease.SnapshotId,lease_id=context.Lease.LeaseId,start_block=Math.Max(0,start),limit=20,anchor_id=evidence?context.Evidence?.AnchorId.Value??"":""},CancellationToken.None);
            if(own!=Interlocked.Read(ref epoch) || Current!=context)return;
            Current=context with{Page=page};Changed?.Invoke(Current);
        }
        catch(Exception ex){if(own==Interlocked.Read(ref epoch))Status="ERROR: "+ex.Message;}
    }
    public async Task CheckWatchAsync()
    {
        var current=Current;if(current==null || project==null)return;
        try
        {
            var result=await client.QueryAsync<SnapshotInfo>("snapshot.get",new{project_token=project.ProjectToken,snapshot_id=current.Lease.SnapshotId,lease_id=current.Lease.LeaseId},CancellationToken.None);
            if(Current==current && result.WatchStatus=="ERROR")Status="ERROR: update failed; previous stable snapshot retained. "+result.FailedCandidate;
            else if(Current==current && result.WatchStatus is "CHANGE_DETECTED" or "UPDATING")Status=result.WatchStatus;
        }
        catch(EngineException ex){Status="ENGINE_UNAVAILABLE: "+ex.Message;}
    }
    public async Task<IssuePage?> IssuesAsync(string filter="",int offset=0)
    {
        var context=Current;if(context==null || project==null)return null;
        return await client.QueryAsync<IssuePage>("issue.page",new{project_token=project.ProjectToken,snapshot_id=context.Lease.SnapshotId,lease_id=context.Lease.LeaseId,offset,limit=1000,filter},CancellationToken.None);
    }
    public string DeveloperText(Presentation p)
    {
        RequestMetadata? last;lock(Metadata)last=Metadata.LastOrDefault();
        return $"ProjectId: {p.Lease.ProjectId}\nSnapshotId: {p.Lease.SnapshotId}\nCharacterId: {p.Knowledge.CharacterId}\nFactId: {p.Knowledge.FactId}\nIssueId: {p.Issues.Issues.FirstOrDefault()?.IssueId}\nEvidenceId: {p.Evidence?.EvidenceId}\nAnchorId: {p.Evidence?.AnchorId}\nRequestId: {last?.RequestId}\nMethod: {last?.Method}\nDuration: {last?.DurationMs:F2} ms\nPayload: {last?.PayloadBytes} bytes\nCompleteness: {p.Knowledge.Completeness}\nFreshness: {p.Knowledge.Freshness}\nManifest: {JsonSerializer.Serialize(p.Knowledge.Manifest,WireJson.Options)}\nDiff: {JsonSerializer.Serialize(p.Diff,WireJson.Options)}";
    }
}
