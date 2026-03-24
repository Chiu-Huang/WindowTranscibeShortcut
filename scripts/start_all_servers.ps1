$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir '..')).Path
$stateDir = Join-Path $scriptDir '.state'
$statePath = Join-Path $stateDir 'server-processes.json'

function Stop-TrackedProcesses {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    try {
        $state = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
        foreach ($processInfo in @($state.processes)) {
            if (-not $processInfo.pid) {
                continue
            }

            $process = Get-Process -Id $processInfo.pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping stale $($processInfo.name) process ($($processInfo.pid))"
                Stop-Process -Id $processInfo.pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    finally {
        Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    }
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string[]]$Arguments
    )

    Write-Host "Starting $Name ..."
    $process = Start-Process -FilePath 'uv' -ArgumentList $Arguments -WorkingDirectory $repoRoot -PassThru
    [pscustomobject]@{
        name = $Name
        pid = $process.Id
        command = @('uv') + $Arguments
    }
}

function Wait-ForHealth {
    param(
        [string]$Name,
        [string]$Url,
        [scriptblock]$Ready,
        [int]$TimeoutSeconds = 180
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
            if (& $Ready $response) {
                Write-Host "$Name is ready at $Url"
                return $response
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
            continue
        }

        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for $Name readiness at $Url"
}

New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
Stop-TrackedProcesses -Path $statePath

$startedProcesses = @()

try {
    $startedProcesses += Start-ServiceProcess -Name 'transcribe-service-api' -Arguments @('run', 'transcribe-service-api', '--warmup')
    Wait-ForHealth -Name 'transcribe-service-api' -Url 'http://127.0.0.1:8766/health' -Ready {
        param($response)
        $response.status -eq 'ok' -and $response.model_loaded -eq $true
    } | Out-Null

    $startedProcesses += Start-ServiceProcess -Name 'window-transcribe-translation-service-api' -Arguments @('run', 'window-transcribe-translation-service-api', '--warmup')
    Wait-ForHealth -Name 'window-transcribe-translation-service-api' -Url 'http://127.0.0.1:8876/health' -Ready {
        param($response)
        $response.status -eq 'ok' -and $response.loaded -eq $true
    } | Out-Null

    $startedProcesses += Start-ServiceProcess -Name 'window-transcribe-shortcut-api' -Arguments @('run', 'window-transcribe-shortcut-api')
    Wait-ForHealth -Name 'window-transcribe-shortcut-api' -Url 'http://127.0.0.1:8765/health' -Ready {
        param($response)
        $response.status -eq 'ok'
    } | Out-Null

    $state = [pscustomobject]@{
        started_at = (Get-Date).ToString('o')
        processes = $startedProcesses
        health_checks = @(
            'http://127.0.0.1:8766/health',
            'http://127.0.0.1:8876/health',
            'http://127.0.0.1:8765/health'
        )
    }

    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8

    Write-Host ''
    Write-Host 'All services are ready.'
    Write-Host '  - Transcribe:   http://127.0.0.1:8766/health'
    Write-Host '  - Translation:  http://127.0.0.1:8876/health'
    Write-Host '  - Orchestrator: http://127.0.0.1:8765/health'
    Write-Host ''
    Write-Host 'You can now drag/drop files onto the preset scripts.'
    Write-Host 'When you are done, double-click scripts\stop_all_servers.bat.'
}
catch {
    Write-Error $_

    foreach ($processInfo in $startedProcesses) {
        if ($processInfo.pid) {
            Stop-Process -Id $processInfo.pid -Force -ErrorAction SilentlyContinue
        }
    }

    Remove-Item -LiteralPath $statePath -Force -ErrorAction SilentlyContinue
    exit 1
}
