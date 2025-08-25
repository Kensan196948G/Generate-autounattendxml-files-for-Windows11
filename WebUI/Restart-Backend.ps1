# バックエンド再起動スクリプト

Write-Host "バックエンドを再起動します..." -ForegroundColor Yellow

# Pythonプロセスを停止
Write-Host "既存のバックエンドを停止中..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" } | Stop-Process -Force
Start-Sleep -Seconds 2

# バックエンドを再起動
Write-Host "バックエンドを起動中..." -ForegroundColor Green

$backendPath = "E:\Generate-autounattendxml-files-for-Windows11\WebUI\backend"
Set-Location $backendPath

# main.pyを起動
if (Test-Path ".\venv\Scripts\python.exe") {
    Write-Host "仮想環境のPythonを使用" -ForegroundColor Gray
    & ".\venv\Scripts\python.exe" main.py
} else {
    Write-Host "システムのPythonを使用" -ForegroundColor Gray
    & python main.py
}