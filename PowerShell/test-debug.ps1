# デバッグスクリプト
$VerbosePreference = 'Continue'
$DebugPreference = 'Continue'

cd 'E:\Generate-autounattendxml-files-for-Windows11\PowerShell'

# スクリプト実行
& '.\Generate-UnattendXML-V2.ps1' -Preset Minimal -OutputPath '.\Outputs' -Verbose

# 生成されたファイルを確認
$latestXml = Get-ChildItem '.\Outputs\unattend_*.xml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestXml) {
    Write-Host "`n=== 生成されたXMLの最初の100行 ===" -ForegroundColor Cyan
    Get-Content $latestXml.FullName | Select-Object -First 100
}