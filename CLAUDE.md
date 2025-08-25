# Windows 11 Sysprep応答ファイル自動生成システム

## プロジェクト概要

このプロジェクトは、Windows 11のSysprep実行時に使用する応答ファイル（unattend.xml）を自動生成するシステムです。企業環境でのPCキッティング作業を自動化し、以下の設定を含む包括的なセットアップを実現します。

### 主要機能

1. **ユーザーアカウント管理**
   - 複数の管理者アカウント作成
   - デフォルトadministratorアカウントの無効化
   - ドメインユーザー設定

2. **システム設定**
   - ホスト名の自動設定
   - Bluetooth無効化
   - IPv6無効化
   - Windows Firewall無効化
   - 音源ミュート設定

3. **ネットワーク設定**
   - グループポリシー設定
   - 安全でないゲストログオンの有効化
   - ネットワークアイコン表示

4. **アプリケーション設定**
   - .NET Framework 3.5の有効化
   - Office初回起動設定
   - 既定のプログラム設定（メール、ブラウザ、PDF）
   - セキュリティソフトの設定確認

## システムアーキテクチャ

### コア技術スタック
- **言語**: Python 3.10+
- **XMLライブラリ**: lxml（高性能XML処理）
- **設定管理**: YAML/JSON
- **テストフレームワーク**: pytest
- **バリデーション**: XML Schema (XSD)

### モジュール構成

```
src/
├── core/              # コアエンジン
│   ├── xml_generator.py
│   └── validator.py
├── modules/           # 機能モジュール
│   ├── user_management.py
│   ├── network_config.py
│   ├── system_settings.py
│   └── application_config.py
├── templates/         # XMLテンプレート
├── schemas/          # XSDスキーマ
└── utils/            # ユーティリティ
```

## 開発方針

### SubAgent機能（30体以上）の活用

1. **ユーザー管理エージェント群**
   - UserCreationAgent
   - UserPermissionAgent
   - DomainJoinAgent
   - GroupPolicyAgent

2. **システム設定エージェント群**
   - NetworkConfigAgent
   - FirewallConfigAgent
   - BluetoothConfigAgent
   - AudioConfigAgent

3. **アプリケーション設定エージェント群**
   - OfficeConfigAgent
   - DefaultAppAgent
   - SecuritySoftwareAgent

4. **検証エージェント群**
   - XMLValidationAgent
   - SchemaValidationAgent
   - DependencyCheckAgent

### Claude-flow機能の活用

並列処理と高度な制御フローを実装：

```python
# 並列処理の例
parallel_tasks = [
    create_users(),
    configure_network(),
    setup_applications(),
    validate_settings()
]
results = await asyncio.gather(*parallel_tasks)
```

## XML生成仕様

### 主要なXMLパス（Windows System Image Manager準拠）

1. **specialize** パス
   - コンピューター名設定
   - ドメイン参加設定

2. **oobeSystem** パス
   - ユーザーアカウント作成
   - 初期設定のスキップ

3. **auditSystem** パス
   - 監査モード設定

4. **offlineServicing** パス
   - オフライン更新設定

## セキュリティ考慮事項

1. **パスワード管理**
   - パスワードの暗号化保存
   - 環境変数からの読み込み
   - XMLファイルへの平文パスワード非推奨

2. **ファイルアクセス制御**
   - 生成されたXMLファイルの適切な権限設定
   - ログファイルの機密情報マスキング

3. **監査ログ**
   - すべての設定変更の記録
   - タイムスタンプ付きログ

## 使用方法

### 基本的な使用例

```bash
# 設定ファイルからXML生成
python generate_unattend.py --config config.yaml --output unattend.xml

# インタラクティブモード
python generate_unattend.py --interactive

# バリデーションのみ
python generate_unattend.py --validate existing_unattend.xml
```

### 設定ファイル形式（YAML）

```yaml
system:
  hostname: "WIN11-PC001"
  timezone: "Tokyo Standard Time"
  
users:
  - name: "mirai-user"
    groups: ["Administrators"]
    password: "${MIRAI_PASSWORD}"
  - name: "l-admin"
    groups: ["Administrators"]
    password: "${LADMIN_PASSWORD}"
    
network:
  disable_ipv6: true
  disable_firewall: true
  disable_bluetooth: true
  
applications:
  dotnet_35: true
  default_browser: "Edge"
  default_mail: "Outlook"
  default_pdf: "Adobe Acrobat Reader DC"
```

## テスト戦略

1. **単体テスト**
   - 各モジュールの独立したテスト
   - モックを使用した外部依存の分離

2. **統合テスト**
   - XML生成の全体フロー
   - スキーマ検証

3. **E2Eテスト**
   - 実際のWindows環境での動作確認
   - Sysprep実行シミュレーション

## 開発ロードマップ

### フェーズ1: 基盤構築
- [x] プロジェクト構造設計
- [ ] コアモジュール実装
- [ ] 基本的なXML生成機能

### フェーズ2: 機能実装
- [ ] ユーザー管理機能
- [ ] ネットワーク設定機能
- [ ] アプリケーション設定機能

### フェーズ3: 高度な機能
- [ ] SubAgent統合
- [ ] Claude-flow並列処理
- [ ] GUI/Webインターフェース

### フェーズ4: テストと最適化
- [ ] 包括的なテストスイート
- [ ] パフォーマンス最適化
- [ ] ドキュメント整備

## コントリビューション

このプロジェクトへの貢献を歓迎します。以下のガイドラインに従ってください：

1. コードスタイルは`black`フォーマッターに準拠
2. すべての新機能にはテストを追加
3. ドキュメントの更新を忘れずに

## ライセンス

MIT License

## サポート

問題や質問がある場合は、GitHubのIssueを作成してください。

---

*このドキュメントは継続的に更新されます。最新の情報はGitHubリポジトリを確認してください。*