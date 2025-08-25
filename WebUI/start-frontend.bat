@echo off
chcp 65001 > nul
title Windows 11 無人応答ファイル生成システム - フロントエンド

echo ============================================================
echo Windows 11 無人応答ファイル生成システム
echo フロントエンド起動
echo ============================================================
echo.

cd frontend

REM 環境変数設定
set NEXT_PUBLIC_API_URL=http://192.168.3.92:8080/api
set NEXT_PUBLIC_LOCAL_IP=192.168.3.92

echo 環境変数を設定しました:
echo   API URL: %NEXT_PUBLIC_API_URL%
echo   Local IP: %NEXT_PUBLIC_LOCAL_IP%
echo.

REM node_modulesが存在しない場合はインストール
if not exist node_modules (
    echo Node.js依存関係をインストール中...
    npm install
    echo.
)

echo フロントエンドサーバーを起動中...
echo URL: http://192.168.3.92:3050
echo.
echo 終了するには Ctrl+C を押してください
echo ============================================================
echo.

npm run dev