# Node.js依存関係クリーンインストール PowerShell版

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Node.js依存関係のクリーンインストール" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 現在のディレクトリを保存
$currentDir = Get-Location

# frontendディレクトリに移動
$frontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $frontendPath

# node_modulesを削除
if (Test-Path ".\node_modules") {
    Write-Host "node_modulesフォルダを削除中..." -ForegroundColor Yellow
    Remove-Item -Path ".\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✓ node_modules削除完了" -ForegroundColor Green
}

# package-lock.jsonを削除
if (Test-Path ".\package-lock.json") {
    Write-Host "package-lock.jsonを削除中..." -ForegroundColor Yellow
    Remove-Item -Path ".\package-lock.json" -Force -ErrorAction SilentlyContinue
    Write-Host "✓ package-lock.json削除完了" -ForegroundColor Green
}

Write-Host ""
Write-Host "npmキャッシュをクリア中..." -ForegroundColor Yellow
$cacheResult = & cmd.exe /c "npm cache clean --force" 2>&1
Write-Host "✓ キャッシュクリア完了" -ForegroundColor Green

Write-Host ""
Write-Host "新しい依存関係をインストール中..." -ForegroundColor Yellow
Write-Host "（初回は時間がかかります。しばらくお待ちください...）" -ForegroundColor Gray
Write-Host ""

# cmd.exe経由でnpm installを実行
$installProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm install" -WorkingDirectory $frontendPath -Wait -PassThru -NoNewWindow

if ($installProcess.ExitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ インストール完了！" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "フロントエンドを起動する方法:" -ForegroundColor Green
    Write-Host ""
    Write-Host "方法1: PowerShellで実行" -ForegroundColor Yellow
    Write-Host "  Set-Location '$frontendPath'" -ForegroundColor White
    Write-Host "  cmd.exe /c 'npm run dev'" -ForegroundColor White
    Write-Host ""
    Write-Host "方法2: コマンドプロンプトで実行" -ForegroundColor Yellow
    Write-Host "  cd $frontendPath" -ForegroundColor White
    Write-Host "  npm run dev" -ForegroundColor White
    Write-Host ""
    Write-Host "方法3: 自動起動スクリプト" -ForegroundColor Yellow
    Write-Host "  .\Start-Frontend-Now.ps1" -ForegroundColor White
    Write-Host "============================================================" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ インストールにエラーが発生しました" -ForegroundColor Red
    Write-Host "以下を手動で実行してください:" -ForegroundColor Yellow
    Write-Host "  1. コマンドプロンプトを開く" -ForegroundColor White
    Write-Host "  2. cd $frontendPath" -ForegroundColor White
    Write-Host "  3. npm install" -ForegroundColor White
}

Write-Host ""
Read-Host "Enterキーで終了"

# 元のディレクトリに戻る
Set-Location $currentDir