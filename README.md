# Windows 11 Sysprep 無人応答ファイル生成システム

Windows 11の無人インストール用応答ファイル（autounattend.xml）を自動生成する総合システムです。

## 🎯 システム概要

企業環境でのPCキッティング作業を効率化し、Windows 11の展開を自動化するための包括的なソリューションを提供します。

## 🚀 2つのバージョン

### 1. WebUI版（推奨） ✨
モダンなWebインターフェースで直感的に操作可能
- **📁 フォルダ**: `/WebUI`
- **📖 ドキュメント**: `/Docs/XML-Document-WebUIversion`
- **✨ 特徴**: 
  - ブラウザベースの使いやすいUI
  - 日本語設定ログの自動生成
  - 42体のSubAgentによる並列処理
  - リアルタイムプレビュー

### 2. PowerShell版 ⚡
コマンドラインベースの軽量版
- **📁 フォルダ**: `/PowerShell`
- **📖 ドキュメント**: `/Docs/XML-Document-PowershellVersion`
- **✨ 特徴**: 
  - スクリプトによる自動化
  - バッチ処理対応
  - 最小限の依存関係

## 📋 クイックスタート

### WebUI版の起動（推奨）

```powershell
# WebUIフォルダに移動
cd WebUI

# 自動セットアップ・起動
.\Auto-Fix-All-Simple.ps1 -Verbose

# ブラウザで以下のURLにアクセス
# http://[あなたのIPアドレス]:3050
```

### PowerShell版の使用

```powershell
# PowerShellフォルダに移動
cd PowerShell

# 基本的な使用
.\Generate-UnattendXML.ps1 -Preset Enterprise -Output autounattend.xml
```

## ✨ 主な機能

### 基本機能
- ✅ **Windows 11全エディション対応** (Pro/Home/Enterprise/Education)
- ✅ **完全日本語対応** (UI、ログ、ドキュメント)
- ✅ **ユーザーアカウント自動設定** (複数アカウント対応)
- ✅ **ネットワーク自動設定** (Wi-Fi、有線LAN)

### 高度な機能
- ✅ **Windows 11要件バイパス** (TPM 2.0、セキュアブート、CPU要件)
- ✅ **Microsoftアカウントバイパス** (ローカルアカウントでのセットアップ)
- ✅ **Windows機能の事前設定** (.NET、Hyper-V、WSL等)
- ✅ **プライバシー設定の自動化**
- ✅ **OOBE画面のスキップ設定**

### 出力機能
- ✅ **autounattend.xml生成**
- ✅ **設定内容の日本語ログ出力**
- ✅ **ZIP形式での一括ダウンロード**

## 📁 プロジェクト構成

```
Generate-autounattendxml-files-for-Windows11/
├── 📂 WebUI/                           # WebUI版
│   ├── 📂 backend/                    # FastAPIバックエンド
│   │   ├── main.py                   # APIサーバー
│   │   ├── enhanced_xml_generator.py # XML生成エンジン
│   │   ├── config_transformer.py     # 設定変換
│   │   └── config_log_generator.py   # ログ生成
│   ├── 📂 frontend/                   # Next.js フロントエンド
│   │   └── src/
│   │       ├── pages/                # UIページ
│   │       └── services/             # API通信
│   └── *.ps1                          # 管理スクリプト群
│
├── 📂 PowerShell/                      # PowerShell版
│   ├── Generate-UnattendXML.ps1      # メインスクリプト
│   ├── 📂 Modules/                    # 機能モジュール
│   └── 📂 Configs/                    # プリセット設定
│
├── 📂 Docs/                            # ドキュメント
│   ├── 📂 XML-Document-WebUIversion/  # WebUI版詳細ドキュメント
│   │   ├── README.md                 # 概要
│   │   ├── システム仕様書/           # 技術仕様
│   │   ├── 利用ガイド/               # 使い方
│   │   ├── API仕様書/                # API仕様
│   │   ├── 設定リファレンス/         # 設定項目詳細
│   │   └── トラブルシューティング/   # 問題解決
│   └── 📂 XML-Document-PowershellVersion/
│
├── 📂 src/                             # 共通コアモジュール（Python）
├── 📂 tests/                           # テストコード
├── 📂 configs/                         # 設定ファイル例
└── 📂 test-outputs/                    # テスト出力

```

## 🔧 必要環境

### WebUI版
- Windows 10/11
- Python 3.10以上
- Node.js 18以上
- PowerShell 5.1以上

### PowerShell版
- Windows 10/11
- PowerShell 5.1以上

## 📖 詳細ドキュメント

- 📘 [WebUI版 完全ガイド](./Docs/XML-Document-WebUIversion/README.md)
- 📗 [PowerShell版 ガイド](./Docs/XML-Document-PowershellVersion/README.md)
- 📙 [API仕様書](./Docs/XML-Document-WebUIversion/API仕様書/API仕様.md)
- 📕 [設定項目リファレンス](./Docs/XML-Document-WebUIversion/設定リファレンス/設定項目一覧.md)
- 📓 [トラブルシューティング](./Docs/XML-Document-WebUIversion/トラブルシューティング/問題解決ガイド.md)

## 🚀 使用例

### 企業向け設定
```yaml
エディション: Windows 11 Enterprise
ユーザー: 
  - local-admin (管理者)
  - domain-user (標準ユーザー)
機能: .NET Framework 3.5
ネットワーク: 企業Wi-Fi自動設定
プライバシー: すべてスキップ
```

### 開発環境向け設定
```yaml
エディション: Windows 11 Pro
ユーザー: dev-admin
機能: Hyper-V, WSL, .NET
要件バイパス: すべて有効
```

## 🤝 貢献

プロジェクトへの貢献を歓迎します：
1. Issueで問題報告や機能提案
2. Pull Requestでコード貢献
3. ドキュメントの改善

## 📄 ライセンス

MIT License

## ⚠️ 注意事項

- 生成されたXMLファイルは本番環境で使用する前に十分なテストを行ってください
- Windows 11の要件バイパスはMicrosoftのサポート対象外となる可能性があります
- 企業環境での使用には組織のポリシーを確認してください

## 📞 サポート

問題や質問がある場合：
1. [トラブルシューティングガイド](./Docs/XML-Document-WebUIversion/トラブルシューティング/問題解決ガイド.md)を確認
2. GitHubのIssueセクションで報告
3. ログファイル（`logs/`フォルダ）を添付して詳細を説明

---

*最終更新: 2025年8月24日 | バージョン: 2.0.0*