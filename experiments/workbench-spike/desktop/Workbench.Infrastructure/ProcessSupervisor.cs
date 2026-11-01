using System.Diagnostics;
using System.Text.Json;
using Workbench.Protocol;
namespace Workbench.Infrastructure;
public sealed class ProcessSupervisor : IAsyncDisposable
{
    Process? process;Task? stderr;
    public int ProcessId=>process?.Id ?? 0;
    public long WorkingSet { get { if(process is not {HasExited:false})return 0;process.Refresh();return process.WorkingSet64;} }
    public event Action<string>? Exited;
    public Process Launch(string executable,IEnumerable<string> arguments,string directory)
    {
        if(process!=null)throw new InvalidOperationException("Process already owned");
        var info=new ProcessStartInfo(executable){WorkingDirectory=directory,UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true};
        foreach(var a in arguments)info.ArgumentList.Add(a);
        info.Environment.Remove("PYTHONPATH");info.Environment["PYTHONDONTWRITEBYTECODE"]="1";info.Environment["PYTHONIOENCODING"]="utf-8";
        process=new Process{StartInfo=info,EnableRaisingEvents=true};
        var owned=process;process.Exited+=(_,_)=>Exited?.Invoke($"Engine exit {owned.ExitCode}");
        if(!process.Start())throw new IOException("Unable to launch engine");
        stderr=Task.Run(async()=>{string? line;while((line=await process.StandardError.ReadLineAsync())!=null){if(line.Length>8192)line=line[..8192];Debug.WriteLine(line);}});
        return process;
    }
    public void KillForTest(){if(process is {HasExited:false})process.Kill(entireProcessTree:true);}
    public async ValueTask DisposeAsync()
    {
        if(process==null)return;
        if(!process.HasExited)
        {
            try{process.StandardInput.Close();}catch(ObjectDisposedException){} // Transport may already have closed its owned stream.
            try{await process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(3));}
            catch(TimeoutException){process.Kill(entireProcessTree:true);await process.WaitForExitAsync();}
        }
        if(stderr!=null)await stderr;process.Dispose();process=null;
    }
}
