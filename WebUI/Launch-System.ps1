# ============================================================================
# Windows 11 無人応答ファイル生成システム - 簡単起動スクリプト
# PowerShell版完全統合
# ============================================================================

param(
    [switch]$BackendOnly,     # バックエンドのみ起動
    [switch]$FrontendOnly,    # フロントエンドのみ起動
    [switch]$Debug            # デバッグモード
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# カラー出力
function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    switch ($Type) {
        "Success" { Write-Host "[$timestamp] ✅ $Message" -ForegroundColor Green }
        "Error" { Write-Host "[$timestamp] ❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "[$timestamp] ⚠️  $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "[$timestamp] ℹ️  $Message" -ForegroundColor Cyan }
    }
}

# バナー表示
Clear-Host
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       Windows 11 無人応答ファイル生成システム - PowerShell版            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# IPアドレス取得
function Get-LocalIPAddress {
    $targetIP = "192.168.3.92"
    
    $checkIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
               Where-Object { $_.IPAddress -eq $targetIP }
    if ($checkIP) { return $targetIP }
    
    $privateIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { 
            ($_.IPAddress -like "192.168.*" -or 
             $_.IPAddress -like "10.*" -or 
             $_.IPAddress -like "172.16.*") -and
            $_.IPAddress -notlike "169.254.*"
        } | Select-Object -First 1
    
    if ($privateIP) { return $privateIP.IPAddress }
    
    return "127.0.0.1"
}

$IP = Get-LocalIPAddress
Write-Status "IPアドレス: $IP" "Info"
Write-Host ""

# バックエンド起動
if (-not $FrontendOnly) {
    Write-Status "バックエンドサーバーを起動中..." "Info"
    
    $backendScript = @"
Set-Location '$ScriptRoot\backend'
Write-Host '======================================'
Write-Host ' バックエンドサーバー起動'
Write-Host ' Context7 + SubAgent(42体) + Claude-flow'
Write-Host '======================================'
Write-Host ''
Write-Host 'URL: http://$IP:8080'
Write-Host 'API Docs: http://$IP:8080/api/docs'
Write-Host ''

# 仮想環境の確認
if (Test-Path '.\venv\Scripts\python.exe') {
    Write-Host '仮想環境を使用' -ForegroundColor Green
    .\venv\Scripts\python.exe main.py
} else {
    Write-Host 'システムPythonを使用' -ForegroundColor Yellow
    python main.py
}
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal
    Write-Status "バックエンドサーバーを新しいウィンドウで起動しました" "Success"
    
    # 起動待機
    Start-Sleep -Seconds 3
}

# フロントエンド起動
if (-not $BackendOnly) {
    Write-Status "フロントエンドサーバーを起動中..." "Info"
    
    $frontendScript = @"
Set-Location '$ScriptRoot\frontend'
Write-Host '======================================'
Write-Host ' フロントエンドサーバー起動'
Write-Host ' Schneegans.de スタイルUI'
Write-Host '======================================'
Write-Host ''
Write-Host 'URL: http://$IP:3050'
Write-Host ''

# 環境変数設定
`$env:NEXT_PUBLIC_API_URL = 'http://$IP:8080/api'
`$env:NEXT_PUBLIC_LOCAL_IP = '$IP'

# node_modules確認
if (-not (Test-Path '.\node_modules')) {
    Write-Host 'パッケージをインストール中...' -ForegroundColor Yellow
    npm install
}

# UIファイル切り替え
if (Test-Path '.\src\pages\index_new.tsx') {
    Write-Host '新しいUIを適用中...' -ForegroundColor Yellow
    if (Test-Path '.\src\pages\index.tsx') {
        Move-Item '.\src\pages\index.tsx' '.\src\pages\index_old.tsx' -Force
    }
    Move-Item '.\src\pages\index_new.tsx' '.\src\pages\index.tsx' -Force
    Write-Host '新しいUIが適用されました' -ForegroundColor Green
}

# サーバー起動（cmd経由）
Write-Host 'Next.js開発サーバーを起動中...' -ForegroundColor Yellow
cmd /c "npm run dev"
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal
    Write-Status "フロントエンドサーバーを新しいウィンドウで起動しました" "Success"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "📌 アクセスURL:" -ForegroundColor White

if (-not $FrontendOnly) {
    Write-Host "   バックエンドAPI:  http://${IP}:8080" -ForegroundColor Cyan
    Write-Host "   API仕様書:       http://${IP}:8080/api/docs" -ForegroundColor Cyan
}

if (-not $BackendOnly) {
    Write-Host "   フロントエンド:   http://${IP}:3050" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🛑 停止方法:" -ForegroundColor Yellow
Write-Host "   1. 各PowerShellウィンドウで Ctrl+C" -ForegroundColor Gray
Write-Host "   2. または .\Stop-WebUI.ps1 を実行" -ForegroundColor Gray
Write-Host ""

# デバッグモード
if ($Debug) {
    Write-Status "デバッグモード有効" "Warning"
    
    # ポートチェック関数
    function Test-Port {
        param([int]$Port)
        try {
            $connection = New-Object System.Net.Sockets.TcpClient
            $connection.Connect("127.0.0.1", $Port)
            $connection.Close()
            return $true
        } catch {
            return $false
        }
    }
    
    Write-Host ""
    Write-Host "ポート監視中..." -ForegroundColor Yellow
    
    while ($true) {
        $backendStatus = if (Test-Port -Port 8080) { "✅" } else { "❌" }
        $frontendStatus = if (Test-Port -Port 3050) { "✅" } else { "❌" }
        
        Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Backend: $backendStatus | Frontend: $frontendStatus" -NoNewline
        
        Start-Sleep -Seconds 5
    }
}

# ブラウザ起動
if (-not $BackendOnly) {
    Start-Sleep -Seconds 5
    Write-Status "ブラウザを開いています..." "Info"
    Start-Process "http://${IP}:3050"
}

Write-Host ""
Write-Status "システムが起動しました" "Success"
Write-Host ""
Write-Host "このウィンドウは閉じても構いません（サーバーは継続動作します）" -ForegroundColor Gray
Write-Host ""