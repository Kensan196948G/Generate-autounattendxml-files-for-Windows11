# API仕様書

## 📡 API概要

Windows 11 無人応答ファイル生成システムのREST API仕様書です。全23項目の設定に対応したエンドポイントを提供します。

### 基本情報
- **ベースURL**: `http://localhost:8081`
- **プロトコル**: HTTP/1.1
- **データ形式**: JSON
- **文字エンコーディング**: UTF-8
- **認証**: なし（ローカル使用前提）

### Swagger UI
- **URL**: `http://localhost:8081/api/docs`
- **説明**: 対話的なAPI仕様書とテスト環境

---

## 🔌 エンドポイント一覧

### 1. XML生成 - メインエンドポイント

#### `POST /api/generate-unattend`

全23項目の設定を受け取り、autounattend.xmlと日本語ログを生成します。

**リクエスト**
```http
POST /api/generate-unattend HTTP/1.1
Content-Type: application/json

{
  "regionLanguage": { ... },
  "architecture": "amd64",
  "setupBehavior": { ... },
  // ... 全23項目の設定
}
```

**レスポンス（成功）**
```http
HTTP/1.1 200 OK
Content-Type: application/xml
Content-Disposition: attachment; filename="autounattend.xml"

<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <!-- XML content -->
</unattend>
```

**レスポンス（エラー）**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "Invalid configuration",
  "details": "Product key is invalid",
  "timestamp": "2024-08-24T12:00:00Z"
}
```

---

### 2. ログ付きXML生成

#### `POST /api/generate-with-log`

XMLファイルと日本語ログファイルをZIP形式で返します。

**リクエスト**
```json
{
  // 全23項目の設定（generate-unattendと同じ）
}
```

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename="windows11_config.zip"

[Binary ZIP data containing:]
- unattend.xml
- configuration_log.txt
```

---

### 3. システムステータス

#### `GET /api/status`

システムの稼働状況を確認します。

**レスポンス**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "agents": {
    "total": 42,
    "active": 42,
    "idle": 0
  },
  "context7": {
    "status": "enabled",
    "performance": "optimal"
  },
  "timestamp": "2024-08-24T12:00:00Z"
}
```

---

### 4. エージェント一覧

#### `GET /api/agents`

利用可能な42体のSubAgent情報を取得します。

**レスポンス**
```json
{
  "agents": [
    {
      "id": 1,
      "name": "UserCreationAgent",
      "category": "user_management",
      "status": "active",
      "description": "ユーザーアカウント作成を担当"
    },
    {
      "id": 2,
      "name": "WiFiConfigAgent",
      "category": "network",
      "status": "active",
      "description": "Wi-Fi設定を担当"
    },
    // ... 全42体のエージェント情報
  ],
  "total": 42,
  "categories": {
    "user_management": 8,
    "network": 6,
    "system": 10,
    "application": 6,
    "features": 8,
    "ui_ux": 4
  }
}
```

---

### 5. プリセット設定

#### `GET /api/presets`

利用可能なプリセット設定を取得します。

**レスポンス**
```json
{
  "presets": [
    {
      "id": "enterprise",
      "name": "エンタープライズ",
      "description": "企業環境向けの推奨設定",
      "settings": {
        "disableTelemetry": true,
        "disableConsumerFeatures": true,
        // ... プリセット設定
      }
    },
    {
      "id": "development",
      "name": "開発環境",
      "description": "開発者向けの設定",
      "settings": {
        "enableHyperV": true,
        "enableWSL": true,
        // ... プリセット設定
      }
    },
    {
      "id": "minimal",
      "name": "最小構成",
      "description": "最小限の設定",
      "settings": {
        // ... プリセット設定
      }
    }
  ]
}
```

---

### 6. ヘルスチェック

#### `GET /api/health`

簡易的なヘルスチェックエンドポイント。

**レスポンス**
```json
{
  "status": "ok",
  "timestamp": "2024-08-24T12:00:00Z"
}
```

---

## 📝 リクエストボディ詳細

### 完全な設定オブジェクト構造

```typescript
interface ComprehensiveConfig {
  // 1. 地域と言語の設定
  regionLanguage: {
    displayLanguage: string;      // 例: "ja-JP"
    inputLocale: string;          // 例: "0411:00000411"
    systemLocale: string;         // 例: "ja-JP"
    userLocale: string;           // 例: "ja-JP"
    uiLanguage: string;           // 例: "ja-JP"
    uiLanguageFallback: string;   // 例: "en-US"
    timezone: string;             // 例: "Tokyo Standard Time"
    geoLocation: string;          // 例: "122"
  };

