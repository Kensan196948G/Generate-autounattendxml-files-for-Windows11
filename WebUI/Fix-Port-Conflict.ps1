#Requires -Version 5.0
<#
.SYNOPSIS
    ポート競合を解決してWebUIを起動
.DESCRIPTION
    使用中のポートを解放してから、WebUIを正常に起動します
#>

param(
    [int]$BackendPort = 8081,
    [int]$FrontendPort = 3050
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "ポート競合解決スクリプト" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# バックエンドポート（8081）の解放
Write-Host "🔍 ポート $BackendPort を使用中のプロセスを確認中..." -ForegroundColor Yellow

$backendProcess = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($backendProcess) {
    foreach ($pid in $backendProcess) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "⚠️  発見: $($process.Name) (PID: $pid)" -ForegroundColor Yellow
            Write-Host "🔧 プロセスを終了中..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Host "✅ プロセスを終了しました" -ForegroundColor Green
        }
    }
} else {
    Write-Host "✅ ポート $BackendPort は利用可能です" -ForegroundColor Green
}

# フロントエンドポート（3050）の解放
Write-Host ""
Write-Host "🔍 ポート $FrontendPort を使用中のプロセスを確認中..." -ForegroundColor Yellow

$frontendProcess = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($frontendProcess) {
    foreach ($pid in $frontendProcess) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "⚠️  発見: $($process.Name) (PID: $pid)" -ForegroundColor Yellow
            Write-Host "🔧 プロセスを終了中..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Host "✅ プロセスを終了しました" -ForegroundColor Green
        }
    }
} else {
    Write-Host "✅ ポート $FrontendPort は利用可能です" -ForegroundColor Green
}

# Node.jsプロセスのクリーンアップ
Write-Host ""
Write-Host "🧹 残留プロセスをクリーンアップ中..." -ForegroundColor Yellow

$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Node.jsプロセスをクリーンアップしました" -ForegroundColor Green
}

$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Pythonプロセスをクリーンアップしました" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ ポート競合を解決しました" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# WebUIを起動するか確認
$response = Read-Host "WebUIを起動しますか？ (Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    Write-Host ""
    Write-Host "🚀 WebUIを起動中..." -ForegroundColor Yellow
    
    $startScript = Join-Path $PSScriptRoot "Start-WebUI-Full.ps1"
    if (Test-Path $startScript) {
        & $startScript
    } else {
        Write-Host "❌ Start-WebUI-Full.ps1 が見つかりません" -ForegroundColor Red
        Write-Host "   手動で起動してください" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "手動で起動する場合は以下を実行してください：" -ForegroundColor Gray
    Write-Host "  .\Start-WebUI-Full.ps1" -ForegroundColor White
}