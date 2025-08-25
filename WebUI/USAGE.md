# Windows 11 無人応答ファイル生成システム - 使用方法

## 📋 使用方法

### 基本起動:

```powershell
# 通常起動
.\Start-WebUI.ps1

# 完全統合版起動（すべての機能有効）
.\Start-WebUI-Complete.ps1 -EnableAutoRepair -RunTests
```

### オプション:

```powershell
# 自動修復機能を有効化
.\Start-WebUI-Complete.ps1 -EnableAutoRepair

# Playwrightテストを実行
.\Start-WebUI-Complete.ps1 -RunTests

# デバッグモード
.\Start-WebUI-Complete.ps1 -Debug

# 強制再起動
.\Start-WebUI-Complete.ps1 -ForceRestart
```

## 🌐 アクセスURL

- **フロントエンド**: http://192.168.3.92:3050
- **バックエンドAPI**: http://192.168.3.92:8080
- **API仕様書**: http://192.168.3.92:8080/api/docs
- **ヘルスチェック**: http://192.168.3.92:8080/api/health

## 🚀 主な機能

### 1. 地域と言語設定
- タイムゾーン選択
- UI言語設定
- 入力方式設定

### 2. コンピューター情報
- コンピューター名
- 組織情報
- プロセッサアーキテクチャ

### 3. ユーザーアカウント管理
- 複数ユーザー作成
- グループ設定
- 自動ログオン設定

### 4. ネットワーク設定
- ワークグループ/ドメイン参加
- IPv6無効化
- ファイアウォール設定

### 5. Windows機能
- .NET Framework 3.5
- Hyper-V
- WSL
- Windows Sandbox

### 6. プライバシー設定
- テレメトリ無効化
- Cortana無効化
- 位置情報サービス

## 🔧 技術仕様

- **フロントエンド**: Next.js 14 + React 18 + TypeScript
- **バックエンド**: FastAPI + Python 3.10+
- **テスト**: Playwright
- **並列処理**: asyncio + Claude-flow
- **自動修復**: 最大20回リトライ with エラー分類

## 📊 システム監視

```powershell
# サーバー監視（自動再起動付き）
.\Monitor-Servers.ps1 -AutoRestart

# 停止
.\Stop-WebUI.ps1
```

## 🎯 プリセット

システムには以下のプリセット設定が含まれています：

- **企業向け**: セキュリティ重視の設定
- **開発環境**: 開発ツールを有効化
- **最小構成**: 最小限の機能のみ

## 📝 詳細設定

### Context7機能
高度なコンテキスト管理システムにより、設定の一貫性と依存関係を自動管理

### SubAgent機能（42体）
各設定項目に特化した専門エージェントが並列処理で高速化

### Claude-flow並列処理
複数のタスクを同時実行し、XML生成時間を大幅短縮

### 自動エラー修復
最大20回の自動リトライとエラー分類による適切な修復戦略

## 💡 使用例

### 企業環境向けの設定
1. `.\Start-WebUI.ps1` を実行
2. ブラウザで http://192.168.3.92:3050 を開く
3. 「企業向け」プリセットを選択
4. 必要に応じてカスタマイズ
5. 「unattend.xml を生成」をクリック

### 開発環境向けの設定
1. `.\Start-WebUI.ps1` を実行
2. 「開発環境」プリセットを選択
3. Windows機能セクションで追加機能を有効化
4. XML生成

## 🆘 トラブルシューティング

### サーバーが起動しない場合
```powershell
# 既存プロセスを強制終了して再起動
.\Start-WebUI.ps1 -ForceRestart
```

### ポートが使用中の場合
```powershell
# ポート確認
netstat -ano | findstr :3050
netstat -ano | findstr :8080

# 強制停止
.\Stop-WebUI.ps1 -Force
```

### 依存関係の問題
```powershell
# バックエンド依存関係の再インストール
cd backend
.\venv\Scripts\pip.exe install -r requirements.txt

# フロントエンド依存関係の再インストール
cd frontend
npm install
```

## 📚 関連ドキュメント

- [README.md](README.md) - システム概要
- [CLAUDE.md](../CLAUDE.md) - プロジェクト仕様
- API仕様書: http://192.168.3.92:8080/api/docs