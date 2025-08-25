"""
Windows 11 Sysprep応答ファイル生成システム - シンプル版バックエンド
最小限の依存関係で動作確認用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socket
import os

# IPアドレスの自動検出
def get_local_ip():
    """ローカルIPアドレスを取得（APIPA除外）"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        
        if not ip.startswith("169.254."):
            return ip
        
        return "127.0.0.1"
    except Exception as e:
        print(f"IP検出エラー: {e}")
        return "127.0.0.1"

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Windows 11 無人応答ファイル生成システム",
    description="Windows 11のSysprep用unattend.xmlファイルを自動生成するWebAPIシステム",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS設定
LOCAL_IP = get_local_ip()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3050",
        f"http://{LOCAL_IP}:3050",
        "http://127.0.0.1:3050"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Windows 11 無人応答ファイル生成システム APIサーバー（シンプル版）",
        "version": "2.0.0",
        "api_docs": f"http://{LOCAL_IP}:8080/api/docs",
        "frontend": f"http://{LOCAL_IP}:3050",
        "status": "running"
    }

@app.get("/api/status")
async def get_status():
    """システムステータス"""
    return {
        "status": "operational",
        "backend": "running",
        "ip_address": LOCAL_IP
    }

@app.get("/api/presets")
async def get_presets():
    """プリセット一覧"""
    return [
        {
            "name": "enterprise",
            "preset_type": "enterprise",
            "description": "企業環境向け設定（セキュリティ重視）",
            "is_builtin": True
        },
        {
            "name": "development",
            "preset_type": "development",
            "description": "開発環境向け設定（開発ツール有効）",
            "is_builtin": True
        },
        {
            "name": "minimal",
            "preset_type": "minimal",
            "description": "最小構成（軽量設定）",
            "is_builtin": True
        }
    ]

@app.post("/api/xml/generate")
async def generate_xml(request: dict):
    """XML生成（ダミー）"""
    return {
        "session_id": "test-session-001",
        "status": "processing",
        "message": "XML生成を開始しました"
    }

if __name__ == "__main__":
    print("="*60)
    print("Windows 11 無人応答ファイル生成システム（シンプル版）")
    print("="*60)
    print(f"ローカルIP: {LOCAL_IP}")
    print(f"バックエンドURL: http://{LOCAL_IP}:8080")
    print(f"API仕様書: http://{LOCAL_IP}:8080/api/docs")
    print(f"フロントエンドURL: http://{LOCAL_IP}:3050")
    print("="*60)
    
    # Uvicornサーバーの起動
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )