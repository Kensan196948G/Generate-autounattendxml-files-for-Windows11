"""
拡張XML生成器
より完全なunattend.xml生成機能を提供
"""

import base64
from xml.etree import ElementTree as ET
from typing import Dict, Any, List

class EnhancedXMLGenerator:
    """拡張版unattend.xml生成器"""
    
    def __init__(self):
        self.namespaces = {
            'unattend': 'urn:schemas-microsoft-com:unattend',
            'wcm': 'http://schemas.microsoft.com/WMIConfig/2002/State'
        }
    
    def generate_complete_xml(self, config: Dict[str, Any]) -> str:
        """
        完全なunattend.xmlを生成
        """
        # ルート要素
        root = ET.Element('unattend')
        root.set('xmlns', 'urn:schemas-microsoft-com:unattend')
        
        # 各パスの設定を追加
        self._add_windows_pe_pass(root, config)
        self._add_specialize_pass(root, config)
        self._add_oobe_pass(root, config)
        
        # FirstLogonCommandsがある場合は追加
        if config.get('first_logon_commands'):
            self._add_first_logon_pass(root, config)
        
        return self._prettify_xml(root)
    
    def _add_windows_pe_pass(self, root: ET.Element, config: Dict):
        """windowsPEパスの設定"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'windowsPE')
        
        arch = config.get('architecture', 'amd64')
        
        # 言語設定
        component = self._create_component(settings, 
            'Microsoft-Windows-International-Core-WinPE', arch)
        
        language = config.get('language', 'ja-JP')
        setup_ui = ET.SubElement(component, 'SetupUILanguage')
        ET.SubElement(setup_ui, 'UILanguage').text = language
        
        ET.SubElement(component, 'InputLocale').text = '0411:00000411' if language == 'ja-JP' else '0409:00000409'
        ET.SubElement(component, 'SystemLocale').text = language
        ET.SubElement(component, 'UILanguage').text = language
        ET.SubElement(component, 'UserLocale').text = language
        
        # セットアップ設定
        setup_component = self._create_component(settings, 
            'Microsoft-Windows-Setup', arch)
        
        # プロダクトキー
        user_data = ET.SubElement(setup_component, 'UserData')
        if config.get('product_key'):
            product_key = ET.SubElement(user_data, 'ProductKey')
            ET.SubElement(product_key, 'Key').text = config['product_key']
        else:
            product_key = ET.SubElement(user_data, 'ProductKey')
            ET.SubElement(product_key, 'WillShowUI').text = 'OnError'
        
        ET.SubElement(user_data, 'AcceptEula').text = 'true'
    
    def _add_specialize_pass(self, root: ET.Element, config: Dict):
        """specializeパスの設定"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'specialize')
        
        arch = config.get('architecture', 'amd64')
        
        # Shell設定
        component = self._create_component(settings, 
            'Microsoft-Windows-Shell-Setup', arch)
        
        ET.SubElement(component, 'TimeZone').text = config.get('timezone', 'Tokyo Standard Time')
        
        if config.get('product_key'):
            ET.SubElement(component, 'ProductKey').text = config['product_key']
        
        if config.get('computer_name'):
            ET.SubElement(component, 'ComputerName').text = config['computer_name']
        
        # 言語設定
        intl_component = self._create_component(settings, 
            'Microsoft-Windows-International-Core', arch)
        
        language = config.get('language', 'ja-JP')
        locale = '0411:00000411' if language == 'ja-JP' else '0409:00000409'
        
        ET.SubElement(intl_component, 'InputLocale').text = locale
        ET.SubElement(intl_component, 'SystemLocale').text = language
        ET.SubElement(intl_component, 'UILanguage').text = language
        ET.SubElement(intl_component, 'UserLocale').text = language
        
        # Wi-Fi設定（specializeパスに追加）
        if config.get('wifi_settings'):
            self._add_wifi_settings(settings, config['wifi_settings'], arch)
    
    def _add_wifi_settings(self, settings: ET.Element, wifi_config: Dict, arch: str):
        """Wi-Fi設定を追加（より詳細な形式）"""
        # Microsoft-Windows-WiFi-ConfigSPコンポーネントを使用
        component = self._create_component(settings,
            'Microsoft-Windows-WiFi-ConfigSP', arch)
        
        # Wi-Fiプロファイルの追加
        wifi_profiles = ET.SubElement(component, 'WiFiProfiles')
        profile = ET.SubElement(wifi_profiles, 'WiFiProfile')
        # wcm:actionは使用しない（名前空間の問題を回避）
        
        # プロファイル名とSSID
        ET.SubElement(profile, 'ProfileName').text = wifi_config.get('ssid', 'Network')
        
        # SSID設定
        ssid_config = ET.SubElement(profile, 'SSIDConfig')
        ssid = ET.SubElement(ssid_config, 'SSID')
        ET.SubElement(ssid, 'name').text = wifi_config.get('ssid', 'Network')
        
        # 接続設定
        ET.SubElement(profile, 'ConnectionType').text = 'ESS'
        ET.SubElement(profile, 'ConnectionMode').text = 'auto' if wifi_config.get('connect_automatically', True) else 'manual'
        
        # セキュリティ設定
        if wifi_config.get('password'):
            msm = ET.SubElement(profile, 'MSM')
            security = ET.SubElement(msm, 'security')
            
            auth_encryption = ET.SubElement(security, 'authEncryption')
            ET.SubElement(auth_encryption, 'authentication').text = 'WPA2PSK'
            ET.SubElement(auth_encryption, 'encryption').text = 'AES'
            
            shared_key = ET.SubElement(security, 'sharedKey')
            ET.SubElement(shared_key, 'keyType').text = 'passPhrase'
            ET.SubElement(shared_key, 'protected').text = 'false'
            ET.SubElement(shared_key, 'keyMaterial').text = wifi_config['password']
    
    def _add_oobe_pass(self, root: ET.Element, config: Dict):
        """oobeSystemパスの設定"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'oobeSystem')
        
        arch = config.get('architecture', 'amd64')
        
        # Shell設定
        component = self._create_component(settings, 
            'Microsoft-Windows-Shell-Setup', arch)
        
        # OOBE設定
        oobe = ET.SubElement(component, 'OOBE')
        
        # Windows 11要件バイパス
        if config.get('bypass_win11_requirements'):
            ET.SubElement(oobe, 'SkipMachineOOBE').text = 'true'
            
        ET.SubElement(oobe, 'SkipUserOOBE').text = 'false'
        ET.SubElement(oobe, 'HideEULAPage').text = 'true'
        ET.SubElement(oobe, 'HideOEMRegistrationScreen').text = 'true'
        ET.SubElement(oobe, 'HideOnlineAccountScreens').text = 'true'
        ET.SubElement(oobe, 'HideWirelessSetupInOOBE').text = 'false'
        ET.SubElement(oobe, 'ProtectYourPC').text = '3'
        
        # ネットワークチェックバイパス
        if config.get('bypass_microsoft_account', True):
            ET.SubElement(oobe, 'BypassNetworkCheck').text = 'true'
        
        # ユーザーアカウント設定
        user_accounts = ET.SubElement(component, 'UserAccounts')
        local_accounts = ET.SubElement(user_accounts, 'LocalAccounts')
        
        # ローカルアカウントの追加
        for account in config.get('local_accounts', []):
            local_account = ET.SubElement(local_accounts, 'LocalAccount')
            # wcm:actionは使用しない（名前空間の問題を回避）
            
            # パスワード設定
            password = ET.SubElement(local_account, 'Password')
            ET.SubElement(password, 'Value').text = self._encode_password(account.get('password', ''))
            ET.SubElement(password, 'PlainText').text = 'false'
            
            ET.SubElement(local_account, 'Description').text = account.get('description', '')
            ET.SubElement(local_account, 'DisplayName').text = account.get('display_name', account['name'])
            ET.SubElement(local_account, 'Group').text = account.get('group', 'Administrators')
            ET.SubElement(local_account, 'Name').text = account['name']
        
        # 言語設定
        intl_component = self._create_component(settings, 
            'Microsoft-Windows-International-Core', arch)
        
        language = config.get('language', 'ja-JP')
        locale = '0411:00000411' if language == 'ja-JP' else '0409:00000409'
        
        ET.SubElement(intl_component, 'InputLocale').text = locale
        ET.SubElement(intl_component, 'SystemLocale').text = language
        ET.SubElement(intl_component, 'UILanguage').text = language
        ET.SubElement(intl_component, 'UserLocale').text = language
    
    def _add_first_logon_pass(self, root: ET.Element, config: Dict):
        """FirstLogonCommandsパスの設定"""
        settings = ET.SubElement(root, 'settings')
        settings.set('pass', 'oobeSystem')
        
        arch = config.get('architecture', 'amd64')
        component = self._create_component(settings, 
            'Microsoft-Windows-Shell-Setup', arch)
        
        commands = ET.SubElement(component, 'FirstLogonCommands')
        
        # Windows機能の有効化
        order = 1
        
        if config.get('enable_dotnet35'):
            command = ET.SubElement(commands, 'SynchronousCommand')
            # wcm:actionは使用しない
            ET.SubElement(command, 'Order').text = str(order)
            ET.SubElement(command, 'CommandLine').text = 'dism /online /enable-feature /featurename:NetFx3 /all'
            ET.SubElement(command, 'Description').text = 'Enable .NET Framework 3.5'
            order += 1
        
        if config.get('enable_hyperv'):
            command = ET.SubElement(commands, 'SynchronousCommand')
            # wcm:actionは使用しない
            ET.SubElement(command, 'Order').text = str(order)
            ET.SubElement(command, 'CommandLine').text = 'dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all'
            ET.SubElement(command, 'Description').text = 'Enable Hyper-V'
            order += 1
        
        if config.get('enable_wsl'):
            command = ET.SubElement(commands, 'SynchronousCommand')
            # wcm:actionは使用しない
            ET.SubElement(command, 'Order').text = str(order)
            ET.SubElement(command, 'CommandLine').text = 'dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all'
            ET.SubElement(command, 'Description').text = 'Enable WSL'
            order += 1
        
        # カスタムコマンド
        for cmd in config.get('first_logon_commands', []):
            command = ET.SubElement(commands, 'SynchronousCommand')
            # wcm:actionは使用しない
            ET.SubElement(command, 'Order').text = str(order)
            ET.SubElement(command, 'CommandLine').text = cmd['command']
            ET.SubElement(command, 'Description').text = cmd.get('description', '')
            order += 1
    
    def _create_component(self, parent: ET.Element, name: str, arch: str) -> ET.Element:
        """コンポーネント要素を作成"""
        component = ET.SubElement(parent, 'component')
        component.set('name', name)
        component.set('processorArchitecture', arch)
        component.set('publicKeyToken', '31bf3856ad364e35')
        component.set('language', 'neutral')
        component.set('versionScope', 'nonSxS')
        return component
    
    def _encode_password(self, password: str) -> str:
        """パスワードを正しくBase64エンコード"""
        if not password:
            return ""
        
        # パスワード + "Password"をUTF-16LEでエンコード
        password_with_suffix = password + "Password"
        password_bytes = password_with_suffix.encode('utf-16le')
        return base64.b64encode(password_bytes).decode('ascii')
    
    def _prettify_xml(self, element: ET.Element) -> str:
        """XMLを整形"""
        from xml.dom import minidom
        
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # XML宣言を追加
        return reparsed.toprettyxml(indent="    ", encoding="utf-8").decode('utf-8')