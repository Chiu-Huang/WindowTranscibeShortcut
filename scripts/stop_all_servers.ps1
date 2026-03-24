$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$statePath = Join-Path (Join-Path $scriptDir '.state') 'server-processes.json'

if (-not (Test-Path -LiteralPath $statePath)) {
    Write-Host 'No tracked services are currently running.'
    exit 0
}

$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$stoppedAny = $false

foreach ($processInfo in @($state.processes)) {
    if (-not $processInfo.pid) {
        continue
    }

    $process = Get-Process -Id $processInfo.pid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Stopping $($processInfo.name) process ($($processInfo.pid))"
        Stop-Process -Id $processInfo.pid -Force -ErrorAction SilentlyContinue
        $stoppedAny = $true
    }
    else {
        Write-Host "$($processInfo.name) process ($($processInfo.pid)) is already stopped"
    }
}

Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue

if ($stoppedAny) {
    Write-Host 'All tracked services have been stopped.'
}
else {
    Write-Host 'Tracked services were already stopped.'
}
