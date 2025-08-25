# Windows 11 Sysprep WebUI API仕様書

## API概要

- **ベースURL**: `http://[IP_ADDRESS]:8081/api`
- **プロトコル**: HTTP/HTTPS
- **データ形式**: JSON (リクエスト), XML/ZIP (レスポンス)
- **文字エンコーディング**: UTF-8

## 認証

現在のバージョンでは認証は実装されていません。将来的にJWT認証を追加予定。

## エンドポイント一覧

### 1. XML生成

#### `POST /api/generate-unattend`

unattend.xmlファイルを生成します。

**リクエスト**

```http
POST /api/generate-unattend
Content-Type: application/json
```

**リクエストボディ**

```json
{
  "windows_edition": "Pro",
  "language": "ja-JP",
  "timezone": "Tokyo Standard Time",
  "architecture": "amd64",
  "product_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
  "computer_name": "WIN11-PC",
  "local_accounts": [
    {
      "name": "admin",
      "password": "P@ssw0rd123!",
      "display_name": "Administrator",
      "description": "Local admin account",
      "group": "Administrators"
    }
  ],
  "wifi_settings": {
    "ssid": "MyWiFi",
    "password": "WiFiPassword",
    "auth_type": "WPA2PSK",
    "connect_automatically": true
  },
  "bypass_win11_requirements": true,
  "bypass_microsoft_account": true,
  "bypass_network_check": true,
  "skip_privacy": true,
  "enable_dotnet35": false,
  "enable_hyperv": false,
  "enable_wsl": false,
  "enable_sandbox": false,
  "desktop_icons": {
    "computer": true,
    "network": true,
    "recycle_bin": true,
    "user_files": false
  }
}
```

**レスポンス**

```http
HTTP/1.1 200 OK
Content-Type: application/xml
Content-Disposition: attachment; filename=autounattend.xml

<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  ...
</unattend>
```

**エラーレスポンス**

```json
{
  "detail": "エラーメッセージ"
}
```

### 2. XML + ログ生成（ZIP）

#### `POST /api/generate-with-log`

unattend.xmlと設定ログをZIPファイルとして生成します。

**リクエスト**

```http
POST /api/generate-with-log
Content-Type: application/json
```

**リクエストボディ**

generate-unattendと同じ形式

**レスポンス**

```http
HTTP/1.1 200 OK
Content-Type: application/zip
Content-Disposition: attachment; filename=unattend_package.zip
X-Generator: Windows11-Unattend-Generator
X-Version: 2.0.0

[バイナリデータ]
```

**ZIPファイル内容**

- `autounattend.xml` - 無人応答ファイル
- `設定ログ.txt` - 日本語設定ログ

### 3. システム状態

#### `GET /api/status`

システムの現在の状態を取得します。

**リクエスト**

```http
GET /api/status
```

**レスポンス**

```json
{
  "status": "running",
  "version": "2.0.0",
  "backend_ip": "192.168.3.92",
  "timestamp": "2025-08-24T12:00:00.000000",
  "allowed_origins": [
    "http://192.168.3.92:3050",
    "http://localhost:3050"
  ]
}
```

### 4. ヘルスチェック

#### `GET /api/health`

詳細なシステムヘルス情報を取得します。

**リクエスト**

```http
GET /api/health
```

**レスポンス**

```json
{
  "status": "healthy",
  "system": {
    "platform": "Windows-11",
    "python_version": "3.10.11",
    "hostname": "DESKTOP-ABC123"
  },
  "metrics": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_usage_percent": 62.3
  },
  "services": {
    "xml_generator": "operational",
    "config_transformer": "operational",
    "log_generator": "operational"
  },
  "timestamp": "2025-08-24T12:00:00.000000"
}
```

## データモデル

### WindowsEdition

```typescript
type WindowsEdition = "Pro" | "Home" | "Enterprise" | "Education";
```

### LocalAccount

