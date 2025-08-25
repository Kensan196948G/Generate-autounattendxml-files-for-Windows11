# ============================================================================
# フロントエンドサーバー起動スクリプト (PowerShell版)
# ============================================================================

param(
    [string]$IP = "",
    [int]$Port = 3050,
    [switch]$Production,
    [switch]$SkipInstall
)

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendPath = Join-Path $ScriptRoot "frontend"

# カラー出力関数
function Write-ColorHost {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# ヘッダー表示
Clear-Host
Write-ColorHost "======================================" -ForegroundColor Cyan
Write-ColorHost " Windows 11 無人応答ファイル生成システム" -ForegroundColor Green
Write-ColorHost " フロントエンドサーバー (PowerShell版)" -ForegroundColor Green
Write-ColorHost " Schneegans.de スタイルUI" -ForegroundColor Green
Write-ColorHost "======================================" -ForegroundColor Cyan
Write-Host ""

# IPアドレス検出
function Get-LocalIPAddress {
    $targetIP = "192.168.3.92"
    
    # 指定IPの確認
    $checkIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | 
               Where-Object { $_.IPAddress -eq $targetIP }
    if ($checkIP) { 
        return $targetIP 
    }
    
    # その他のプライベートIP（APIPA除外）
    $privateIP = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { 
            ($_.IPAddress -like "192.168.*" -or 
             $_.IPAddress -like "10.*" -or 
             $_.IPAddress -like "172.16.*") -and
            $_.IPAddress -notlike "169.254.*"
        } | Select-Object -First 1
    
    if ($privateIP) { 
        return $privateIP.IPAddress 
    }
    
    return "127.0.0.1"
}

# IPアドレス設定
if ([string]::IsNullOrEmpty($IP)) {
    $IP = Get-LocalIPAddress
}

Write-ColorHost "設定情報:" -ForegroundColor Yellow
Write-Host "  IPアドレス: $IP"
Write-Host "  ポート: $Port"
Write-Host "  フロントエンドパス: $FrontendPath"
Write-Host ""

# ディレクトリ確認
if (-not (Test-Path $FrontendPath)) {
    Write-ColorHost "エラー: フロントエンドディレクトリが見つかりません" -ForegroundColor Red
    Write-Host "パス: $FrontendPath"
    Read-Host "Enterキーで終了"
    exit 1
}

# 作業ディレクトリ変更
Set-Location $FrontendPath
Write-ColorHost "作業ディレクトリ: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# package.json確認
if (-not (Test-Path ".\package.json")) {
    Write-ColorHost "エラー: package.jsonが見つかりません" -ForegroundColor Red
    Read-Host "Enterキーで終了"
    exit 1
}

# node_modules確認とインストール
if (-not (Test-Path ".\node_modules") -and -not $SkipInstall) {
    Write-ColorHost "node_modulesが見つかりません。パッケージをインストールします..." -ForegroundColor Yellow
    
    try {
        Write-Host "npm install を実行中..."
        
        # npmコマンドを直接実行
        $npmProcess = Start-Process -FilePath "npm" -ArgumentList "install" -NoNewWindow -Wait -PassThru
        
        if ($npmProcess.ExitCode -ne 0) {
            throw "npm install が失敗しました (Exit Code: $($npmProcess.ExitCode))"
        }
        
        Write-ColorHost "パッケージのインストールが完了しました" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-ColorHost "エラー: パッケージのインストールに失敗しました" -ForegroundColor Red
        Write-Host $_
        Read-Host "Enterキーで終了"
        exit 1
    }
}

# 環境変数設定
Write-ColorHost "環境変数を設定中..." -ForegroundColor Yellow
$env:NEXT_PUBLIC_API_URL = "http://${IP}:8080/api"
$env:NEXT_PUBLIC_LOCAL_IP = $IP
$env:NODE_ENV = if ($Production) { "production" } else { "development" }

Write-Host "  NEXT_PUBLIC_API_URL: $env:NEXT_PUBLIC_API_URL"
Write-Host "  NEXT_PUBLIC_LOCAL_IP: $env:NEXT_PUBLIC_LOCAL_IP"
Write-Host "  NODE_ENV: $env:NODE_ENV"
Write-Host ""

# UIファイルの切り替え確認
$IndexPath = ".\src\pages\index.tsx"
$NewIndexPath = ".\src\pages\index_new.tsx"
$OldIndexPath = ".\src\pages\index_old.tsx"

if (Test-Path $NewIndexPath) {
    Write-ColorHost "新しいUIファイルを適用中..." -ForegroundColor Yellow
    
    # 既存のindex.tsxをバックアップ
    if (Test-Path $IndexPath) {
        Move-Item -Path $IndexPath -Destination $OldIndexPath -Force
        Write-Host "  既存のindex.tsxをindex_old.tsxにバックアップしました"
    }
    
    # 新しいUIを適用
    Move-Item -Path $NewIndexPath -Destination $IndexPath -Force
    Write-ColorHost "  新しいUIが適用されました" -ForegroundColor Green
    Write-Host ""
}

# サーバー起動
Write-ColorHost "フロントエンドサーバーを起動中..." -ForegroundColor Yellow
Write-Host ""
Write-ColorHost "========================================" -ForegroundColor Cyan
Write-ColorHost " URL: http://${IP}:${Port}" -ForegroundColor Green
Write-ColorHost " API: http://${IP}:8080/api" -ForegroundColor Green
Write-ColorHost "========================================" -ForegroundColor Cyan
Write-Host ""
Write-ColorHost "サーバーを停止するには Ctrl+C を押してください" -ForegroundColor Yellow
Write-Host ""

try {
    if ($Production) {
        # プロダクションビルド
        Write-ColorHost "プロダクションビルドを作成中..." -ForegroundColor Yellow
        $buildProcess = Start-Process -FilePath "npm" -ArgumentList "run", "build" -NoNewWindow -Wait -PassThru
        
        if ($buildProcess.ExitCode -ne 0) {
            throw "ビルドに失敗しました"
        }
        
        Write-ColorHost "プロダクションサーバーを起動中..." -ForegroundColor Green
        & npm run start
    } else {
        # 開発サーバー
        Write-ColorHost "開発サーバーを起動中..." -ForegroundColor Green
        
        # npm run dev を実行（cmd経由で実行）
        & cmd /c "npm run dev"
    }
} catch {
    Write-ColorHost "エラー: サーバーの起動に失敗しました" -ForegroundColor Red
    Write-Host $_
    Write-Host ""
    Write-Host "トラブルシューティング:"
    Write-Host "  1. Node.jsが正しくインストールされているか確認"
    Write-Host "  2. ポート $Port が他のプロセスで使用されていないか確認"
    Write-Host "  3. npm install が正常に完了しているか確認"
    Write-Host ""
} finally {
    Write-Host ""
    Write-ColorHost "フロントエンドサーバーが停止しました" -ForegroundColor Yellow
    Read-Host "Enterキーで終了"
}