# API接続テストスクリプト

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "API接続テスト" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://192.168.3.92:8080"

# 1. ルートエンドポイントテスト
Write-Host "1. ルートエンドポイントをテスト中..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ ルート接続成功" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "   バージョン: $($content.version)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ ルート接続失敗: $_" -ForegroundColor Red
}

# 2. /api/status エンドポイントテスト
Write-Host ""
Write-Host "2. /api/status エンドポイントをテスト中..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/api/status" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ ステータス取得成功" -ForegroundColor Green
    $status = $response.Content | ConvertFrom-Json
    Write-Host "   ステータス: $($status.status)" -ForegroundColor Gray
    Write-Host "   Context7: $($status.context7)" -ForegroundColor Gray
    Write-Host "   SubAgent数: $($status.subagents.total)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ ステータス取得失敗: $_" -ForegroundColor Red
}

# 3. /api/agents エンドポイントテスト
Write-Host ""
Write-Host "3. /api/agents エンドポイントをテスト中..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/api/agents" -UseBasicParsing -TimeoutSec 5
    Write-Host "   ✅ エージェント一覧取得成功" -ForegroundColor Green
    $agents = $response.Content | ConvertFrom-Json
    Write-Host "   エージェント数: $($agents.total)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ エージェント一覧取得失敗: $_" -ForegroundColor Red
}

# 4. CORSヘッダーテスト
Write-Host ""
Write-Host "4. CORSヘッダーをテスト中..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$API_BASE/api/status" -UseBasicParsing -TimeoutSec 5 -Headers @{
        "Origin" = "http://192.168.3.92:3050"
    }
    
    if ($response.Headers["Access-Control-Allow-Origin"]) {
        Write-Host "   ✅ CORS設定確認" -ForegroundColor Green
        Write-Host "   Allow-Origin: $($response.Headers['Access-Control-Allow-Origin'])" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️  CORSヘッダーが設定されていません" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ CORSテスト失敗: $_" -ForegroundColor Red
}

# 5. ポート確認
Write-Host ""
Write-Host "5. ポート状態を確認中..." -ForegroundColor Yellow
$port8080 = Test-NetConnection -ComputerName "192.168.3.92" -Port 8080 -InformationLevel Quiet
$port3050 = Test-NetConnection -ComputerName "192.168.3.92" -Port 3050 -InformationLevel Quiet

if ($port8080) {
    Write-Host "   ✅ ポート8080: 開放" -ForegroundColor Green
} else {
    Write-Host "   ❌ ポート8080: 閉じている" -ForegroundColor Red
}

if ($port3050) {
    Write-Host "   ✅ ポート3050: 開放" -ForegroundColor Green
} else {
    Write-Host "   ❌ ポート3050: 閉じている" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "テスト完了" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# curlコマンドの例を表示
Write-Host "手動テストコマンド:" -ForegroundColor Yellow
Write-Host '  curl http://192.168.3.92:8080/api/status' -ForegroundColor White
Write-Host '  curl -H "Origin: http://192.168.3.92:3050" http://192.168.3.92:8080/api/status -v' -ForegroundColor White
Write-Host ""

Read-Host "Enterキーで終了"