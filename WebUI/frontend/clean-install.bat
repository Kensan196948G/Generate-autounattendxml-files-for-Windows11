@echo off
chcp 65001 > nul
title Node.js依存関係クリーンインストール

echo ============================================================
echo Node.js依存関係のクリーンインストール
echo ============================================================
echo.

REM node_modulesとpackage-lock.jsonを削除
if exist node_modules (
    echo node_modulesフォルダを削除中...
    rmdir /s /q node_modules
)

if exist package-lock.json (
    echo package-lock.jsonを削除中...
    del package-lock.json
)

echo.
echo npmキャッシュをクリア中...
npm cache clean --force

echo.
echo 新しい依存関係をインストール中...
npm install

echo.
echo ============================================================
echo インストール完了！
echo.
echo 次のコマンドでフロントエンドを起動できます:
echo   npm run dev
echo ============================================================
echo.
pause