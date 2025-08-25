# PowerShell実行ポリシー修正スクリプト
# npm.ps1の実行エラーを解決

Write-Host "PowerShell実行ポリシーを確認・修正します..." -ForegroundColor Yellow
Write-Host ""

# 現在の実行ポリシーを確認
$currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
Write-Host "現在の実行ポリシー (CurrentUser): $currentPolicy" -ForegroundColor Cyan

# 実行ポリシーが制限されている場合
if ($currentPolicy -in @("Restricted", "AllSigned")) {
    Write-Host ""
    Write-Host "実行ポリシーが制限されています。" -ForegroundColor Yellow
    Write-Host "RemoteSignedに変更することで、npmコマンドが実行可能になります。" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "実行ポリシーを変更しますか？ (Y/N)"
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "✅ 実行ポリシーをRemoteSignedに変更しました" -ForegroundColor Green
            
            # 変更後の確認
            $newPolicy = Get-ExecutionPolicy -Scope CurrentUser
            Write-Host "新しい実行ポリシー: $newPolicy" -ForegroundColor Green
            Write-Host ""
            Write-Host "これでStart-WebUI.ps1が正常に動作するはずです。" -ForegroundColor Green
        } catch {
            Write-Host "❌ 実行ポリシーの変更に失敗しました" -ForegroundColor Red
            Write-Host "管理者権限で実行するか、以下のコマンドを管理者PowerShellで実行してください:" -ForegroundColor Yellow
            Write-Host "  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor White
        }
    } else {
        Write-Host "実行ポリシーの変更をキャンセルしました。" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "代替方法:" -ForegroundColor Cyan
        Write-Host "1. start-frontend.bat を使用してフロントエンドを起動" -ForegroundColor White
        Write-Host "2. コマンドプロンプトから 'npm run dev' を実行" -ForegroundColor White
    }
} else {
    Write-Host "✅ 実行ポリシーは適切に設定されています" -ForegroundColor Green
}

Write-Host ""
Write-Host "Enterキーで終了..."
Read-Host