# ファイル名変更スクリプト
$frontendPath = "E:\Generate-autounattendxml-files-for-Windows11\WebUI\frontend\src\pages"

# 古いindex.tsxをバックアップ
if (Test-Path "$frontendPath\index.tsx") {
    Move-Item -Path "$frontendPath\index.tsx" -Destination "$frontendPath\index_old.tsx" -Force
    Write-Host "index.tsx を index_old.tsx にバックアップしました" -ForegroundColor Green
}

# 新しいindex_new.tsxをindex.tsxにリネーム
if (Test-Path "$frontendPath\index_new.tsx") {
    Move-Item -Path "$frontendPath\index_new.tsx" -Destination "$frontendPath\index.tsx" -Force
    Write-Host "index_new.tsx を index.tsx にリネームしました" -ForegroundColor Green
}

Write-Host "ファイル名の変更が完了しました" -ForegroundColor Cyan