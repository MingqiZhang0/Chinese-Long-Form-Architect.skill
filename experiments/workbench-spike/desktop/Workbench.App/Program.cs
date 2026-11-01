using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Themes.Fluent;
namespace Workbench.App;
static class Program
{
    public static string[] Arguments=[];
    [STAThread] public static int Main(string[] args)
    {Arguments=args;return AppBuilder.Configure<SpikeApp>().UsePlatformDetect().LogToTrace().StartWithClassicDesktopLifetime(args);}
}
public sealed class SpikeApp : Application
{
    public override void Initialize()=>Styles.Add(new FluentTheme());
    public override void OnFrameworkInitializationCompleted()
    {if(ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)desktop.MainWindow=new MainWindow(Program.Arguments);base.OnFrameworkInitializationCompleted();}
}
