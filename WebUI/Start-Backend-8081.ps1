#Requires -Version 5.0
<#
.SYNOPSIS
    WebUIバックエンドサーバーをポート8081で起動
.DESCRIPTION
    Windows 11 Sysprep応答ファイル生成システムのバックエンドAPIサーバーを起動します
#>

param(
    [switch]$Debug,
    [switch]$NoOpen
)

# 管理者権限チェック
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  管理者権限での実行を推奨します" -ForegroundColor Yellow
}

# パス設定
$BackendPath = Join-Path $PSScriptRoot "backend"

# Python確認
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Pythonがインストールされていません" -ForegroundColor Red
    Write-Host "   https://www.python.org/ からPythonをインストールしてください" -ForegroundColor Yellow
    exit 1
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "WebUI バックエンドサーバー起動" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Pythonバージョン確認
$pythonVersion = python --version 2>&1
Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green

# 依存関係インストール確認
Write-Host ""
Write-Host "📦 依存関係を確認中..." -ForegroundColor Yellow

Set-Location $BackendPath

# 仮想環境の確認と作成
if (-not (Test-Path "venv")) {
    Write-Host "🔧 仮想環境を作成中..." -ForegroundColor Yellow
    python -m venv venv
}

# 仮想環境のアクティベート
$venvActivate = Join-Path $BackendPath "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "✅ 仮想環境をアクティベートしました" -ForegroundColor Green
}

# 依存関係のインストール
if (Test-Path "requirements.txt") {
    Write-Host "📦 依存関係をインストール中..." -ForegroundColor Yellow
    pip install -q -r requirements.txt
    Write-Host "✅ 依存関係のインストール完了" -ForegroundColor Green
} else {
    Write-Host "⚠️  requirements.txtが見つかりません" -ForegroundColor Yellow
    Write-Host "   必要なパッケージを手動でインストールしてください" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "サーバー情報" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🌐 URL: http://localhost:8081" -ForegroundColor Green
Write-Host "📚 API Docs: http://localhost:8081/docs" -ForegroundColor Green
Write-Host "🔧 環境: " -NoNewline
if ($Debug) {
    Write-Host "デバッグモード" -ForegroundColor Yellow
} else {
    Write-Host "本番モード" -ForegroundColor Green
}
Write-Host ""
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ブラウザを開く
if (-not $NoOpen) {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8081/docs"
}

# サーバー起動
try {
    if ($Debug) {
        $env:DEBUG = "true"
        python main.py --debug
    } else {
        python main.py
    }
} catch {
    Write-Host ""
    Write-Host "❌ サーバーの起動に失敗しました" -ForegroundColor Red
    Write-Host "   エラー: $_" -ForegroundColor Red
    exit 1
} finally {
    Write-Host ""
    Write-Host "🛑 サーバーを停止しました" -ForegroundColor Yellow
}