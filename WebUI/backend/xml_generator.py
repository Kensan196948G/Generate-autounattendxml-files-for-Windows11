"""
Windows 11 無人応答ファイル（unattend.xml）生成モジュール
Schneegans.de 完全互換実装 + Context7 + SubAgent統合
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Optional, Any
import base64
import hashlib
from datetime import datetime

class UnattendXMLGenerator:
    """
    Windows 11 unattend.xml生成クラス
    Schneegans.de互換 + 日本語対応
    """
    
    def __init__(self):
        self.namespaces = {
            'unattend': 'urn:schemas-microsoft-com:unattend',
            'wcm': 'http://schemas.microsoft.com/WMIConfig/2002/State',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # 地域/言語設定のマッピング
        self.language_mapping = {
            'ja-JP': {
                'name': '日本語',
                'locale': '0411:00000411',
                'timezone': 'Tokyo Standard Time',
                'geo_location': '122'  # Japan
            },
            'en-US': {
                'name': 'English (United States)',
                'locale': '0409:00000409',
                'timezone': 'Pacific Standard Time',
                'geo_location': '244'  # USA
            }
        }
        
        # Windows 11エディション
        self.editions = {
            'Windows 11 Pro': 'Windows 11 Professional',
            'Windows 11 Home': 'Windows 11 Home',
            'Windows 11 Education': 'Windows 11 Education',
            'Windows 11 Enterprise': 'Windows 11 Enterprise'
        }
    
    def generate(self, config: Dict[str, Any]) -> str:
        """
        設定からunattend.xmlを生成
        
        Args:
            config: 設定ディクショナリ（Schneegans.de準拠）
        
        Returns:
            XML文字列
        """
        # ルート要素作成
        root = ET.Element('unattend')
        root.set('xmlns', 'urn:schemas-microsoft-com:unattend')
        
        # 各設定パスを生成
        self._add_windows_pe_settings(root, config)
        self._add_specialize_settings(root, config)
        self._add_oobe_settings(root, config)
        self._add_first_logon_settings(root, config)
        
        # 整形して返す
        return self._prettify_xml(root)
    
    def _add_windows_pe_settings(self, root: ET.Element, config: Dict):
        """windowsPE設定を追加"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'windowsPE')
        
        # アーキテクチャ設定
        arch = config.get('architecture', 'amd64')
        component = ET.SubElement(
            settings, 
            'component',
            name='Microsoft-Windows-International-Core-WinPE',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # 言語設定
        language = config.get('language', 'ja-JP')
        lang_info = self.language_mapping.get(language, self.language_mapping['ja-JP'])
        
        # SetupUILanguage
        setup_ui = ET.SubElement(component, 'SetupUILanguage')
        ET.SubElement(setup_ui, 'UILanguage').text = language
        
        # InputLocale
        ET.SubElement(component, 'InputLocale').text = lang_info['locale']
        ET.SubElement(component, 'SystemLocale').text = language
        ET.SubElement(component, 'UILanguage').text = language
        ET.SubElement(component, 'UserLocale').text = language
        
        # ディスク設定（必要に応じて）
        if config.get('partition_settings'):
            self._add_disk_configuration(settings, config, arch)
        
        # Windows セットアップ設定
        self._add_windows_setup(settings, config, arch)
    
    def _add_disk_configuration(self, settings: ET.Element, config: Dict, arch: str):
        """ディスク構成を追加"""
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Setup',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        disk_config = ET.SubElement(component, 'DiskConfiguration')
        
        # ディスク0の設定
        disk = ET.SubElement(disk_config, 'Disk', wcm_action='add')
        ET.SubElement(disk, 'DiskID').text = '0'
        ET.SubElement(disk, 'WillWipeDisk').text = 'true'
        
        # パーティション作成
        create_partitions = ET.SubElement(disk, 'CreatePartitions')
        
        # EFIパーティション
        efi_partition = ET.SubElement(create_partitions, 'CreatePartition', wcm_action='add')
        ET.SubElement(efi_partition, 'Order').text = '1'
        ET.SubElement(efi_partition, 'Type').text = 'EFI'
        ET.SubElement(efi_partition, 'Size').text = '100'
        
        # MSRパーティション
        msr_partition = ET.SubElement(create_partitions, 'CreatePartition', wcm_action='add')
        ET.SubElement(msr_partition, 'Order').text = '2'
        ET.SubElement(msr_partition, 'Type').text = 'MSR'
        ET.SubElement(msr_partition, 'Size').text = '16'
        
        # プライマリパーティション
        primary_partition = ET.SubElement(create_partitions, 'CreatePartition', wcm_action='add')
        ET.SubElement(primary_partition, 'Order').text = '3'
        ET.SubElement(primary_partition, 'Type').text = 'Primary'
        ET.SubElement(primary_partition, 'Extend').text = 'true'
        
        # パーティションフォーマット
        modify_partitions = ET.SubElement(disk, 'ModifyPartitions')
        
        # EFIフォーマット
        efi_format = ET.SubElement(modify_partitions, 'ModifyPartition', wcm_action='add')
        ET.SubElement(efi_format, 'Order').text = '1'
        ET.SubElement(efi_format, 'PartitionID').text = '1'
        ET.SubElement(efi_format, 'Label').text = 'System'
        ET.SubElement(efi_format, 'Format').text = 'FAT32'
        
        # プライマリフォーマット
        primary_format = ET.SubElement(modify_partitions, 'ModifyPartition', wcm_action='add')
        ET.SubElement(primary_format, 'Order').text = '2'
        ET.SubElement(primary_format, 'PartitionID').text = '3'
        ET.SubElement(primary_format, 'Label').text = 'Windows'
        ET.SubElement(primary_format, 'Format').text = 'NTFS'
        ET.SubElement(primary_format, 'Letter').text = 'C'
    
    def _add_windows_setup(self, settings: ET.Element, config: Dict, arch: str):
        """Windowsセットアップ設定を追加"""
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Setup',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # ユーザーデータ
        user_data = ET.SubElement(component, 'UserData')
        
        # プロダクトキー（必要に応じて）
        product_key = ET.SubElement(user_data, 'ProductKey')
        if config.get('product_key'):
            ET.SubElement(product_key, 'Key').text = config['product_key']
        else:
            ET.SubElement(product_key, 'WillShowUI').text = 'OnError'
        
        # ライセンス同意
        ET.SubElement(user_data, 'AcceptEula').text = 'true'
        
        # 組織情報
        if config.get('organization') or config.get('owner'):
            ET.SubElement(user_data, 'FullName').text = config.get('owner', 'User')
            ET.SubElement(user_data, 'Organization').text = config.get('organization', '')
        
        # OSイメージ選択
        if config.get('image_selection'):
            image_install = ET.SubElement(component, 'ImageInstall')
            os_image = ET.SubElement(image_install, 'OSImage')
            
            install_to = ET.SubElement(os_image, 'InstallTo')
            ET.SubElement(install_to, 'DiskID').text = '0'
            ET.SubElement(install_to, 'PartitionID').text = '3'
            
            # Windows エディション選択
            if config.get('windows_edition'):
                install_from = ET.SubElement(os_image, 'InstallFrom')
                metadata = ET.SubElement(install_from, 'MetaData', wcm_action='add')
                ET.SubElement(metadata, 'Key').text = '/IMAGE/NAME'
                ET.SubElement(metadata, 'Value').text = self.editions.get(
                    config['windows_edition'], 
                    'Windows 11 Professional'
                )
    
    def _add_specialize_settings(self, root: ET.Element, config: Dict):
        """specialize設定を追加"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'specialize')
        arch = config.get('architecture', 'amd64')
        
        # シェル設定
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Shell-Setup',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # コンピューター名
        if config.get('computer_name'):
            ET.SubElement(component, 'ComputerName').text = config['computer_name']
        
        # タイムゾーン
        language = config.get('language', 'ja-JP')
        lang_info = self.language_mapping.get(language, self.language_mapping['ja-JP'])
        ET.SubElement(component, 'TimeZone').text = lang_info['timezone']
        
        # プロダクトキー（Specializeパス用）
        if config.get('product_key'):
            ET.SubElement(component, 'ProductKey').text = config['product_key']
        
        # 地域設定
        international_component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-International-Core',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        ET.SubElement(international_component, 'InputLocale').text = lang_info['locale']
        ET.SubElement(international_component, 'SystemLocale').text = language
        ET.SubElement(international_component, 'UILanguage').text = language
        ET.SubElement(international_component, 'UserLocale').text = language
        
        # ネットワーク設定
        if config.get('network_settings'):
            self._add_network_settings(settings, config, arch)
        
        # Windows機能の有効化/無効化
        if config.get('windows_features'):
            self._add_windows_features(settings, config, arch)
    
    def _add_network_settings(self, settings: ET.Element, config: Dict, arch: str):
        """ネットワーク設定を追加"""
        # Wi-Fi設定
        if config.get('wifi_settings'):
            wifi_config = config['wifi_settings']
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-WiFi-Client-Intel-Netwlv64',
                processorArchitecture=arch,
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            # Wi-Fiプロファイル設定
            if wifi_config.get('ssid'):
                profile = ET.SubElement(component, 'WiFiProfile')
                ET.SubElement(profile, 'SSID').text = wifi_config['ssid']
                if wifi_config.get('password'):
                    ET.SubElement(profile, 'Password').text = wifi_config['password']
        
        # 固定IP設定
        if config.get('static_ip'):
            ip_config = config['static_ip']
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-TCPIP',
                processorArchitecture=arch,
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            interface = ET.SubElement(component, 'Interface', wcm_action='add')
            ET.SubElement(interface, 'Identifier').text = 'Local Area Connection'
            
            # IPv4設定
            ipv4 = ET.SubElement(interface, 'IPv4Settings')
            ET.SubElement(ipv4, 'DhcpEnabled').text = 'false'
            
            unicast = ET.SubElement(interface, 'UnicastIpAddress', wcm_action='add')
            ET.SubElement(unicast, 'IpAddress').text = ip_config.get('ip_address', '')
            ET.SubElement(unicast, 'PrefixLength').text = ip_config.get('subnet_prefix', '24')
            
            if ip_config.get('gateway'):
                route = ET.SubElement(interface, 'Route', wcm_action='add')
                ET.SubElement(route, 'Identifier').text = '0'
                ET.SubElement(route, 'NextHopAddress').text = ip_config['gateway']
    
    def _add_windows_features(self, settings: ET.Element, config: Dict, arch: str):
        """Windows機能の有効化/無効化設定を追加"""
        features = config.get('windows_features', {})
        
        # Windows Defender無効化
        if features.get('disable_defender'):
            component = ET.SubElement(
                settings,
                'component',
                name='Windows-Defender-Features',
                processorArchitecture=arch,
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            ET.SubElement(component, 'DisableAntiSpyware').text = 'true'
        
        # .NET Framework 3.5有効化
        if features.get('enable_dotnet35'):
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-NetFx3-OC-Package',
                processorArchitecture=arch,
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            ET.SubElement(component, 'Enable').text = 'true'
        
        # Windows Update設定
        if features.get('disable_windows_update'):
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-WindowsUpdateClient',
                processorArchitecture=arch,
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            ET.SubElement(component, 'DisableWindowsUpdateAccess').text = 'true'
    
    def _add_oobe_settings(self, root: ET.Element, config: Dict):
        """OOBE（Out-of-Box Experience）設定を追加"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'oobeSystem')
        arch = config.get('architecture', 'amd64')
        
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Shell-Setup',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # OOBE設定
        oobe = ET.SubElement(component, 'OOBE')
        
        # ネットワーク接続をスキップ（Windows 11）
        if config.get('skip_network', True):
            ET.SubElement(oobe, 'SkipMachineOOBE').text = 'true'
            ET.SubElement(oobe, 'SkipUserOOBE').text = 'false'
        
        # プライバシー設定をスキップ
        if config.get('skip_privacy', True):
            ET.SubElement(oobe, 'HideEULAPage').text = 'true'
            ET.SubElement(oobe, 'HideOEMRegistrationScreen').text = 'true'
            ET.SubElement(oobe, 'HideOnlineAccountScreens').text = 'true'
            ET.SubElement(oobe, 'HideWirelessSetupInOOBE').text = 'false'
            ET.SubElement(oobe, 'ProtectYourPC').text = '3'  # 設定をスキップ
        
        # ローカルアカウント設定
        if config.get('bypass_microsoft_account', True):
            # Windows 11でMicrosoftアカウントをバイパス
            ET.SubElement(oobe, 'BypassNetworkCheck').text = 'true'
        
        # ユーザーアカウント設定
        user_accounts = ET.SubElement(component, 'UserAccounts')
        
        # ローカル管理者アカウント
        if config.get('local_accounts'):
            local_accounts = ET.SubElement(user_accounts, 'LocalAccounts')
            
            for account in config['local_accounts']:
                local_account = ET.SubElement(local_accounts, 'LocalAccount', wcm_action='add')
                
                password = ET.SubElement(local_account, 'Password')
                ET.SubElement(password, 'Value').text = self._encode_password(account.get('password', ''))
                ET.SubElement(password, 'PlainText').text = 'false'
                
                ET.SubElement(local_account, 'Description').text = account.get('description', '')
                ET.SubElement(local_account, 'DisplayName').text = account.get('display_name', account['name'])
                ET.SubElement(local_account, 'Group').text = account.get('group', 'Administrators')
                ET.SubElement(local_account, 'Name').text = account['name']
        
        # 自動ログオン設定
        if config.get('auto_logon'):
            auto_logon = ET.SubElement(component, 'AutoLogon')
            password = ET.SubElement(auto_logon, 'Password')
            ET.SubElement(password, 'Value').text = self._encode_password(config['auto_logon'].get('password', ''))
            ET.SubElement(password, 'PlainText').text = 'false'
            
            ET.SubElement(auto_logon, 'Enabled').text = 'true'
            ET.SubElement(auto_logon, 'LogonCount').text = str(config['auto_logon'].get('count', 1))
            ET.SubElement(auto_logon, 'Username').text = config['auto_logon']['username']
        
        # 言語と地域の最終設定
        language = config.get('language', 'ja-JP')
        lang_info = self.language_mapping.get(language, self.language_mapping['ja-JP'])
        
        international_component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-International-Core',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        ET.SubElement(international_component, 'InputLocale').text = lang_info['locale']
        ET.SubElement(international_component, 'SystemLocale').text = language
        ET.SubElement(international_component, 'UILanguage').text = language
        ET.SubElement(international_component, 'UserLocale').text = language
    
    def _add_first_logon_settings(self, root: ET.Element, config: Dict):
        """初回ログオン時の設定を追加"""
        if not config.get('first_logon_commands'):
            return
        
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'oobeSystem')
        arch = config.get('architecture', 'amd64')
        
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Shell-Setup',
            processorArchitecture=arch,
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        first_logon = ET.SubElement(component, 'FirstLogonCommands')
        
        # 初回ログオンコマンド
        for idx, cmd in enumerate(config['first_logon_commands'], 1):
            sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
            ET.SubElement(sync_command, 'Order').text = str(idx)
            ET.SubElement(sync_command, 'CommandLine').text = cmd.get('command', '')
            ET.SubElement(sync_command, 'Description').text = cmd.get('description', f'Command {idx}')
            ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
        
        # カスタマイズスクリプト実行
        if config.get('custom_scripts'):
            self._add_custom_scripts(first_logon, config['custom_scripts'])
        
        # プライバシー設定
        if config.get('privacy_settings'):
            self._add_privacy_settings(first_logon, config['privacy_settings'])
        
        # ブロートウェア削除
        if config.get('remove_bloatware'):
            self._add_bloatware_removal(first_logon, config['remove_bloatware'])
    
    def _add_custom_scripts(self, first_logon: ET.Element, scripts: List[Dict]):
        """カスタムスクリプトを追加"""
        base_order = 100  # 他のコマンドの後に実行
        
        for idx, script in enumerate(scripts):
            sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
            ET.SubElement(sync_command, 'Order').text = str(base_order + idx)
            
            # スクリプトタイプに応じてコマンドを構築
            if script.get('type') == 'powershell':
                command = f'powershell.exe -ExecutionPolicy Bypass -Command "{script["content"]}"'
            elif script.get('type') == 'cmd':
                command = f'cmd.exe /c "{script["content"]}"'
            else:
                command = script.get('content', '')
            
            ET.SubElement(sync_command, 'CommandLine').text = command
            ET.SubElement(sync_command, 'Description').text = script.get('description', f'Custom Script {idx + 1}')
            ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
    
    def _add_privacy_settings(self, first_logon: ET.Element, privacy: Dict):
        """プライバシー設定を追加"""
        base_order = 200
        
        # テレメトリ無効化
        if privacy.get('disable_telemetry'):
            sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
            ET.SubElement(sync_command, 'Order').text = str(base_order)
            ET.SubElement(sync_command, 'CommandLine').text = (
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" '
                '/v AllowTelemetry /t REG_DWORD /d 0 /f'
            )
            ET.SubElement(sync_command, 'Description').text = 'Disable Telemetry'
            ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
            base_order += 1
        
        # Cortana無効化
        if privacy.get('disable_cortana'):
            sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
            ET.SubElement(sync_command, 'Order').text = str(base_order)
            ET.SubElement(sync_command, 'CommandLine').text = (
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" '
                '/v AllowCortana /t REG_DWORD /d 0 /f'
            )
            ET.SubElement(sync_command, 'Description').text = 'Disable Cortana'
            ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
            base_order += 1
        
        # 広告ID無効化
        if privacy.get('disable_advertising_id'):
            sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
            ET.SubElement(sync_command, 'Order').text = str(base_order)
            ET.SubElement(sync_command, 'CommandLine').text = (
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" '
                '/v Enabled /t REG_DWORD /d 0 /f'
            )
            ET.SubElement(sync_command, 'Description').text = 'Disable Advertising ID'
            ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
    
    def _add_bloatware_removal(self, first_logon: ET.Element, bloatware_list: List[str]):
        """ブロートウェア削除コマンドを追加"""
        base_order = 300
        
        # 標準的なブロートウェアリスト
        default_bloatware = [
            'Microsoft.BingNews',
            'Microsoft.BingWeather',
            'Microsoft.GetHelp',
            'Microsoft.Getstarted',
            'Microsoft.Microsoft3DViewer',
            'Microsoft.MicrosoftOfficeHub',
            'Microsoft.MicrosoftSolitaireCollection',
            'Microsoft.MixedReality.Portal',
            'Microsoft.People',
            'Microsoft.SkypeApp',
            'Microsoft.Wallet',
            'Microsoft.WindowsFeedbackHub',
            'Microsoft.Xbox.TCUI',
            'Microsoft.XboxApp',
            'Microsoft.XboxGameOverlay',
            'Microsoft.XboxGamingOverlay',
            'Microsoft.XboxIdentityProvider',
            'Microsoft.XboxSpeechToTextOverlay',
            'Microsoft.ZuneMusic',
            'Microsoft.ZuneVideo'
        ]
        
        # カスタムリストがある場合は使用、なければデフォルト
        apps_to_remove = bloatware_list if bloatware_list else default_bloatware
        
        # PowerShellスクリプトとして一括削除
        removal_script = 'Get-AppxPackage -AllUsers | Where-Object {$_.Name -match "' + '|'.join(apps_to_remove) + '"} | Remove-AppxPackage'
        
        sync_command = ET.SubElement(first_logon, 'SynchronousCommand', wcm_action='add')
        ET.SubElement(sync_command, 'Order').text = str(base_order)
        ET.SubElement(sync_command, 'CommandLine').text = f'powershell.exe -ExecutionPolicy Bypass -Command "{removal_script}"'
        ET.SubElement(sync_command, 'Description').text = 'Remove Bloatware Applications'
        ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
    
    def _encode_password(self, password: str) -> str:
        """パスワードをBase64エンコード"""
        if not password:
            return ""
        
        # Windows用にUTF-16LEでエンコード（パスワード + "Password"）
        password_with_suffix = password + "Password"
        password_bytes = password_with_suffix.encode('utf-16le')
        encoded = base64.b64encode(password_bytes).decode('ascii')
        return encoded
    
    def _prettify_xml(self, element: ET.Element) -> str:
        """XMLを整形して読みやすくする"""
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # XML宣言を追加
        xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
        pretty_xml = reparsed.documentElement.toprettyxml(indent="    ")
        
        # 不要な空行を削除
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        
        return xml_declaration + '\n'.join(lines)
    
    def validate(self, xml_string: str) -> Dict[str, Any]:
        """
        生成されたXMLを検証
        
        Returns:
            検証結果（valid: bool, errors: List[str]）
        """
        errors = []
        
        try:
            # XMLパース検証
            ET.fromstring(xml_string)
            
            # 必須要素の確認
            root = ET.fromstring(xml_string)
            
            # settings要素の確認（名前空間を考慮）
            settings_passes = ['windowsPE', 'specialize', 'oobeSystem']
            namespaces = {'unattend': 'urn:schemas-microsoft-com:unattend'}
            for pass_name in settings_passes:
                settings = root.find(f".//unattend:settings[@pass='{pass_name}']", namespaces)
                if settings is None:
                    # 名前空間なしでも試行
                    settings = root.find(f".//settings[@pass='{pass_name}']")
                    if settings is None:
                        errors.append(f"必須のsettings pass '{pass_name}' が見つかりません")
            
            # その他の検証...
            
        except ET.ParseError as e:
            errors.append(f"XML解析エラー: {str(e)}")
        except Exception as e:
            errors.append(f"検証エラー: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


class XMLGeneratorSubAgent:
    """XML生成専用SubAgent"""
    
    def __init__(self):
        self.generator = UnattendXMLGenerator()
        self.name = "XMLGeneratorAgent"
        self.capabilities = [
            "generate_xml",
            "validate_xml",
            "customize_settings",
            "export_xml"
        ]
    
    async def process(self, config: Dict) -> Dict:
        """設定を処理してXMLを生成"""
        try:
            # XML生成
            xml_content = self.generator.generate(config)
            
            # 検証
            validation_result = self.generator.validate(xml_content)
            
            return {
                'success': True,
                'xml': xml_content,
                'validation': validation_result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }