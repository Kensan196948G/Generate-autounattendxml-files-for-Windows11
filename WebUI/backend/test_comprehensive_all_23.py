#!/usr/bin/env python3
"""
包括的な23項目すべての設定をテストするスクリプト
Items 12-22の新しい実装を含む完全なテスト
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

# 全23項目を含む包括的な設定
comprehensive_config = {
    # 1. 地域と言語の設定
    "regionLanguage": {
        "displayLanguage": "ja-JP",
        "inputLocale": "0411:00000411",
        "systemLocale": "ja-JP",
        "userLocale": "ja-JP",
        "uiLanguage": "ja-JP",
        "uiLanguageFallback": "en-US",
        "timezone": "Tokyo Standard Time",
        "geoLocation": "122"
    },
    
    # 2. プロセッサー・アーキテクチャ
    "architecture": "amd64",
    
    # 3. セットアップの挙動
    "setupBehavior": {
        "skipMachineOOBE": True,
        "skipUserOOBE": True,
        "hideEULAPage": True,
        "hideOEMRegistration": True,
        "hideOnlineAccountScreens": True,
        "hideWirelessSetup": False,
        "protectYourPC": 3,
        "networkLocation": "Work",
        "skipDomainJoin": True
    },
    
    # 4. エディション/プロダクトキー
    "windowsEdition": {
        "edition": "Pro",
        "productKey": "VK7JG-NPHTM-C97JM-9MPGT-3V66T",
        "acceptEula": True,
        "installToAvailable": True,
        "willShowUI": "OnError"
    },
    
    # 5. Windows PE ステージ
    "windowsPE": {
        "disableCommandPrompt": False,
        "disableFirewall": True,
        "enableNetwork": True,
        "enableRemoteAssistance": False,
        "pageFile": "Auto",
        "scratchSpace": 512
    },
    
    # 6. ディスク構成
    "diskConfig": {
        "wipeDisk": True,
        "diskId": 0,
        "partitionStyle": "GPT",
        "partitions": [
            {"type": "EFI", "size": 100},
            {"type": "MSR", "size": 16},
            {"type": "Primary", "size": "remaining", "letter": "C"},
            {"type": "Recovery", "size": 500}
        ]
    },
    
    # 7. コンピューター設定
    "computerSettings": {
        "computerName": "TEST-PC-001",
        "organization": "Test Organization",
        "owner": "Test Owner",
        "joinDomain": False,
        "domain": "",
        "domainOU": "",
        "workgroup": "WORKGROUP"
    },
    
    # 8. ユーザーアカウント
    "userAccounts": {
        "accounts": [
            {
                "name": "testadmin",
                "password": "TestP@ssw0rd123!",
                "displayName": "Test Administrator",
                "description": "Test admin account",
                "group": "Administrators",
                "autoLogon": False,
                "passwordNeverExpires": True
            },
            {
                "name": "testuser",
                "password": "UserP@ssw0rd456!",
                "displayName": "Test User",
                "description": "Standard test user",
                "group": "Users",
                "autoLogon": False,
                "passwordNeverExpires": False
            }
        ],
        "autoLogonCount": 0,
        "disableAdminAccount": True,
        "enableGuestAccount": False
    },
    
    # 9. エクスプローラー調整
    "explorerSettings": {
        "showHiddenFiles": True,
        "showFileExtensions": True,
        "showProtectedOSFiles": False,
        "disableThumbnailCache": False,
        "disableThumbsDB": False,
        "launchTo": "ThisPC",
        "navPaneExpand": True,
        "navPaneShowAll": True
    },
    
    # 10. スタート/タスクバー
    "startTaskbar": {
        "taskbarAlignment": "Left",
        "taskbarSearch": "Icon",
        "taskbarWidgets": False,
        "taskbarChat": False,
        "taskbarTaskView": True,
        "startMenuLayout": "Default",
        "showRecentlyAdded": False,
        "showMostUsed": False,
        "showSuggestions": False
    },
    
    # 11. システム調整
    "systemTweaks": {
        "disableUAC": False,
        "disableSmartScreen": False,
        "disableDefender": False,
        "disableFirewall": True,
        "disableUpdates": False,
        "disableTelemetry": True,
        "disableCortana": True,
        "disableSearchWeb": True,
        "disableGameBar": True,
        "fastStartup": False,
        "hibernation": False
    },
    
    # 12. 視覚効果 (新規実装)
    "visualEffects": {
        "performanceMode": "BestPerformance",
        "transparency": False,
        "animations": False,
        "shadows": False,
        "smoothEdges": False,
        "fontSmoothing": "Standard",
        "wallpaperQuality": "Fill"
    },
    
    # 13. デスクトップ設定 (新規実装)
    "desktopSettings": {
        "showComputer": True,
        "showUserFiles": True,
        "showNetwork": True,
        "showRecycleBin": True,
        "showControlPanel": True,
        "iconSize": "Large",
        "iconSpacing": "Wide",
        "autoArrange": False,
        "alignToGrid": True,
        "wallpaper": "C:\\Windows\\Web\\Wallpaper\\Windows\\img0.jpg",
        "solidColor": "0078D4"
    },
    
    # 14. 仮想マシンサポート
    "vmSupport": {
        "enableHyperV": True,
        "enableWSL": True,
        "enableWSL2": True,
        "enableSandbox": True,
        "enableContainers": True,
        "enableVirtualization": True,
        "nestedVirtualization": True
    },
    
    # 15. Wi-Fi設定
    "wifiSettings": {
        "setup_mode": "configure",
        "ssid": "TestNetwork2024",
        "password": "TestP@ssw0rd!",
        "authType": "WPA2PSK",
        "encryption": "AES",
        "connectAutomatically": True,
        "connectEvenNotBroadcasting": True
    },
    
    # 16. Express Settings (新規実装)
    "expressSettings": {
        "mode": "custom",
        "sendDiagnosticData": False,
        "improveInking": False,
        "tailoredExperiences": False,
        "advertisingId": False,
        "locationServices": False,
        "findMyDevice": False
    },
    
    # 17. ロックキー設定
    "lockKeys": {
        "numLock": True,
        "capsLock": False,
        "scrollLock": False
    },
    
    # 18. 固定キー (新規実装)
    "stickyKeys": {
        "enabled": False,
        "lockModifier": False,
        "turnOffOnTwoKeys": True,
        "feedback": False,
        "beep": False
    },
    
    # 19. 個人用設定 (新規実装)
    "personalization": {
        "theme": "Dark",
        "accentColor": "FF0078D4",
        "startColor": True,
        "taskbarColor": True,
        "titleBarColor": True,
        "lockScreenImage": "C:\\Windows\\Web\\Screen\\img100.jpg",
        "userPicture": "C:\\ProgramData\\Microsoft\\User Account Pictures\\user.png",
        "soundsScheme": ".None",
        "mouseCursorScheme": "Windows Black"
    },
    
    # 20. 不要なアプリの削除
    "removeApps": {
        "apps": [
            "Microsoft.BingNews",
            "Microsoft.BingWeather",
            "Microsoft.GetHelp",
            "Microsoft.Getstarted",
            "Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.People",
            "Microsoft.WindowsFeedbackHub",
            "Microsoft.YourPhone",
            "Microsoft.ZuneMusic",
            "Microsoft.ZuneVideo",
            "Microsoft.Xbox.TCUI",
            "Microsoft.XboxApp",
            "Microsoft.XboxGameOverlay"
        ]
    },
    
    # 21. カスタムスクリプト (新規実装)
    "customScripts": {
        "firstLogon": [
            {
                "order": 1,
                "command": "powershell -Command \"Write-Host 'Test Script 1 Executed'\"",
                "description": "Test PowerShell script",
                "requiresRestart": False
            },
            {
                "order": 2,
                "command": "cmd /c echo Test Script 2 > C:\\test_log.txt",
                "description": "Test CMD script",
                "requiresRestart": False
            }
        ],
        "setupScripts": [
            {
                "order": 1,
                "path": "C:\\Setup\\configure.ps1",
                "description": "Configuration script"
            }
        ]
    },
    
    # 22. WDAC設定 (新規実装)
    "wdac": {
        "enabled": True,
        "policyMode": "Enforced",
        "allowMicrosoftApps": True,
        "allowStoreApps": True,
        "allowReputableApps": False,
        "customRules": [
            "Allow C:\\CustomApps\\*",
            "Block C:\\UnsafeApps\\*"
        ]
    },
    
    # 23. その他のコンポーネント
    "additionalComponents": {
        "dotnet35": True,
        "dotnet48": True,
        "iis": True,
        "telnetClient": True,
        "tftpClient": False,
        "smb1": False,
        "powershell2": False,
        "directPlay": True,
        "printToPDF": True,
        "xpsViewer": True,
        "mediaFeatures": True,
        "workFolders": False
    }
}

def test_comprehensive_generation():
    """全23項目でXML生成をテスト"""
    print("=" * 80)
    print("包括的な23項目テスト - 全設定項目を含むXML生成")
    print("=" * 80)
    print(f"テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # APIエンドポイントに送信
    url = "http://localhost:8081/api/generate-unattend"
    
    print("送信する設定項目:")
    for i, key in enumerate(comprehensive_config.keys(), 1):
        status = "✅ 設定済み"
        if key in ["visualEffects", "desktopSettings", "expressSettings", 
                   "stickyKeys", "personalization", "customScripts", "wdac"]:
            status += " (新規実装)"
        print(f"  {i:2}. {key}: {status}")
    
    print("\nAPIリクエスト送信中...")
    
    try:
        response = requests.post(
            url,
            json=comprehensive_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ XML生成成功!")
            
            # レスポンスをファイルに保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # ZIPファイルとして保存
            zip_filename = f"test_comprehensive_all23_{timestamp}.zip"
            with open(zip_filename, "wb") as f:
                f.write(response.content)
            print(f"📦 ZIPファイル保存: {zip_filename}")
            
            # ZIPファイルから内容を抽出して確認
            import zipfile
            import os
            
            extract_dir = f"test_output_{timestamp}"
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # XMLファイルを解析
            xml_path = os.path.join(extract_dir, "unattend.xml")
            if os.path.exists(xml_path):
                print(f"\n📄 XMLファイル解析: {xml_path}")
                
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                # FirstLogonCommandsを探す
                print("\n🔍 FirstLogonCommands検証:")
                namespaces = {
                    '': 'urn:schemas-microsoft-com:unattend',
                    'wcm': 'http://schemas.microsoft.com/WMIConfig/2002/State'
                }
                
                commands = root.findall(".//FirstLogonCommands/SynchronousCommand", namespaces)
                if commands:
                    print(f"  ✅ {len(commands)}個のコマンドが見つかりました")
                    
                    # コマンドの種類を分類
                    reg_commands = 0
                    dism_commands = 0
                    powershell_commands = 0
                    other_commands = 0
                    
                    for cmd in commands:
                        cmd_line = cmd.find("CommandLine", namespaces)
                        if cmd_line is not None and cmd_line.text:
                            if "reg add" in cmd_line.text.lower():
                                reg_commands += 1
                            elif "dism" in cmd_line.text.lower():
                                dism_commands += 1
                            elif "powershell" in cmd_line.text.lower():
                                powershell_commands += 1
                            else:
                                other_commands += 1
                    
                    print(f"    - レジストリコマンド: {reg_commands}個")
                    print(f"    - DISMコマンド: {dism_commands}個")
                    print(f"    - PowerShellコマンド: {powershell_commands}個")
                    print(f"    - その他のコマンド: {other_commands}個")
                    
                    # 最初の5個のコマンドを表示
                    print("\n  最初の5個のコマンド例:")
                    for i, cmd in enumerate(commands[:5], 1):
                        cmd_line = cmd.find("CommandLine", namespaces)
                        if cmd_line is not None and cmd_line.text:
                            cmd_text = cmd_line.text[:100] + "..." if len(cmd_line.text) > 100 else cmd_line.text
                            print(f"    {i}. {cmd_text}")
                else:
                    print("  ⚠️ FirstLogonCommandsが見つかりません")
                
                # 各設定セクションの確認
                print("\n📋 主要セクション確認:")
                sections = [
                    ("specialize", "ComputerName", "コンピューター名"),
                    ("oobeSystem", "UserAccounts", "ユーザーアカウント"),
                    ("windowsPE", "SetupUILanguage", "言語設定"),
                ]
                
                for pass_name, element, description in sections:
                    found = root.find(f".//*[@pass='{pass_name}']//{element}", namespaces)
                    if found is not None:
                        print(f"  ✅ {description} ({pass_name})")
                    else:
                        print(f"  ❌ {description} ({pass_name})")
                
            # ログファイルも確認
            log_path = os.path.join(extract_dir, "configuration_log.txt")
            if os.path.exists(log_path):
                print(f"\n📝 ログファイル確認: {log_path}")
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"  ログ行数: {len(lines)}行")
                    
                    # 新規実装項目の確認
                    new_items = ["視覚効果", "デスクトップ設定", "Express Settings", 
                                "固定キー", "個人用設定", "カスタムスクリプト", "WDAC"]
                    print("\n  新規実装項目の記載確認:")
                    for item in new_items:
                        found = any(item in line for line in lines)
                        status = "✅" if found else "❌"
                        print(f"    {status} {item}")
            
        else:
            print(f"❌ エラー: ステータスコード {response.status_code}")
            print(f"レスポンス: {response.text}")
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == "__main__":
    test_comprehensive_generation()