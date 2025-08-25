"""
XML生成テストスクリプト
設定が正しくXMLに反映されるかテスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_xml_generator import EnhancedXMLGenerator
from config_transformer import transform_frontend_config

# テスト設定（フロントエンドの形式を模倣）
test_config = {
    "regionLanguage": {
        "displayLanguage": "ja-JP",
        "languagePriority": ["ja-JP"],
        "keyboardLayouts": [{"language": "ja-JP", "layout": "0411:00000411"}],
        "country": "Japan",
        "manualSelection": False
    },
    "architecture": "amd64",
    "windowsEdition": {
        "useGenericKey": True,
        "edition": "Pro",
        "productKey": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
        "manualKeyEntry": False,
        "useBiosKey": False,
        "imageSelection": "key"
    },
    "userAccounts": {
        "accounts": [{
            "name": "testuser",
            "displayName": "Test User",
            "password": "TestPass123!",
            "group": "Administrators"
        }]
    },
    "wifiSettings": {
        "setup_mode": "configure",
        "profiles": [{
            "ssid": "TestNetwork",
            "auth_type": "WPA2PSK",
            "password": "TestWiFiPassword123",
            "connect_automatically": True,
            "connect_even_if_hidden": False,
            "priority": 1
        }]
    }
}

print("=" * 70)
print("XML生成テスト開始")
print("=" * 70)

# 設定を変換
print("\n1. フロントエンド設定を変換中...")
transformed = transform_frontend_config(test_config)

print("\n変換後の設定:")
import json
print(json.dumps(transformed, indent=2, ensure_ascii=False))

# デフォルト設定と結合
final_config = {
    "language": "ja-JP",
    "architecture": "amd64",
    "skip_network": False,
    "skip_privacy": True,
    "bypass_microsoft_account": True,
    "bypass_win11_requirements": True,
    "windows_edition": "Windows 11 Pro",
    "product_key": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
    "timezone": "Tokyo Standard Time",
    "enable_autologin": False,
    "local_accounts": [{
        "name": "mirai-user",
        "password": "mirai",
        "description": "Default administrator user",
        "display_name": "Mirai User",
        "group": "Administrators"
    }],
    **transformed
}

print("\n最終設定:")
print(json.dumps(final_config, indent=2, ensure_ascii=False))

# XML生成
print("\n2. XML生成中...")
generator = EnhancedXMLGenerator()
xml_content = generator.generate_complete_xml(final_config)

# 結果を保存
output_file = Path("test_output.xml")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"\n3. XMLを保存しました: {output_file}")

# XMLの一部を表示
print("\n生成されたXMLの抜粋:")
lines = xml_content.split('\n')
for i, line in enumerate(lines[:50]):  # 最初の50行を表示
    print(f"{i+1:3}: {line}")

# 重要な要素が含まれているかチェック
print("\n4. 重要な要素のチェック:")
checks = [
    ("Product Key", "<Key>" in xml_content or "<ProductKey>" in xml_content),
    ("Wi-Fi SSID", "TestNetwork" in xml_content or test_config["wifiSettings"]["profiles"][0]["ssid"] in xml_content),
    ("Wi-Fi Password", "TestWiFiPassword" in xml_content or test_config["wifiSettings"]["profiles"][0]["password"] in xml_content),
    ("User Account", "testuser" in xml_content),
    ("User Password (encoded)", "<Password>" in xml_content and "<Value>" in xml_content),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"  {status} {check_name}")

print("\n" + "=" * 70)
print("テスト完了")
print("=" * 70)