# フロントエンド即起動スクリプト

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Windows 11 無人応答ファイル生成システム" -ForegroundColor Green
Write-Host "フロントエンド起動" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$frontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $frontendPath

# node_modulesの存在確認
if (-not (Test-Path ".\node_modules")) {
    Write-Host "⚠️  node_modulesが見つかりません" -ForegroundColor Yellow
    Write-Host "依存関係をインストール中..." -ForegroundColor Yellow
    
    # cmd.exe経由でnpm installを実行
    $installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm install" -WorkingDirectory $frontendPath -Wait -PassThru -NoNewWindow
    
    if ($installProcess.ExitCode -ne 0) {
        Write-Host "❌ インストールに失敗しました" -ForegroundColor Red
        Read-Host "Enterキーで終了"
        exit 1
    }
    Write-Host "✅ インストール完了" -ForegroundColor Green
    Write-Host ""
}

# 環境変数設定
$env:NEXT_PUBLIC_API_URL = "http://192.168.3.92:8080/api"
$env:NEXT_PUBLIC_LOCAL_IP = "192.168.3.92"

Write-Host "環境変数を設定しました:" -ForegroundColor Gray
Write-Host "  API URL: $env:NEXT_PUBLIC_API_URL" -ForegroundColor Gray
Write-Host "  Local IP: $env:NEXT_PUBLIC_LOCAL_IP" -ForegroundColor Gray
Write-Host ""

Write-Host "フロントエンドサーバーを起動中..." -ForegroundColor Yellow
Write-Host "URL: http://192.168.3.92:3050" -ForegroundColor Cyan
Write-Host ""
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# cmd.exe経由でnpm run devを実行
& cmd.exe /c "npm run dev"