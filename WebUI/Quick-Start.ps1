# ============================================================================
# Windows 11 無人応答ファイル生成システム - クイックスタート
# Start-WebUI.ps1 を呼び出すシンプルなラッパー
# ============================================================================

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# バナー表示
Clear-Host
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Windows 11 無人応答ファイル生成システム - クイックスタート          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "システムを起動しています..." -ForegroundColor Yellow
Write-Host ""

# Start-WebUI.ps1を実行
& "$ScriptRoot\Start-WebUI.ps1"