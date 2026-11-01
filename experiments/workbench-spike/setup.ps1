param([string]$EnvironmentRoot = (Join-Path ([IO.Path]::GetTempPath()) 'NarrativeWorkbenchSpike/environment'))
$ErrorActionPreference='Stop'
$spikeRoot=$PSScriptRoot
if (!(Test-Path -LiteralPath (Join-Path $EnvironmentRoot 'Scripts/python.exe'))) {
    python -m venv $EnvironmentRoot
    if ($LASTEXITCODE -ne 0) { throw 'venv failed' }
}
$spikePython=Join-Path $EnvironmentRoot 'Scripts/python.exe'
& $spikePython -m pip install --no-compile -r (Join-Path $spikeRoot 'requirements.lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'dependency installation failed' }
Write-Output $spikePython
