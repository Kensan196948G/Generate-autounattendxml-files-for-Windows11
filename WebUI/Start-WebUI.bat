@echo off
chcp 65001 > nul
title Windows 11 無人応答ファイル生成システム

echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║     Windows 11 無人応答ファイル生成システム - 統合起動                  ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

echo システムを起動しています...
echo.

REM バックエンドサーバーを新しいウィンドウで起動
echo バックエンドサーバーを起動中...
start "バックエンド - Context7 + SubAgent(42体)" cmd /k "cd /d backend && if exist venv\Scripts\python.exe (venv\Scripts\python.exe main.py) else (python main.py)"

REM 3秒待機
timeout /t 3 /nobreak > nul

REM フロントエンドサーバーを新しいウィンドウで起動
echo フロントエンドサーバーを起動中...
start "フロントエンド - Schneegans.de スタイルUI" cmd /k "cd /d frontend && set NEXT_PUBLIC_API_URL=http://192.168.3.92:8080/api && set NEXT_PUBLIC_LOCAL_IP=192.168.3.92 && npm run dev"

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo ✅ システムが起動しました！
echo.
echo 📌 アクセスURL:
echo    フロントエンド:  http://192.168.3.92:3050
echo    バックエンドAPI: http://192.168.3.92:8080
echo    API仕様書:      http://192.168.3.92:8080/api/docs
echo.
echo 🛑 停止方法:
echo    各ウィンドウで Ctrl+C を押してください
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM 5秒後にブラウザを開く
timeout /t 5 /nobreak > nul
start http://192.168.3.92:3050

pause