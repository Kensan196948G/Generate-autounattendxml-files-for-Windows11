# Windows 11 無人応答ファイル生成システム

## 📋 概要

Windows 11の無人インストール（Sysprep）用の応答ファイル（autounattend.xml）を自動生成する包括的なシステムです。企業環境でのPC大量展開やキッティング作業を効率化します。

### ✨ 主な特徴

- **全23項目の包括的な設定対応** - 2024年8月24日完全実装
- **WebUIによる直感的な操作** - React/Next.jsベースのモダンなインターフェース
- **42体のSubAgentによる並列処理** - 高速かつ効率的な設定処理
- **Context7エンジン** - 高度な設定管理と最適化
- **日本語環境に完全対応** - UIから生成されるログまで完全日本語化

## 🚀 クイックスタート

### システム要件

- Windows 10/11
- Python 3.10以上
- Node.js 18以上
- PowerShell 5.1以上

### インストール手順

```powershell
# リポジトリのクローン
git clone https://github.com/your-org/Generate-autounattendxml-files-for-Windows11.git
cd Generate-autounattendxml-files-for-Windows11

# WebUIの起動
cd WebUI
.\Start-WebUI.ps1
```

起動後、以下のURLでアクセス可能：
- フロントエンド: http://localhost:3050
- バックエンドAPI: http://localhost:8081
- API仕様書: http://localhost:8081/api/docs

## 📚 ドキュメント構成

### 利用者向け
- [使い方ガイド](./XML-Document-WebUIversion/利用ガイド/使い方ガイド.md) - WebUIの基本的な使い方
- [設定項目一覧（全23項目）](./設定項目一覧_全23項目.md) - 設定可能な全項目の詳細
- [プリセット設定ガイド](./プリセット設定ガイド.md) - 用途別の推奨設定

### 技術者向け
- [システムアーキテクチャ](./システムアーキテクチャ.md) - システム構成と技術詳細
- [API仕様書](./API仕様書.md) - REST APIの詳細仕様
- [XML生成仕様](./XML生成仕様.md) - autounattend.xmlの生成ロジック

### 管理者向け
- [インストール手順書](./インストール手順書.md) - 詳細なセットアップ手順
- [トラブルシューティング](./トラブルシューティングガイド.md) - よくある問題と解決方法
- [運用ガイド](./運用ガイド.md) - 本番環境での運用方法

## 🎯 対応設定項目（全23項目）

### 基本設定（項目1-11）
1. **地域と言語の設定** - 表示言語、入力方式、タイムゾーン等
2. **プロセッサー・アーキテクチャ** - x86/x64/ARM64対応
3. **セットアップの挙動** - OOBE、プライバシー設定のスキップ
4. **エディション/プロダクトキー** - Windows 11の各エディション対応
5. **Windows PE ステージ** - PE環境での動作設定
6. **ディスク構成** - パーティション自動作成（GPT/MBR）
7. **コンピューター設定** - ホスト名、ドメイン/ワークグループ
8. **ユーザーアカウント** - 複数アカウントの一括作成
9. **エクスプローラー調整** - 表示設定、ナビゲーションペイン
10. **スタート/タスクバー** - 配置、検索、ウィジェット設定
11. **システム調整** - UAC、Windows Defender、テレメトリ等

### 拡張設定（項目12-23）- 2024年8月24日実装完了
12. **視覚効果** - パフォーマンス優先/品質優先の切り替え
13. **デスクトップ設定** - アイコン表示、壁紙、配色
14. **仮想マシンサポート** - Hyper-V、WSL、Sandbox等
15. **Wi-Fi設定** - SSID、パスワード、自動接続
16. **Express Settings** - プライバシー設定の一括制御
17. **ロックキー設定** - NumLock、CapsLock、ScrollLock
18. **固定キー** - アクセシビリティ機能
19. **個人用設定** - テーマ、アクセントカラー、サウンド
20. **不要なアプリの削除** - プリインストールアプリの自動削除
21. **カスタムスクリプト** - 独自のPowerShell/バッチ実行
22. **WDAC設定** - Windows Defender Application Control
23. **その他のコンポーネント** - .NET、IIS、各種Windows機能

## 🏗️ システム構成

```
Windows 11 無人応答ファイル生成システム
├── WebUI（フロントエンド）
│   ├── React/Next.js
│   ├── TypeScript
│   └── Tailwind CSS
├── バックエンド
│   ├── FastAPI (Python)
│   ├── 42体のSubAgent
│   └── Context7エンジン
└── 出力
    ├── autounattend.xml
    └── configuration_log.txt（日本語）
```

## 📊 実装統計

- **総コマンド数**: 53個以上のFirstLogonCommands
- **レジストリ設定**: 26個以上
- **DISM機能**: 10個以上のWindows機能
- **PowerShellスクリプト**: 15個以上の自動化処理

## 🔧 主な技術仕様

- **XML名前空間**: `urn:schemas-microsoft-com:unattend`
- **文字エンコーディング**: UTF-8（XMLファイル）、UTF-16LE（パスワード）
- **対応Windowsバージョン**: Windows 11 21H2以降
- **APIプロトコル**: REST API (JSON)

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 📞 サポート

- GitHub Issues: [問題報告](https://github.com/your-org/repo/issues)
- ドキュメント: [オンラインドキュメント](./README.md)

## 🎉 更新履歴

### v2.0.0 (2024-08-24)
- ✅ 全23項目の設定に完全対応
- ✅ 項目12-23の新規実装完了
- ✅ FirstLogonCommandsによる高度な設定制御
- ✅ 日本語ログ生成機能の追加

### v1.0.0 (2024-08-01)
- 初回リリース
- 基本11項目の設定対応
- WebUIの実装

---

*最終更新: 2024年8月24日*