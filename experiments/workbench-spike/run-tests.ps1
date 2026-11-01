param([string]$Python = (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/environment/Scripts/python.exe'))
$ErrorActionPreference='Stop'
$spikeRoot=$PSScriptRoot
$repositoryRoot=(Resolve-Path (Join-Path $spikeRoot '../..')).Path
$desktopRoot=Join-Path $spikeRoot 'desktop'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:AVALONIA_TELEMETRY_OPTOUT='1'
$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
function Checked([scriptblock]$Action) { & $Action; if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE)" } }
Push-Location $repositoryRoot
try {
    Checked { & $Python -B (Join-Path $spikeRoot 'generate_contract.py') --check }
    Checked { & $Python -B (Join-Path $spikeRoot 'tests/test_spike.py') }
    Push-Location $desktopRoot
    try {
        Checked { dotnet restore Workbench.App/Workbench.App.csproj --locked-mode --configfile NuGet.Config --packages (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/nuget') }
        Checked { dotnet restore Workbench.Tests/Workbench.Tests.csproj --locked-mode --configfile NuGet.Config --packages (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/nuget') }
        Checked { dotnet build Workbench.App/Workbench.App.csproj -c Release --no-restore }
        Checked { dotnet build Workbench.Tests/Workbench.Tests.csproj --no-restore }
        Checked { dotnet Workbench.Tests/bin/Debug/net10.0/Workbench.Tests.dll $repositoryRoot $Python }
        $negativeOutput=dotnet build Workbench.Tests/Workbench.Tests.csproj --no-restore -p:DefineConstants=NOMINAL_NEGATIVE 2>&1
        if ($LASTEXITCODE -eq 0 -or ($negativeOutput -join "`n") -notmatch 'CS1503') { throw 'Nominal ID negative compilation did not reject FactId as CharacterId' }
        Write-Output 'PASS nominal-ID negative compilation'
    } finally { Pop-Location }
    Checked { & $Python -B (Join-Path $spikeRoot 'tests/run_ui.py') --live --output (Join-Path $spikeRoot 'artifacts/ui-live.json') }
} finally { Pop-Location }
