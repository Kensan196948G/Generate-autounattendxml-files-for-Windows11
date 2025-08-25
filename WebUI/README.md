# Windows 11 無人応答ファイル生成システム WebUI

## 🚀 クイックスタート

### 基本起動（推奨）

```powershell
# 通常起動
.\Start-WebUI.ps1
```

これで、バックエンドとフロントエンドの両方が自動的に起動します。

### 完全統合版（すべての機能有効）

```powershell
# 自動修復・テスト機能付き
.\Start-WebUI-Complete.ps1 -EnableAutoRepair -RunTests
```

## 🌐 アクセスURL

- **フロントエンド**: http://192.168.3.92:3050
- **バックエンドAPI**: http://192.168.3.92:8080
- **API仕様書**: http://192.168.3.92:8080/api/docs
- **ヘルスチェック**: http://192.168.3.92:8080/api/health

## 概要

Windows 11のSysprep用unattend.xmlファイルを自動生成するWebベースのシステムです。
[Schneegans.de Unattend Generator](https://schneegans.de/windows/unattend-generator/)を参考に、日本語化と機能拡張を行いました。

## システム構成

- **フロントエンド**: Next.js (React) - ポート3050 (PowerShellで起動)
- **バックエンド**: FastAPI (Python) - ポート8080
- **並列処理**: Claude-flow + 42体のSubAgent
- **リアルタイム通信**: WebSocket

## 特徴

### 🎯 主要機能
- **日本語完全対応**: UIからエラーメッセージまですべて日本語
- **42体のSubAgent**: 各設定領域を専門的に処理
- **リアルタイム生成**: WebSocketによる進捗表示
- **プリセット対応**: Enterprise/Development/Minimal
- **ネットワークアクセス**: IPアドレス自動検出で他PCからもアクセス可能

### 📋 対応する設定項目

#### ユーザー管理
- 複数ユーザーアカウント作成
- 管理者権限設定
- パスワードポリシー
- 自動ログオン設定
- Administratorアカウント無効化

#### ネットワーク設定
- IPv6無効化
- Windows Firewall設定
- Bluetooth無効化
- DNS設定
- グループポリシー設定

#### Windows機能
- .NET Framework 3.5
- Hyper-V
- Windows Subsystem for Linux
- Windows Sandbox
- IIS

#### アプリケーション設定
- 既定のブラウザ/メール/PDF
- Office初回起動設定
- タスクバー設定
- スタートメニュー設定

## インストール

### 前提条件
- Windows 10/11
- Python 3.8以上
- Node.js 16以上
- PowerShell 5.1以上

### セットアップ

#### 方法1: 自動セットアップ（推奨）

**PowerShellで実行:**
```powershell
cd E:\Generate-autounattendxml-files-for-Windows11\WebUI
.\Start-WebUI.ps1
```

**注意**: PowerShellでは現在のディレクトリのスクリプトを実行する際、必ず `.\` を付ける必要があります。

**コマンドプロンプトで実行:**
```batch
cd E:\Generate-autounattendxml-files-for-Windows11\WebUI
start-webui.bat
```

#### IPアドレス検出のテスト

起動前にIPアドレスが正しく検出されるか確認する場合:
```powershell
.\Test-IPDetection.ps1
```

#### 方法2: 手動セットアップ

1. **バックエンドのセットアップ**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

2. **フロントエンドのセットアップ**
```bash
cd frontend
npm install
npm run dev
```

## 使用方法

### アクセス方法

システム起動後、以下のURLにアクセス:
- **フロントエンド**: http://[あなたのIP]:3050
- **API仕様書**: http://[あなたのIP]:8080/api/docs

### 基本的な使い方

1. **プリセット選択または新規作成**
   - Enterprise: 企業環境向け（セキュリティ重視）
   - Development: 開発環境向け（開発ツール有効）
   - Minimal: 最小構成（軽量設定）
   - カスタム: 手動で詳細設定

2. **設定の入力**
   - Step 1: 基本設定（コンピューター名、タイムゾーン等）
   - Step 2: ユーザーアカウント設定
   - Step 3: ネットワーク設定
   - Step 4: Windows機能設定
   - Step 5: アプリケーション設定

3. **XMLの生成と保存**
   - 「生成」ボタンをクリック
   - リアルタイムで進捗を確認
   - 生成完了後、プレビューを確認
   - 「ダウンロード」ボタンで保存

### 高度な使い方

#### カスタムプリセットの作成
```json
// frontend/src/presets/custom.json
{
  "name": "カスタムプリセット",
  "description": "独自の設定テンプレート",
  "settings": {
    "users": [...],
    "network": {...},
    "features": {...}
  }
}
```

#### APIの直接利用
```python
import requests

# XML生成
response = requests.post(
    "http://localhost:8080/api/generate",
    json={
        "preset": "enterprise",
        "custom_settings": {...}
    }
)

xml_content = response.json()["xml"]
```

## トラブルシューティング

### よくある問題

#### ポートが使用中
```powershell
# ポート3050の確認
netstat -ano | findstr :3050

# ポート8080の確認
netstat -ano | findstr :8080

# プロセスの終了
taskkill /PID [プロセスID] /F
```

#### 依存関係のエラー
```bash
# Pythonパッケージの再インストール
pip install -r requirements.txt --force-reinstall

# Node.jsパッケージの再インストール
npm ci
```

#### ネットワークアクセスできない
- Windows Defenderファイアウォールで3050と8080ポートを許可
- ネットワークプロファイルをプライベートに設定

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────┐
│                   ブラウザ                        │
│              http://[IP]:3050                    │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼──────┐        ┌────────▼────────┐
│  Next.js     │        │   WebSocket     │
│  Frontend    │◄───────┤   リアルタイム   │
│  Port: 3050  │        │   通信          │
└──────┬───────┘        └────────┬────────┘
       │                         │
       │         REST API        │
       │                         │
┌──────▼──────────────────────────▼────────┐
│           FastAPI Backend                 │
│           Port: 8080                      │
├───────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐      │
│  │Claude-flow  │  │ 42 SubAgents │      │
│  │並列処理      │◄─┤ 専門処理      │      │
│  └─────────────┘  └──────────────┘      │
└───────────────────────────────────────────┘
```

## 開発者向け情報

### プロジェクト構造
```
WebUI/
├── backend/              # FastAPIバックエンド
│   ├── app/
│   │   ├── agents/      # 42体のSubAgent
│   │   ├── api/         # APIエンドポイント
│   │   ├── claude_flow/ # 並列処理エンジン
│   │   ├── core/        # 設定管理
│   │   ├── models/      # データモデル
│   │   └── services/    # ビジネスロジック
│   └── main.py          # メインアプリケーション
├── frontend/            # Next.jsフロントエンド
│   ├── src/
│   │   ├── components/  # UIコンポーネント
│   │   ├── pages/       # ページコンポーネント
│   │   ├── services/    # API通信
│   │   └── hooks/       # カスタムフック
│   └── package.json
├── Start-WebUI.ps1      # PowerShell起動スクリプト
└── start-webui.bat      # バッチ起動スクリプト
```

### ビルドとデプロイ

#### プロダクションビルド
```bash
# フロントエンド
cd frontend
npm run build
npm start

# バックエンド
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

#### PM2での永続化
```bash
# PM2のインストール
npm install -g pm2

# プロセスの登録と起動
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## ライセンス

MIT License

## 謝辞

このプロジェクトは[Schneegans.de](https://schneegans.de/windows/unattend-generator/)の
Unattend Generatorに影響を受けて開発されました。

## サポート

問題や要望がある場合は、GitHubのIssueを作成してください。

---

*最終更新日: 2024年8月23日*
*バージョン: 2.0.0*