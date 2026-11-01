param(
    [string]$Python = (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/environment/Scripts/python.exe'),
    [string]$Output = (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/package')
)
$ErrorActionPreference='Stop'
$spikeRoot=$PSScriptRoot
$repositoryRoot=(Resolve-Path (Join-Path $spikeRoot '../..')).Path
$env:AVALONIA_TELEMETRY_OPTOUT='1'
$env:PYTHONDONTWRITEBYTECODE='1'
New-Item -ItemType Directory -Force -Path $Output | Out-Null
$schema=Join-Path $repositoryRoot 'docs/workbench/contracts/workbench-wire.schema.json'
Push-Location $repositoryRoot
try {
    & $Python -m PyInstaller --noconfirm --clean --onedir --name narrative-host --paths (Join-Path $repositoryRoot 'scripts') --paths (Join-Path $spikeRoot 'service') --add-data "$schema;docs/workbench/contracts" --distpath (Join-Path $Output 'engine') --workpath (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/freezer') --specpath (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike') (Join-Path $spikeRoot 'service/host.py')
    if ($LASTEXITCODE -ne 0) { throw 'Python freezer failed' }
    Push-Location (Join-Path $spikeRoot 'desktop')
    try {
        dotnet publish Workbench.App/Workbench.App.csproj -c Release -r win-x64 --self-contained true -o (Join-Path $Output 'app') -p:RuntimeFrameworkVersion=10.0.11 --configfile NuGet.Config --packages (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/nuget')
        if ($LASTEXITCODE -ne 0) { throw '.NET publish failed' }
    } finally { Pop-Location }
    New-Item -ItemType Directory -Force -Path (Join-Path $Output 'docs/workbench/contracts') | Out-Null
    Copy-Item -LiteralPath $schema -Destination (Join-Path $Output 'docs/workbench/contracts/workbench-wire.schema.json')
    $fixtureDestination=Join-Path $Output 'experiments/workbench-spike/fixtures/tiny'
    & $Python -B (Join-Path $spikeRoot 'fixture.py') $fixtureDestination
    if ($LASTEXITCODE -ne 0) { throw 'Package fixture failed' }
    Copy-Item -LiteralPath (Join-Path $spikeRoot 'launch-package.ps1') -Destination (Join-Path $Output 'launch.ps1')
    & $Python -B (Join-Path $spikeRoot 'package_manifest.py') $Output
    if ($LASTEXITCODE -ne 0) { throw 'Package manifest failed' }
} finally { Pop-Location }
