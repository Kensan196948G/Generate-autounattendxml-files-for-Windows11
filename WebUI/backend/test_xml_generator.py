#!/usr/bin/env python3
"""
XML生成器のテスト用スクリプト
"""

from xml_generator import UnattendXMLGenerator

# テスト設定
config = {
    "language": "ja-JP",
    "architecture": "amd64",
    "skip_network": True,
    "skip_privacy": True,
    "bypass_microsoft_account": True,
    "windows_edition": "Windows 11 Pro",
    "timezone": "Tokyo Standard Time",
    "enable_autologin": False,
    "user_accounts": [],
    "first_logon_commands": [],
}

# XML生成器をテスト
generator = UnattendXMLGenerator()
try:
    xml_content = generator.generate(config)
    print("XML生成成功!")
    print("="*50)
    print(xml_content[:500] + "..." if len(xml_content) > 500 else xml_content)
    print("="*50)
    
    # バリデーションテスト
    validation = generator.validate(xml_content)
    print(f"バリデーション結果: {validation}")
    
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()