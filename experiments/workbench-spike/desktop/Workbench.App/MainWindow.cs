using System.Diagnostics;
using System.Text.Json;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Controls.Templates;
using Avalonia.VisualTree;
using Avalonia.Threading;
using Workbench.Infrastructure;
using Workbench.Protocol;
namespace Workbench.App;
public sealed class MainWindow : Window
{
    readonly TextBlock status=new(){Text="STARTING"},badge=new(){Text="Snapshot: —"},answer=new(){TextWrapping=TextWrapping.Wrap};
    readonly TextBox manuscript=new(){IsReadOnly=true,AcceptsReturn=true,TextWrapping=TextWrapping.Wrap,FontSize=18,FontFamily=new FontFamily("Microsoft YaHei UI, Noto Sans CJK SC, sans-serif")};
    readonly TextBox trace=new(){IsReadOnly=true,AcceptsReturn=true,TextWrapping=TextWrapping.Wrap};
    readonly TextBox diagnostics=new(){IsReadOnly=true,AcceptsReturn=true,TextWrapping=TextWrapping.Wrap};
    readonly ListBox issues=new(){ItemTemplate=new FuncDataTemplate<Issue>((issue,_)=>new TextBlock{Text=issue?.Message})};
    readonly TextBlock issueCount=new();
    readonly TabControl tabs=new();
    readonly TextBox day=new(){Text="3",PlaceholderText="Story day"};
    readonly ComboBox actor=new(){ItemsSource=new[]{"A","B"},SelectedIndex=0},fact=new(){ItemsSource=new[]{"F1","F2"},SelectedIndex=0};
    readonly CheckBox developer=new(){Content="Developer Mode"};
    readonly Button evidence=new(){Content="Evidence → exact anchor"},retry=new(){Content="Restart / reconnect"};
    readonly Stopwatch clock=Stopwatch.StartNew();readonly string root,project,python;readonly string? frozen,smokePath;readonly double startupDelay;readonly bool smokeLive;
    double shellMs,readyMs;
    WorkbenchClient? client;PresentationModel? model;Presentation? shown;bool closing=false;
    long connectionEpoch;bool smokeRunning;
    readonly DispatcherTimer watchTimer=new(){Interval=TimeSpan.FromSeconds(2)};
    public MainWindow(string[] args)
    {
        string? Option(string key){int i=Array.IndexOf(args,key);return i>=0 && i+1<args.Length?args[i+1]:null;}
        root=Option("--root")??FindRoot();project=Option("--project")??Path.Combine(root,"experiments/workbench-spike/fixtures/tiny");
        python=Option("--python")??Path.Combine(Path.GetTempPath(),"NarrativeWorkbenchSpike/environment/Scripts/python.exe");frozen=Option("--engine");smokePath=Option("--smoke-output");startupDelay=double.Parse(Option("--startup-delay")??"0",System.Globalization.CultureInfo.InvariantCulture);
        smokeLive=args.Contains("--smoke-live");
        Title="Narrative Workbench — Technical Spike";Width=1280;Height=820;MinWidth=800;MinHeight=520;
        var top=new StackPanel{Orientation=Orientation.Horizontal,Spacing=20,Margin=new Thickness(12),Children={badge,status,developer,retry}};
        var query=new Button{Content="Knowledge state / Why?"};
        var controls=new StackPanel{Spacing=12,Margin=new Thickness(12),Children={new TextBlock{Text="Character / Fact / Story valid day"},actor,fact,day,query,answer,evidence}};
        var previous=new Button{Content="Previous page"};var next=new Button{Content="Next page"};var end=new Button{Content="Jump near end"};
        var nav=new StackPanel{Orientation=Orientation.Horizontal,Spacing=8,Children={previous,next,end}};
        var center=new Grid{RowDefinitions=new RowDefinitions("Auto,*"),Margin=new Thickness(8)};center.Children.Add(nav);center.Children.Add(manuscript);Grid.SetRow(manuscript,1);
        var issueFilter=new TextBox{PlaceholderText="Literal issue filter"};var filterButton=new Button{Content="Filter"};
        var filterRow=new StackPanel{Spacing=4,Children={issueFilter,filterButton,issueCount}};
        filterButton.Click+=async(_,_)=>
        {
            var own=connectionEpoch;var active=model;if(active==null)return;
            try{var page=await active.IssuesAsync(issueFilter.Text??"");if(own==connectionEpoch && page is not null && page.SnapshotId==shown?.Lease.SnapshotId){issues.ItemsSource=page.Issues;issueCount.Text=$"{page.Total} matched / {page.Issues.Count} page rows";}}
            catch(Exception ex){if(own==connectionEpoch)issueCount.Text="ERROR: "+ex.Message;}
        };
        var issuesBody=new DockPanel();DockPanel.SetDock(filterRow,Dock.Top);issuesBody.Children.Add(filterRow);issuesBody.Children.Add(issues);
        tabs.ItemsSource=new[]{new TabItem{Header="Trace",Content=trace},new TabItem{Header="Issues",Content=issuesBody}};
        var right=new Grid{RowDefinitions=new RowDefinitions("*,*"),Margin=new Thickness(8)};right.Children.Add(tabs);right.Children.Add(diagnostics);Grid.SetRow(diagnostics,1);
        var body=new Grid{ColumnDefinitions=new ColumnDefinitions("230,5,*,5,350")};body.Children.Add(controls);body.Children.Add(center);Grid.SetColumn(center,2);body.Children.Add(right);Grid.SetColumn(right,4);
        var split1=new GridSplitter{ResizeDirection=GridResizeDirection.Columns,HorizontalAlignment=HorizontalAlignment.Stretch};var split2=new GridSplitter{ResizeDirection=GridResizeDirection.Columns,HorizontalAlignment=HorizontalAlignment.Stretch};body.Children.Add(split1);Grid.SetColumn(split1,1);body.Children.Add(split2);Grid.SetColumn(split2,3);
        var layout=new Grid{RowDefinitions=new RowDefinitions("Auto,*")};layout.Children.Add(top);layout.Children.Add(body);Grid.SetRow(body,1);Content=layout;
        query.Click+=async(_,_)=>{if(model!=null && double.TryParse(day.Text,out var value))await model.SelectAsync(new(new(actor.SelectedItem?.ToString()??"A"),new(fact.SelectedItem?.ToString()??"F1"),new("story_valid","day",value,"at","CH3")));};
        previous.Click+=async(_,_)=>{if(model!=null)await model.PageAsync((shown?.Page.StartBlock??0)-20);};
        next.Click+=async(_,_)=>{if(model!=null)await model.PageAsync(Math.Min((shown?.Page.TotalBlocks??20)-1,(shown?.Page.StartBlock??0)+20));};
        end.Click+=async(_,_)=>{if(model!=null)await model.PageAsync(Math.Max(0,(shown?.Page.TotalBlocks??20)-20));};
        evidence.Click+=async(_,_)=>{if(model!=null)await model.PageAsync(0,true);};
        developer.IsCheckedChanged+=(_,_)=>{if(model!=null){model.Developer=developer.IsChecked==true;if(shown!=null)Render(shown);}};
        retry.Click+=async(_,_)=>await ConnectAsync();
        Opened+=async(_,_)=>{shellMs=clock.Elapsed.TotalMilliseconds;status.Text=$"STARTING (shell {shellMs:F0} ms)";await ConnectAsync();};
        watchTimer.Tick+=async(_,_)=>{if(model!=null)await model.CheckWatchAsync();};watchTimer.Start();
        Closing+=async(_,e)=>{if(closing)return;e.Cancel=true;closing=true;watchTimer.Stop();if(client!=null)await client.DisposeAsync();Close();};
    }
    static string FindRoot()
    {
        for(var dir=new DirectoryInfo(AppContext.BaseDirectory);dir!=null;dir=dir.Parent)if(File.Exists(Path.Combine(dir.FullName,"docs/workbench/contracts/workbench-wire.schema.json")))return dir.FullName;
        throw new DirectoryNotFoundException("Pass --root repository-or-package-root");
    }
    async Task ConnectAsync()
    {
        var own=++connectionEpoch;
        retry.IsEnabled=false;
        try
        {
            if(client!=null)await client.DisposeAsync();client=new(root,python,frozen,startupDelay:startupDelay);var active=new PresentationModel(client,project);model=active;
            active.PropertyChanged+=(_,_)=>Dispatcher.UIThread.Post(()=>{if(own==connectionEpoch)status.Text=active.Status;});
            active.Changed+=p=>Dispatcher.UIThread.Post(()=>{if(own==connectionEpoch)Render(p);});
            await model.StartAsync(CancellationToken.None);readyMs=clock.Elapsed.TotalMilliseconds-shellMs;await model.SelectAsync(new(new("A"),new("F1"),new("story_valid","day",3,"at","CH3")));
            if(smokePath!=null && !smokeRunning){smokeRunning=true;await SmokeAsync();}
        }
        catch(Exception ex){status.Text="ENGINE_UNAVAILABLE: "+ex.Message;if(smokePath!=null){File.WriteAllText(smokePath,JsonSerializer.Serialize(new{passed=false,error=ex.ToString()}));Close();}}
        finally{retry.IsEnabled=true;}
    }
    void Render(Presentation p)
    {
        if(p.Knowledge.SnapshotId!=p.Lease.SnapshotId || p.Trace.SnapshotId!=p.Lease.SnapshotId || p.Page.SnapshotId!=p.Lease.SnapshotId || p.Issues.SnapshotId!=p.Lease.SnapshotId || (p.Evidence!=null && p.Evidence.SnapshotId!=p.Lease.SnapshotId))throw new InvalidDataException("Mixed snapshot presentation rejected");
        shown=p;badge.Text=$"Snapshot: {p.Lease.SnapshotId}";
        issues.ItemsSource=p.Issues.Issues;issueCount.Text=$"{p.Issues.Total} issues; page of {p.Issues.Issues.Count}";
        answer.Text=$"{p.Knowledge.CharacterId} / {p.Knowledge.FactId}: {p.Knowledge.EpistemicState}\n{p.Knowledge.Completeness} / {p.Knowledge.Freshness}\nEvidence: {p.Evidence?.Health}";
        var page=p.Page;manuscript.Text=string.Join("\n\n",page.Blocks.Select(x=>x.Text));
        manuscript.SelectionStart=0;manuscript.SelectionEnd=0;manuscript.CaretIndex=0;
        evidence.IsEnabled=p.Evidence?.Health==EvidenceHealth.VALID;
        trace.Text=$"Why Trace: {p.Trace.Completeness}\n"+string.Join("\n",p.Trace.Edges.Select(e=>$"{e.Target} ← {e.Source}"))+"\n"+string.Join("\n",p.Trace.Warnings);
        diagnostics.Text=model?.Developer==true?model.DeveloperText(p):$"Read-only / agent_calls = {p.Knowledge.Manifest.AgentCalls}\nPage {page.StartBlock} / {page.TotalBlocks}";
        if(page.Highlight.End>page.Highlight.Start)
        {
            int local=0;bool found=false;
            foreach(var b in page.Blocks)
            {
                if(page.Highlight.Start>=b.Start && page.Highlight.End<=b.Start+b.Text.EnumerateRunes().Count())
                {
                    manuscript.SelectionStart=local+UnicodeOffsets.ToUtf16(b.Text,page.Highlight.Start-b.Start);manuscript.SelectionEnd=local+UnicodeOffsets.ToUtf16(b.Text,page.Highlight.End-b.Start);found=true;break;
                }
                local+=b.Text.Length+2;
            }
            if(!found)throw new InvalidDataException("Highlight outside pinned page");
        }
    }
    async Task SmokeAsync()
    {
        if(model?.Current==null)throw new InvalidOperationException(model?.Status);
        var initialReady=readyMs;
        var timer=Stopwatch.StartNew();await model.PageAsync(0,true);Render(model.Current!);
        string selectedText=manuscript.Text![manuscript.SelectionStart..manuscript.SelectionEnd];
        if(selectedText!=model.Current!.Evidence!.DisplayText)throw new InvalidDataException("Unicode highlight mismatch");
        var jump=timer.Elapsed.TotalMilliseconds;
        developer.IsChecked=true;Render(model.Current);await CaptureAsync(".evidence.png");developer.IsChecked=false;
        timer.Restart();await model.PageAsync(model.Current.Page.TotalBlocks-20);Render(model.Current!);
        var endJump=timer.Elapsed.TotalMilliseconds;
        var issuePage=await model.IssuesAsync();issues.ItemsSource=issuePage?.Issues;issueCount.Text=$"{issuePage?.Total} issues; page of {issuePage?.Issues.Count}";
        timer.Restart();var filtered=await model.IssuesAsync("09999");var filterMs=timer.Elapsed.TotalMilliseconds;
        tabs.SelectedIndex=1;await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
        issues.SelectedIndex=Math.Max(0,(issuePage?.Issues.Count??1)-1);issues.ScrollIntoView(issues.SelectedItem!);
        await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
        int realizedIssues=issues.GetVisualDescendants().OfType<ListBoxItem>().Count();
        if(realizedIssues>300)throw new InvalidDataException("Issue list is not virtualized");
        await CaptureAsync(".issues.png");tabs.SelectedIndex=0;
        long engineWorkingSet=client!.EngineWorkingSet;
        // Render a real laid-out Avalonia window; the screenshot is not a mockup.
        await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
        await CaptureAsync(".png");
        bool livePassed=false,crashPassed=false,restartPassed=false;double publishMs=0,restartMs=0;
        if(smokeLive)
        {
            var s1=model.Current.Lease.SnapshotId;
            var changed=new TaskCompletionSource<Presentation>(TaskCreationOptions.RunContinuationsAsynchronously);
            model.Changed+=p=>{if(p.Lease.SnapshotId!=s1)changed.TrySetResult(p);};
            File.WriteAllText(smokePath+".ready","external editor may remove proof now");timer.Restart();
            var s2=await changed.Task.WaitAsync(TimeSpan.FromSeconds(8));publishMs=timer.Elapsed.TotalMilliseconds;Render(s2);
            livePassed=s2.Evidence?.Health==EvidenceHealth.BROKEN && s2.Knowledge.Completeness==Completeness.PARTIAL && s2.Knowledge.Freshness==Freshness.STALE;
            if(!livePassed)throw new InvalidDataException("S2 did not expose broken evidence");
            var unavailable=new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);client!.Unavailable+=m=>unavailable.TrySetResult(m);client.KillForTest();await unavailable.Task.WaitAsync(TimeSpan.FromSeconds(3));
            await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
            crashPassed=shown?.Lease.SnapshotId==s2.Lease.SnapshotId && status.Text!.Contains("ENGINE_UNAVAILABLE");
            if(!crashPassed)throw new InvalidDataException("Crash lost last stable presentation or status");
            var oldInstance=client.Hello!.ServerInstanceId;timer.Restart();await ConnectAsync();restartMs=timer.Elapsed.TotalMilliseconds;
            await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
            restartPassed=client.Hello?.ServerInstanceId!=oldInstance && model?.Current!=null && model.Current.Knowledge.Freshness==Freshness.STALE;
            if(!restartPassed)throw new InvalidDataException("UI reconnect did not establish a new session and presentation");
        }
        var invariantContext=model?.Current??throw new InvalidOperationException("Presentation unavailable after reconnect");
        developer.IsChecked=true;Render(invariantContext);
        var semantic=JsonSerializer.Serialize(invariantContext.Knowledge,WireJson.Options);developer.IsChecked=false;Render(invariantContext);
        if(semantic!=JsonSerializer.Serialize(model!.Current!.Knowledge,WireJson.Options))throw new InvalidDataException("Developer mode changed semantics");
        File.WriteAllText(smokePath!,JsonSerializer.Serialize(new{passed=true,shell_ms=shellMs,backend_ready_ms=initialReady,evidence_jump_ms=jump,end_jump_ms=endJump,issue_total=issuePage?.Total,issue_page_rows=issuePage?.Issues.Count,issue_filter_ms=filterMs,filtered_rows=filtered?.Total,realized_issue_controls=realizedIssues,highlight_text=selectedText,total_blocks=model!.Current!.Page.TotalBlocks,page_blocks=model.Current.Page.Blocks.Count,ui_working_set=Process.GetCurrentProcess().WorkingSet64,engine_working_set=engineWorkingSet,developer_invariance=true,live_passed=livePassed,crash_passed=crashPassed,restart_passed=restartPassed,restart_ms=restartMs,external_publish_ms=publishMs},new JsonSerializerOptions{WriteIndented=true}));
        Close();
    }
    async Task CaptureAsync(string suffix)
    {
        await Dispatcher.UIThread.InvokeAsync(()=>{},DispatcherPriority.Background);
        using var bitmap=new RenderTargetBitmap(new PixelSize((int)Bounds.Width,(int)Bounds.Height),new Vector(96,96));
        bitmap.Render(this);using var stream=File.Create(smokePath+suffix);bitmap.Save(stream,PngBitmapEncoderOptions.Default);
    }
}
