"""
設定形式変換モジュール
フロントエンドの設定形式をバックエンドのXML生成器が理解できる形式に変換
"""

import base64
from typing import Dict, Any, List

def encode_password(password: str) -> str:
    """
    パスワードをWindows unattend.xml用にBase64エンコード
    UTF-16LEでエンコードしてBase64化
    """
    # Windows用にUTF-16LEでエンコード
    password_bytes = password.encode('utf-16le')
    # Base64エンコード
    encoded = base64.b64encode(password_bytes).decode('ascii')
    # 末尾に"Password"を追加（Windows要件）
    return encoded + "Password"

def transform_frontend_config(frontend_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    フロントエンドの設定形式をバックエンドの形式に変換
    """
    # 基本設定
    backend_config = {
        "language": frontend_config.get("regionLanguage", {}).get("displayLanguage", "ja-JP"),
        "architecture": frontend_config.get("architecture", "amd64"),
        "timezone": "Tokyo Standard Time",
        "bypass_microsoft_account": True,
        "skip_network": False,  # Wi-Fi設定があるため
        "skip_privacy": frontend_config.get("expressSettings") == "all_disabled",
    }
    
    # Windowsエディション設定
    windows_edition = frontend_config.get("windowsEdition", {})
    edition_map = {
        "Home": "Windows 11 Home",
        "Pro": "Windows 11 Pro",
        "Pro N": "Windows 11 Pro N",
        "Education": "Windows 11 Education",
        "Enterprise": "Windows 11 Enterprise",
    }
    backend_config["windows_edition"] = edition_map.get(
        windows_edition.get("edition", "Pro"),
        "Windows 11 Pro"
    )
    backend_config["product_key"] = windows_edition.get("productKey", "")
    
    # ユーザーアカウント設定
    user_accounts = frontend_config.get("userAccounts", {}).get("accounts", [])
    if user_accounts:
        backend_config["local_accounts"] = []
        for account in user_accounts:
            backend_config["local_accounts"].append({
                "name": account.get("name", "user"),
                "password": account.get("password", "password"),
                "display_name": account.get("displayName", account.get("name", "User")),
                "description": f"{account.get('group', 'Users')} account",
                "group": account.get("group", "Users")
            })
    else:
        # デフォルトユーザー
        backend_config["local_accounts"] = [{
            "name": "mirai-user",
            "password": "mirai",
            "display_name": "Mirai User",
            "description": "Default administrator user",
            "group": "Administrators"
        }]
    
    # コンピューター名設定
    computer_settings = frontend_config.get("computerSettings", {})
    if computer_settings.get("computerName") == "fixed" and computer_settings.get("fixedName"):
        backend_config["computer_name"] = computer_settings["fixedName"]
    
    # Wi-Fi設定
    wifi_settings = frontend_config.get("wifiSettings", {})
    if wifi_settings.get("setup_mode") == "configure" and wifi_settings.get("profiles"):
        # 最初のプロファイルをwifi_settingsとして設定
        first_profile = wifi_settings["profiles"][0]
        backend_config["wifi_settings"] = {
            "ssid": first_profile.get("ssid", ""),
            "password": first_profile.get("password", ""),
            "auth_type": first_profile.get("auth_type", "WPA2PSK"),
            "connect_automatically": first_profile.get("connect_automatically", True)
        }
        # skip_networkをFalseに設定
        backend_config["skip_network"] = False
    
    # Windows機能設定
    # .NET Framework 3.5
    system_tweaks = frontend_config.get("systemTweaks", {})
    if system_tweaks.get("features", {}).get("dotnet35"):
        backend_config["enable_dotnet35"] = True
    
    # Hyper-V
    if system_tweaks.get("features", {}).get("hyperv"):
        backend_config["enable_hyperv"] = True
    
    # WSL
    if system_tweaks.get("features", {}).get("wsl"):
        backend_config["enable_wsl"] = True
    
    # ディスク設定
    disk_config = frontend_config.get("diskConfig", {})
    backend_config["disk_config"] = {
        "mode": disk_config.get("mode", "auto"),
        "partition_layout": disk_config.get("partitionLayout", "GPT")
    }
    
    # デスクトップ設定
    desktop_settings = frontend_config.get("desktopSettings", {})
    if desktop_settings:
        backend_config["desktop_icons"] = desktop_settings.get("desktop_icons", {})
        backend_config["hide_edge_prompts"] = desktop_settings.get("hide_edge_prompts", True)
    
    # 不要なアプリの削除
    remove_apps = frontend_config.get("removeApps", [])
    if remove_apps:
        backend_config["remove_apps"] = remove_apps
    
    # カスタムスクリプト
    custom_scripts = frontend_config.get("customScripts", {})
    if custom_scripts.get("restartExplorer"):
        backend_config["restart_explorer"] = True
    
    # OOBEスキップ設定
    setup_behavior = frontend_config.get("setupBehavior", {})
    backend_config["bypass_win11_requirements"] = setup_behavior.get("bypassWin11Requirements", True)
    backend_config["allow_offline_install"] = setup_behavior.get("allowOfflineInstall", True)
    
    return backend_config