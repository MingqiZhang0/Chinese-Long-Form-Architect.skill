param([string]$Project = (Join-Path $PSScriptRoot 'experiments/workbench-spike/fixtures/tiny'))
& (Join-Path $PSScriptRoot 'app/Workbench.App.exe') --root $PSScriptRoot --engine (Join-Path $PSScriptRoot 'engine/narrative-host/narrative-host.exe') --project $Project
