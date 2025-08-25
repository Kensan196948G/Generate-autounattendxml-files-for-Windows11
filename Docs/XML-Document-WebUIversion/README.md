# Windows 11 Sysprep 無人応答ファイル生成システム - WebUI版

## 📋 システム概要

Windows 11のSysprep実行時に使用する無人応答ファイル（autounattend.xml）を、Webインターフェースから簡単に生成できるシステムです。

### ✨ 主要機能

- 🌐 **Webブラウザベースの直感的なUI**
- 📝 **日本語設定ログの同時生成**
- 🔧 **包括的なWindows設定のカスタマイズ**
- ⚡ **42体のSubAgentによる並列処理**
- 🔄 **Context7による高度な設定管理**

## 🚀 クイックスタート

### 必要要件

- Windows 11/10
- Python 3.10以上
- Node.js 18以上
- PowerShell 5.1以上

### インストール手順

```powershell
# 1. WebUIフォルダに移動
cd E:\Generate-autounattendxml-files-for-Windows11\WebUI

# 2. 自動セットアップスクリプトを実行
.\Auto-Fix-All-Simple.ps1 -Verbose

# 3. ブラウザでアクセス
# http://192.168.3.92:3050/ （IPアドレスは環境により異なります）
```

## 📁 プロジェクト構成

```
WebUI/
├── backend/          # FastAPIバックエンド
│   ├── main.py      # メインAPIサーバー
│   ├── enhanced_xml_generator.py  # XML生成エンジン
│   ├── config_transformer.py      # 設定変換モジュール
│   └── config_log_generator.py    # ログ生成モジュール
├── frontend/         # Next.js/Reactフロントエンド
│   └── src/
│       ├── pages/   # UIページ
│       └── services/# API通信サービス
└── *.ps1            # 管理用PowerShellスクリプト
```

## 🔌 システムアーキテクチャ

### バックエンド（FastAPI）
- **ポート**: 8081
- **エンドポイント**: 
  - `/api/generate-unattend` - XML生成
  - `/api/generate-with-log` - XML + ログ生成（ZIP）
  - `/api/status` - システム状態
  - `/api/docs` - API仕様書

### フロントエンド（Next.js）
- **ポート**: 3050
- **フレームワーク**: React + TypeScript
- **スタイリング**: CSS Modules

## 📖 詳細ドキュメント

- [システム仕様書](./システム仕様書/システム詳細仕様.md)
- [利用ガイド](./利用ガイド/使い方ガイド.md)
- [API仕様書](./API仕様書/API仕様.md)
- [設定リファレンス](./設定リファレンス/設定項目一覧.md)
- [トラブルシューティング](./トラブルシューティング/問題解決ガイド.md)

## 💡 主な設定項目

### 基本設定
- 言語・地域設定（日本語対応）
- Windowsエディション選択
- プロダクトキー設定

### ユーザーアカウント
- ローカル管理者アカウント作成
- パスワード暗号化
- グループ設定

### ネットワーク
- Wi-Fi自動設定
- ネットワーク要件バイパス
- Microsoftアカウントバイパス

### Windows機能
- .NET Framework 3.5
- Hyper-V
- WSL (Windows Subsystem for Linux)
- Windows Sandbox

### システム設定
- Windows 11要件バイパス（TPM/セキュアブート）
- プライバシー設定
- OOBE画面スキップ

## 🔧 管理コマンド

### システム起動
```powershell
# 完全起動
.\Auto-Fix-All-Simple.ps1 -Verbose

# 個別起動
.\Start-Backend-8081.ps1  # バックエンドのみ
.\Start-Frontend.ps1       # フロントエンドのみ
```

### システム停止
```powershell
.\Stop-WebUI.ps1
```

### トラブルシューティング
```powershell
.\Fix-Port-Conflict.ps1   # ポート競合解決
.\Test-Connection.ps1      # 接続テスト
```

## 📦 生成ファイル

### XMLのみダウンロード
- `autounattend.xml` - Windows無人応答ファイル

### XML + ログダウンロード（ZIP）
- `autounattend.xml` - Windows無人応答ファイル
- `設定ログ.txt` - 日本語での詳細設定記録

## 🔄 更新履歴

### v2.0.0 (2025-08-24)
- WebUI版の完全実装
- 日本語設定ログ生成機能追加
- 42体のSubAgent統合
- Context7エンジン実装

### v1.0.0
- PowerShell版の初期リリース

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストは歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📧 サポート

問題や質問がある場合は、GitHubのIssueセクションで報告してください。

---

*このシステムは継続的に改善されています。最新の情報はこのドキュメントを参照してください。*