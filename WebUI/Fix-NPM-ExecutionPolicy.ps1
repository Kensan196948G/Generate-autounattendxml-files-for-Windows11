# ============================================================================
# NPM実行ポリシー修正スクリプト
# npm.ps1の実行エラーを解決
# ============================================================================

Write-Host "NPM実行ポリシーの問題を修正します..." -ForegroundColor Yellow
Write-Host ""

# 現在の実行ポリシーを確認
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
Write-Host "現在の実行ポリシー: $currentPolicy" -ForegroundColor Cyan

# 選択肢を提示
Write-Host ""
Write-Host "修正方法を選択してください:" -ForegroundColor Yellow
Write-Host "1. 実行ポリシーを RemoteSigned に変更（推奨）" -ForegroundColor Green
Write-Host "2. 実行ポリシーを Bypass に変更（一時的）" -ForegroundColor Yellow
Write-Host "3. npm.cmd を使用するように環境を設定" -ForegroundColor Cyan
Write-Host "4. キャンセル" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "選択 (1-4)"

switch ($choice) {
    "1" {
        Write-Host "実行ポリシーを RemoteSigned に変更します..." -ForegroundColor Green
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "✅ 実行ポリシーが変更されました" -ForegroundColor Green
            Write-Host "これでnpmコマンドが正常に動作します" -ForegroundColor Green
        } catch {
            Write-Host "❌ 実行ポリシーの変更に失敗しました" -ForegroundColor Red
            Write-Host "管理者権限でPowerShellを実行してください" -ForegroundColor Yellow
        }
    }
    "2" {
        Write-Host "実行ポリシーを Bypass に変更します..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
            Write-Host "✅ 現在のセッションでのみ実行ポリシーが変更されました" -ForegroundColor Green
        } catch {
            Write-Host "❌ 実行ポリシーの変更に失敗しました" -ForegroundColor Red
        }
    }
    "3" {
        Write-Host "npm.cmd を使用する設定を適用します..." -ForegroundColor Cyan
        
        # エイリアスを作成
        Write-Host "PowerShellプロファイルにエイリアスを追加します..." -ForegroundColor Yellow
        
        $profilePath = $PROFILE.CurrentUserAllHosts
        $profileDir = Split-Path -Parent $profilePath
        
        # プロファイルディレクトリが存在しない場合は作成
        if (-not (Test-Path $profileDir)) {
            New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
        }
        
        # エイリアス設定を追加
        $aliasCommand = @"

# NPM実行ポリシー回避用エイリアス
Set-Alias -Name npm-run -Value { cmd /c "npm `$args" }
function npm { cmd /c "npm `$args" }
"@
        
        if (Test-Path $profilePath) {
            $content = Get-Content $profilePath -Raw
            if ($content -notlike "*npm-run*") {
                Add-Content -Path $profilePath -Value $aliasCommand
            }
        } else {
            Set-Content -Path $profilePath -Value $aliasCommand
        }
        
        Write-Host "✅ エイリアスが設定されました" -ForegroundColor Green
        Write-Host "新しいPowerShellセッションで有効になります" -ForegroundColor Yellow
    }
    "4" {
        Write-Host "キャンセルしました" -ForegroundColor Gray
    }
    default {
        Write-Host "無効な選択です" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 ヒント:" -ForegroundColor Yellow
Write-Host "  すべてのスクリプトは自動的にcmd経由でnpmを実行するように更新されています" -ForegroundColor Gray
Write-Host "  実行ポリシーを変更しなくても動作します" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 フロントエンドを手動で起動する場合:" -ForegroundColor Cyan
Write-Host "  cd frontend" -ForegroundColor White
Write-Host "  cmd /c \"npm run dev\"" -ForegroundColor White
Write-Host ""