```typescript
interface LocalAccount {
  name: string;           // ユーザー名（必須）
  password: string;       // パスワード（必須、8文字以上）
  display_name?: string;  // 表示名
  description?: string;   // 説明
  group?: "Administrators" | "Users";  // グループ（デフォルト: Users）
}
```

### WiFiSettings

```typescript
interface WiFiSettings {
  ssid: string;          // ネットワーク名（必須）
  password: string;      // パスワード（必須）
  auth_type?: "WPA2PSK" | "WPA3SAE";  // 認証方式
  connect_automatically?: boolean;     // 自動接続
}
```

### DesktopIcons

```typescript
interface DesktopIcons {
  computer?: boolean;      // このPC
  network?: boolean;       // ネットワーク
  recycle_bin?: boolean;   // ごみ箱
  user_files?: boolean;    // ユーザーフォルダー
}
```

## エラーコード

| コード | 説明 | 対処法 |
|--------|------|--------|
| 400 | 不正なリクエスト | リクエストボディの形式を確認 |
| 422 | 検証エラー | 必須フィールドや値の形式を確認 |
| 500 | サーバーエラー | ログを確認し、管理者に連絡 |
| 503 | サービス利用不可 | しばらく待ってから再試行 |

## 制限事項

- **リクエストサイズ**: 最大10MB
- **タイムアウト**: 30秒
- **同時接続数**: 100
- **レート制限**: なし（将来実装予定）

## CORSポリシー

以下のオリジンからのアクセスを許可：

- `http://localhost:3050`
- `http://localhost:3000`
- `http://[LOCAL_IP]:3050`
- `http://[LOCAL_IP]:3000`
- `http://[LOCAL_IP]:8082`
- `http://[LOCAL_IP]:8083`

許可メソッド：
- GET
- POST
- OPTIONS

## サンプルコード

### JavaScript (Axios)

```javascript
import axios from 'axios';

const API_BASE = 'http://192.168.3.92:8081/api';

// XML生成
async function generateXML(config) {
  try {
    const response = await axios.post(
      `${API_BASE}/generate-unattend`,
      config,
      { responseType: 'blob' }
    );
    
    // ダウンロード処理
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'autounattend.xml';
    link.click();
  } catch (error) {
    console.error('Error:', error);
  }
}

// 使用例
const config = {
  windows_edition: 'Pro',
  language: 'ja-JP',
  local_accounts: [{
    name: 'admin',
    password: 'P@ssw0rd123!',
    group: 'Administrators'
  }]
};

generateXML(config);
```

### Python

```python
import requests
import json

API_BASE = 'http://192.168.3.92:8081/api'

def generate_xml(config):
    """XML生成"""
    response = requests.post(
        f'{API_BASE}/generate-unattend',
        json=config
    )
    
    if response.status_code == 200:
        with open('autounattend.xml', 'wb') as f:
            f.write(response.content)
        print('XML生成成功')
    else:
        print(f'エラー: {response.status_code}')

# 使用例
config = {
    'windows_edition': 'Pro',
    'language': 'ja-JP',
    'local_accounts': [{
        'name': 'admin',
        'password': 'P@ssw0rd123!',
        'group': 'Administrators'
    }]
}

generate_xml(config)
```

### cURL

```bash
# XML生成
curl -X POST http://192.168.3.92:8081/api/generate-unattend \
  -H "Content-Type: application/json" \
  -d '{
    "windows_edition": "Pro",
    "language": "ja-JP",
    "local_accounts": [{
      "name": "admin",
      "password": "P@ssw0rd123!",
      "group": "Administrators"
    }]
  }' \
  --output autounattend.xml

# XML + ログ生成（ZIP）
curl -X POST http://192.168.3.92:8081/api/generate-with-log \
  -H "Content-Type: application/json" \
  -d '{"windows_edition": "Pro"}' \
  --output unattend_package.zip
```

## 変更履歴

### v2.0.0 (2025-08-24)
- 初版リリース
- XML生成エンドポイント追加
- ログ生成機能追加
- ZIP形式でのダウンロード対応

---

*最終更新: 2025年8月24日*