  // 2. プロセッサー・アーキテクチャ
  architecture: 'amd64' | 'x86' | 'arm64';

  // 3. セットアップの挙動
  setupBehavior: {
    skipMachineOOBE: boolean;
    skipUserOOBE: boolean;
    hideEULAPage: boolean;
    hideOEMRegistration: boolean;
    hideOnlineAccountScreens: boolean;
    hideWirelessSetup: boolean;
    protectYourPC: number;        // 1-3
    networkLocation: string;      // "Home" | "Work" | "Public"
    skipDomainJoin: boolean;
  };

  // 4. エディション/プロダクトキー
  windowsEdition: {
    edition: string;              // "Home" | "Pro" | "Enterprise"
    productKey: string;
    acceptEula: boolean;
    installToAvailable: boolean;
    willShowUI: string;           // "Never" | "OnError" | "Always"
  };

  // 5. Windows PE ステージ
  windowsPE: {
    disableCommandPrompt: boolean;
    disableFirewall: boolean;
    enableNetwork: boolean;
    enableRemoteAssistance: boolean;
    pageFile: string;             // "Auto" | カスタムサイズ
    scratchSpace: number;         // MB単位
  };

  // 6. ディスク構成
  diskConfig: {
    wipeDisk: boolean;
    diskId: number;
    partitionStyle: 'GPT' | 'MBR';
    partitions: Array<{
      type: string;               // "EFI" | "MSR" | "Primary" | "Recovery"
      size: number | 'remaining';
      letter?: string;
    }>;
  };

  // 7. コンピューター設定
  computerSettings: {
    computerName: string;         // "*"で自動生成
    organization: string;
    owner: string;
    joinDomain: boolean;
    domain: string;
    domainOU: string;
    workgroup: string;
  };

  // 8. ユーザーアカウント
  userAccounts: {
    accounts: Array<{
      name: string;
      password: string;
      displayName: string;
      description: string;
      group: string;              // "Administrators" | "Users"
      autoLogon: boolean;
      passwordNeverExpires: boolean;
    }>;
    autoLogonCount: number;
    disableAdminAccount: boolean;
    enableGuestAccount: boolean;
  };

  // 9-23: その他の設定項目...
  // （詳細は設定項目一覧を参照）
}
```

---

## 🔄 エラーコード

### HTTP ステータスコード

| コード | 説明 | 対処法 |
|--------|------|--------|
| 200 | 成功 | - |
| 400 | 不正なリクエスト | リクエストボディを確認 |
| 404 | エンドポイントが見つからない | URLを確認 |
| 422 | バリデーションエラー | 設定値を確認 |
| 500 | サーバーエラー | ログを確認 |

### アプリケーションエラーコード

```json
{
  "error_code": "ERR_INVALID_PRODUCT_KEY",
  "message": "指定されたプロダクトキーが無効です",
  "details": {
    "field": "windowsEdition.productKey",
    "value": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
    "expected": "有効なWindows 11プロダクトキー"
  }
}
```

---

## 🔐 セキュリティ

### CORS設定

```python
allowed_origins = [
    "http://localhost:3050",
    "http://localhost:3000",
    "http://192.168.3.92:3050",
    "http://192.168.3.92:8084"
]
```

### パスワード処理
- パスワードはBase64エンコード（UTF-16LE）で送信
- XMLファイル内では`PasswordValue`要素として保存
- ログファイルではマスキング処理

---

## 📊 レート制限

現在のバージョンではレート制限は実装されていません。
ローカル環境での使用を前提としています。

本番環境では以下の制限を推奨：
- 1分あたり10リクエスト
- 1時間あたり100リクエスト

---

## 🧪 テスト用cURLコマンド

### 基本的なXML生成
```bash
curl -X POST http://localhost:8081/api/generate-unattend \
  -H "Content-Type: application/json" \
  -d @config.json \
  -o unattend.xml
```

### ステータス確認
```bash
curl http://localhost:8081/api/status
```

### エージェント一覧取得
```bash
curl http://localhost:8081/api/agents | jq .
```

---

## 📝 変更履歴

### v2.0.0 (2024-08-24)
- 全23項目の設定に対応
- FirstLogonCommands実装（53個以上）
- 日本語ログ生成機能追加

### v1.0.0 (2024-08-01)
- 初回リリース
- 基本11項目の設定対応

---

*最終更新: 2024年8月24日*