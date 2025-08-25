# 🚀 Windows 11 無人応答ファイル生成システム - スタートガイド

## ここから始めましょう！

### ✨ 最も簡単な方法

PowerShellを開いて、以下のコマンドを実行するだけです：

```powershell
.\Start-WebUI.ps1
```

これだけで、システム全体が起動します！

---

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

---

## 🌐 アクセスURL

システム起動後、以下のURLにアクセスできます：

- **フロントエンド**: http://192.168.3.92:3050
- **バックエンドAPI**: http://192.168.3.92:8080
- **API仕様書**: http://192.168.3.92:8080/api/docs
- **ヘルスチェック**: http://192.168.3.92:8080/api/health

---

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

---

## 🔧 技術仕様

- **フロントエンド**: Next.js 14 + React 18 + TypeScript
- **バックエンド**: FastAPI + Python 3.10+
- **テスト**: Playwright
- **並列処理**: asyncio + Claude-flow
- **自動修復**: 最大20回リトライ with エラー分類

---

## 📊 システム監視

```powershell
# サーバー監視（自動再起動付き）
.\Monitor-Servers.ps1 -AutoRestart

# 停止
.\Stop-WebUI.ps1
```

---

## 🎯 使い方の例

### 企業向け設定を作成する場合：

1. **システムを起動**
   ```powershell
   .\Start-WebUI.ps1
   ```

2. **ブラウザでアクセス**
   - http://192.168.3.92:3050 を開く

3. **設定を選択**
   - 「企業向け」プリセットをクリック
   - 必要に応じて詳細設定を調整

4. **XML生成**
   - 「unattend.xml を生成」ボタンをクリック
   - ファイルが自動的にダウンロードされます

---

## 🆘 困ったときは

### サーバーが起動しない
```powershell
.\Start-WebUI.ps1 -ForceRestart
```

### ポートが使用中
```powershell
.\Stop-WebUI.ps1 -Force
.\Start-WebUI.ps1
```

### 依存関係の問題
```powershell
# バックエンド
cd backend
.\venv\Scripts\pip.exe install -r requirements.txt

# フロントエンド
cd frontend
npm install
```

---

## 📚 詳細ドキュメント

- [USAGE.md](USAGE.md) - 詳細な使用方法
- [README.md](README.md) - システム概要
- [CLAUDE.md](../CLAUDE.md) - プロジェクト仕様

---

## 💡 ヒント

- システムは完全に日本語対応しています
- Schneegans.de スタイルの美しいUIを採用
- 42体のSubAgentが並列処理で高速動作
- Context7機能で設定の一貫性を保証
- 自動エラー修復で安定動作

---

## 🎉 さあ、始めましょう！

```powershell
.\Start-WebUI.ps1
```

このコマンドを実行して、Windows 11の無人セットアップを簡単に実現しましょう！