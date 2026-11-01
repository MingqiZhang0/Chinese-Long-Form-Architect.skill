using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Workbench.Infrastructure;
using Workbench.Protocol;

string root=Path.GetFullPath(args[0]);string python=args[1];string? frozen=args.Length>2?args[2]:null;
string spike=Path.Combine(root,"experiments/workbench-spike");var checks=new List<string>();var metrics=new Dictionary<string,double>();
void Check(bool value,string name){if(!value)throw new InvalidOperationException(name);checks.Add(name);}
var schema=new SchemaBoundary(Path.Combine(root,"docs/workbench/contracts/workbench-wire.schema.json"));
foreach(var goldenFile in new[]{"golden-wire.json","spike-golden-wire.json"})
{
var gold=JsonDocument.Parse(File.ReadAllBytes(Path.Combine(root,"docs/workbench/contracts",goldenFile))).RootElement;
foreach(var group in new[]{"valid","invalid"})foreach(var row in gold.GetProperty(group).EnumerateArray())
{
    var message=row.GetProperty("message");bool accepted;
    try{schema.Validate(message,message.TryGetProperty("method",out _)?"Request":message.TryGetProperty("event",out _)?"SnapshotEvent":message.TryGetProperty("error",out _)?"ErrorResponse":"SuccessResponse");accepted=true;}catch(JsonException){accepted=false;}
    Check(accepted==(group=="valid"),"golden "+row.GetProperty("name").GetString());
    if(accepted && message.TryGetProperty("result",out var result))
    {
        var kind=result.GetProperty("kind").GetString()!;var type=typeof(Hello).Assembly.GetType("Workbench.Protocol."+kind)!;
        var dto=result.Deserialize(type,WireJson.Options)!;var serialized=JsonSerializer.SerializeToElement(dto,type,WireJson.Options);
        Check(JsonElement.DeepEquals(result,serialized),"typed re-encode "+kind);
    }
}
}
var unicode="薛照𠮷🙂e\u0301\r\nEnglish\n";
for(int i=0;i<=unicode.EnumerateRunes().Count();i++)Check(UnicodeOffsets.ToUtf16(unicode,i)==unicode.EnumerateRunes().Take(i).Sum(r=>r.Utf16SequenceLength),"scalar mapping "+i);
foreach(var bad in new byte[][]{[0], [0,128,0,1], [0,0,0,1,255], [0,0,0,3,123,125]})
{
    bool failed=false;try{await FramedTransport.ReadFrameAsync(new MemoryStream(bad),CancellationToken.None);}catch(Exception ex) when(ex is IOException or InvalidDataException or DecoderFallbackException){failed=true;}
    Check(failed,"malformed frame");
}
string temp=Path.Combine(Path.GetTempPath(),"叙事 spike "+Guid.NewGuid());Directory.CreateDirectory(temp);
try
{
    var generate=new ProcessStartInfo(python){UseShellExecute=false,RedirectStandardError=true};generate.ArgumentList.Add(Path.Combine(spike,"fixture.py"));generate.ArgumentList.Add(temp);
    using(var process=Process.Start(generate)!){await process.WaitForExitAsync();Check(process.ExitCode==0,"fixture generation");}
    object Query(ProjectInfo p,SnapshotLease s,string actor,string fact,double day)=>new{project_token=p.ProjectToken,snapshot_id=s.SnapshotId,lease_id=s.LeaseId,domain="actor_epistemic",character_id=new CharacterId(actor),fact_id=new FactId(fact),position=new NarrativePosition("story_valid","day",day,"at","CH3")};
    string instance;
    await using(var client=new WorkbenchClient(root,python,frozen,testDelays:"{\"A\":0.12,\"B\":0.04}"))
    {
        client.RequestCompleted+=m=>metrics[m.Method+"_ms"]=m.DurationMs;
        var t=Stopwatch.StartNew();await client.StartAsync(CancellationToken.None);metrics["cold_handshake_ms"]=t.Elapsed.TotalMilliseconds;instance=client.Hello!.ServerInstanceId;
        var p=await client.OpenAsync(temp,CancellationToken.None);var s1=await client.PinAsync(p.ProjectToken,null,CancellationToken.None);
        var k=await client.QueryAsync<KnowledgeResult>("state.query",Query(p,s1,"A","F1",3),CancellationToken.None);
        Check(k.EpistemicState==EpistemicState.KNOWN && k.Completeness==Completeness.FULL,"real owner historical known FULL");
        var retired=await client.QueryAsync<KnowledgeResult>("state.query",Query(p,s1,"A","F1",5),CancellationToken.None);Check(retired.EpistemicState==EpistemicState.UNKNOWN,"retired stays retired");
        var missing=await client.QueryAsync<KnowledgeResult>("state.query",Query(p,s1,"A","F2",3),CancellationToken.None);Check(missing.EpistemicState==EpistemicState.UNKNOWN && missing.Completeness==Completeness.PARTIAL,"untimed is PARTIAL UNKNOWN");
        var why=await client.QueryAsync<TraceResult>("trace.query",new{project_token=p.ProjectToken,snapshot_id=s1.SnapshotId,lease_id=s1.LeaseId,node_id=k.KnowledgeId},CancellationToken.None);
        Check(why.Edges.Count==7 && why.Completeness==Completeness.FULL,"all 7 provenance edges including shared support");
        Check(k.Manifest.AgentCalls==0 && why.Manifest.AgentCalls==0,"agent zero assertion");
        var slowResponse=client.QueryAsync<KnowledgeResult>("state.query",Query(p,s1,"A","F1",3),CancellationToken.None);
        var fastResponse=client.QueryAsync<KnowledgeResult>("state.query",Query(p,s1,"B","F1",3),CancellationToken.None);
        Check(await Task.WhenAny(slowResponse,fastResponse)==fastResponse,"responses arrive out of request order");await Task.WhenAll(slowResponse,fastResponse);
        var ev=await client.QueryAsync<EvidenceResult>("source.resolve",new{project_token=p.ProjectToken,snapshot_id=s1.SnapshotId,lease_id=s1.LeaseId,evidence_id=new EvidenceId("EV1")},CancellationToken.None);
        var page=await client.QueryAsync<ManuscriptPage>("manuscript.page",new{project_token=p.ProjectToken,snapshot_id=s1.SnapshotId,lease_id=s1.LeaseId,start_block=0,limit=20,anchor_id=ev.AnchorId.Value},CancellationToken.None);
        var block=page.Blocks[0];Check(block.Text[UnicodeOffsets.ToUtf16(block.Text,ev.Span.Start-block.Start)..UnicodeOffsets.ToUtf16(block.Text,ev.Span.End-block.Start)]==ev.DisplayText,"C# exact Unicode evidence span");
        var notice=new TaskCompletionSource<SnapshotEvent>(TaskCreationOptions.RunContinuationsAsynchronously);client.SnapshotPublished+=e=>notice.TrySetResult(e);
        await client.QueryAsync<ControlAck>("observation.subscribe",new{project_token=p.ProjectToken},CancellationToken.None);
        var source=Path.Combine(temp,"manuscript.txt");var text=await File.ReadAllTextAsync(source);t.Restart();
        // Test is the external editor; the service exposes no write method.
        await File.WriteAllTextAsync(source,text.Replace("<!-- block:proof -->\n𠮷🙂 e\u0301 薛照亲眼确认：钥匙是蓝色的。\r\n\r\n",""),new UTF8Encoding(false));
        var published=await notice.Task.WaitAsync(TimeSpan.FromSeconds(6));metrics["snapshot_external_publish_ms"]=t.Elapsed.TotalMilliseconds;
        var s2=await client.PinAsync(p.ProjectToken,published.SnapshotId,CancellationToken.None);
        var broken=await client.QueryAsync<EvidenceResult>("source.resolve",new{project_token=p.ProjectToken,snapshot_id=s2.SnapshotId,lease_id=s2.LeaseId,evidence_id=new EvidenceId("EV1")},CancellationToken.None);
        Check(broken.Health==EvidenceHealth.BROKEN,"S2 evidence BROKEN");
        var historical=await client.QueryAsync<EvidenceResult>("source.resolve",new{project_token=p.ProjectToken,snapshot_id=s1.SnapshotId,lease_id=s1.LeaseId,evidence_id=new EvidenceId("EV1")},CancellationToken.None);Check(historical.Health==EvidenceHealth.VALID,"S1 immutable source survives S2");
        var stale=await client.QueryAsync<KnowledgeResult>("state.query",Query(p,s2,"A","F1",3),CancellationToken.None);Check(stale.Completeness==Completeness.PARTIAL && stale.Freshness==Freshness.STALE,"S2 query visibly PARTIAL STALE");
        var diff=await client.QueryAsync<SemanticDiff>("snapshot.compare",new{project_token=p.ProjectToken,snapshot_id=s2.SnapshotId,lease_id=s2.LeaseId,before_snapshot_id=s1.SnapshotId,before_lease_id=s1.LeaseId},CancellationToken.None);Check(diff.ChangedEvidence.Count==1 && !diff.CanonicalChanged,"structured S1 S2 diff, canonical unchanged");
        using(var cancel=new CancellationTokenSource())
        {
            var slow=client.QueryAsync<KnowledgeResult>("state.query",Query(p,s2,"A","F1",3),cancel.Token);cancel.Cancel();bool cancelled=false;
            try{await slow;}catch(OperationCanceledException){cancelled=true;}Check(cancelled,"cancel wins");
        }
        var terminal=await client.QueryAsync<KnowledgeResult>("state.query",Query(p,s2,"B","F1",3),CancellationToken.None);Check(terminal!=null,"result wins without duplicate terminal");
        var statePath=Path.Combine(temp,"canonical/state.json");var originalState=await File.ReadAllBytesAsync(statePath);await File.WriteAllTextAsync(statePath,"{");
        using(var timer=new PeriodicTimer(TimeSpan.FromMilliseconds(50)))
        {
            bool retained=false;var deadline=Stopwatch.StartNew();
            while(deadline.Elapsed<TimeSpan.FromSeconds(5) && await timer.WaitForNextTickAsync())
            {
                var info=await client.QueryAsync<SnapshotInfo>("snapshot.get",new{project_token=p.ProjectToken,snapshot_id=s2.SnapshotId,lease_id=s2.LeaseId},CancellationToken.None);
                if(info.WatchStatus=="ERROR"){retained=info.SnapshotId==s2.SnapshotId && info.FailedCandidate.Length>0;break;}
            }
            Check(retained,"failed candidate keeps last stable snapshot");
        }
        await File.WriteAllBytesAsync(statePath,originalState);
        var down=new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);client.Unavailable+=s=>down.TrySetResult(s);
        client.KillForTest();await down.Task.WaitAsync(TimeSpan.FromSeconds(3));
        bool unavailable=false;try{await client.QueryAsync<Health>("health.query",new{},CancellationToken.None);}catch(EngineException e){unavailable=e.Code=="ENGINE_UNAVAILABLE";}
        Check(unavailable,"backend crash makes uncached queries unavailable");
    }
    await using(var restarted=new WorkbenchClient(root,python,frozen))
    {
        await restarted.StartAsync(CancellationToken.None);Check(restarted.Hello!.ServerInstanceId!=instance,"restart new engine instance");var p=await restarted.OpenAsync(temp,CancellationToken.None);var s=await restarted.PinAsync(p.ProjectToken,null,CancellationToken.None);Check(true,"restart new session and lease");
        var warm=new List<RequestMetadata>();restarted.RequestCompleted+=m=>warm.Add(m);
        for(int i=0;i<30;i++)
        {
            await restarted.QueryAsync<KnowledgeResult>("state.query",Query(p,s,"A","F1",3),CancellationToken.None);
            await restarted.QueryAsync<TraceResult>("trace.query",new{project_token=p.ProjectToken,snapshot_id=s.SnapshotId,lease_id=s.LeaseId,node_id="K1"},CancellationToken.None);
            await restarted.QueryAsync<EvidenceResult>("source.resolve",new{project_token=p.ProjectToken,snapshot_id=s.SnapshotId,lease_id=s.LeaseId,evidence_id=new EvidenceId("EV1")},CancellationToken.None);
            await restarted.QueryAsync<ManuscriptPage>("manuscript.page",new{project_token=p.ProjectToken,snapshot_id=s.SnapshotId,lease_id=s.LeaseId,start_block=0,limit=20,anchor_id=""},CancellationToken.None);
        }
        foreach(var group in warm.GroupBy(m=>m.Method))
        {
            var values=group.Select(m=>m.DurationMs).Order().ToArray();metrics[group.Key+"_warm_p50_ms"]=values[values.Length/2];metrics[group.Key+"_warm_p95_ms"]=values[(int)Math.Ceiling(values.Length*.95)-1];
        }
    }
    // The ViewModel itself rejects late results, independent of service cancellation.
    await using(var racing=new WorkbenchClient(root,python,frozen,testDelays:"{\"A\":0.12,\"B\":0.04}"))
    {
        var model=new PresentationModel(racing,temp);await model.StartAsync(CancellationToken.None);
        var pos=new NarrativePosition("story_valid","day",3,"at","CH3");
        for(int i=0;i<100;i++)
        {
            var a=model.SelectAsync(new(new("A"),new("F1"),pos));var b=model.SelectAsync(new(new("A"),new("F2"),pos));var c=model.SelectAsync(new(new("B"),new("F2"),pos));
            await Task.WhenAll(a,b,c);Check(model.Current?.Knowledge.CharacterId==new CharacterId("B") && model.Current.Knowledge.FactId==new FactId("F2"),"latest selection C "+i);
        }
        var semantic=JsonSerializer.Serialize(model.Current!.Knowledge,WireJson.Options);model.Developer=true;_ =model.DeveloperText(model.Current);model.Developer=false;
        Check(semantic==JsonSerializer.Serialize(model.Current.Knowledge,WireJson.Options),"Developer OFF ON semantic invariant");
    }
}
finally{Directory.Delete(temp,true);}
var report=JsonSerializer.Serialize(new{passed=true,checks_count=checks.Count,checks,metrics},new JsonSerializerOptions{WriteIndented=true});
File.WriteAllText(Path.Combine(spike,frozen==null?"artifacts/csharp-tests.json":"artifacts/csharp-frozen-tests.json"),report);Console.WriteLine($"PASS {checks.Count} checks; "+JsonSerializer.Serialize(metrics));
