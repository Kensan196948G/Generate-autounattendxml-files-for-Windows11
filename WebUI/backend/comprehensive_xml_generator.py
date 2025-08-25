"""
包括的XML生成モジュール
全23項目の設定をautounattend.xmlに反映
"""

import xml.etree.ElementTree as ET
import base64
from typing import Dict, Any, List

class ComprehensiveXMLGenerator:
    """全23項目対応のXML生成クラス"""
    
    def __init__(self):
        self.namespaces = {
            'xmlns': 'urn:schemas-microsoft-com:unattend',
            'wcm': 'http://schemas.microsoft.com/WMIConfig/2002/State'
        }
    
    def generate_complete_xml(self, config: Dict[str, Any]) -> str:
        """
        包括的な設定からautounattend.xmlを生成
        """
        # ルート要素の作成
        root = ET.Element('unattend', xmlns=self.namespaces['xmlns'])
        
        # 各パスの設定を追加
        self._add_windows_pe_pass(root, config)
        self._add_specialize_pass(root, config)
        self._add_oobe_system_pass(root, config)
        self._add_offline_servicing_pass(root, config)
        
        # XMLを文字列に変換
        return self._prettify_xml(root)
    
    def _add_windows_pe_pass(self, root: ET.Element, config: Dict[str, Any]):
        """Windows PEパスの設定"""
        settings = ET.SubElement(root, 'settings', pass_='windowsPE')
        
        # 1. 地域と言語の設定
        self._add_international_core_winpe(settings, config)
        
        # 4. Windowsエディションとプロダクトキー
        self._add_setup_component(settings, config)
        
        # 5. Windows PE設定
        self._add_winpe_settings(settings, config)
        
        # 6. ディスク構成
        self._add_disk_configuration(settings, config)
    
    def _add_specialize_pass(self, root: ET.Element, config: Dict[str, Any]):
        """Specializeパスの設定"""
        settings = ET.SubElement(root, 'settings', pass_='specialize')
        
        # 7. コンピューター設定
        self._add_computer_settings(settings, config)
        
        # 9. エクスプローラー設定
        self._add_explorer_settings(settings, config)
        
        # 11. システム調整
        self._add_system_tweaks(settings, config)
        
        # 14. 仮想マシンサポート
        self._add_vm_features(settings, config)
        
        # 15. Wi-Fi設定
        if config.get('wifi_settings'):
            self._add_wifi_config(settings, config)
        
        # 22. WDAC設定
        self._add_wdac_settings(settings, config)
        
        # 23. その他のコンポーネント
        self._add_additional_components(settings, config)
    
    def _add_oobe_system_pass(self, root: ET.Element, config: Dict[str, Any]):
        """OOBEシステムパスの設定"""
        settings = ET.SubElement(root, 'settings', pass_='oobeSystem')
        
        # 3. セットアップの挙動
        self._add_oobe_settings(settings, config)
        
        # 8. ユーザーアカウント
        self._add_user_accounts(settings, config)
        
        # 10. スタート/タスクバー
        self._add_start_taskbar_settings(settings, config)
        
        # 12. 視覚効果
        self._add_visual_effects(settings, config)
        
        # 13. デスクトップ設定
        self._add_desktop_settings(settings, config)
        
        # 16. Express Settings
        self._add_express_settings(settings, config)
        
        # 17. ロックキー設定
        self._add_lock_keys(settings, config)
        
        # 18. 固定キー
        self._add_sticky_keys(settings, config)
        
        # 19. 個人用設定
        self._add_personalization(settings, config)
        
        # 20. 不要なアプリの削除
        self._add_remove_apps(settings, config)
        
        # 21. カスタムスクリプト
        self._add_custom_scripts(settings, config)
    
    def _add_offline_servicing_pass(self, root: ET.Element, config: Dict[str, Any]):
        """オフラインサービシングパス（オプション）"""
        if config.get('offline_updates'):
            settings = ET.SubElement(root, 'settings', pass_='offlineServicing')
            # オフライン更新の設定
    
    def _add_international_core_winpe(self, settings: ET.Element, config: Dict[str, Any]):
        """地域と言語の設定（Windows PE）"""
        component = ET.SubElement(
            settings, 
            'component',
            name='Microsoft-Windows-International-Core-WinPE',
            processorArchitecture=config.get('architecture', 'amd64'),
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        setup_ui = ET.SubElement(component, 'SetupUILanguage')
        ET.SubElement(setup_ui, 'UILanguage').text = config.get('language', 'ja-JP')
        
        ET.SubElement(component, 'InputLocale').text = config.get('input_locale', '0411:00000411')
        ET.SubElement(component, 'SystemLocale').text = config.get('system_locale', 'ja-JP')
        ET.SubElement(component, 'UILanguage').text = config.get('ui_language', 'ja-JP')
        ET.SubElement(component, 'UserLocale').text = config.get('user_locale', 'ja-JP')
    
    def _add_setup_component(self, settings: ET.Element, config: Dict[str, Any]):
        """セットアップコンポーネント（エディション/プロダクトキー）"""
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Setup',
            processorArchitecture=config.get('architecture', 'amd64'),
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # プロダクトキー設定
        if config.get('product_key'):
            user_data = ET.SubElement(component, 'UserData')
            product_key = ET.SubElement(user_data, 'ProductKey')
            ET.SubElement(product_key, 'Key').text = config['product_key']
            ET.SubElement(user_data, 'AcceptEula').text = 'true'
        
        # Windows 11要件バイパス
        if config.get('bypass_win11_requirements'):
            run_sync = ET.SubElement(component, 'RunSynchronous')
            
            # TPMバイパス
            cmd1 = ET.SubElement(run_sync, 'RunSynchronousCommand')
            ET.SubElement(cmd1, 'Order').text = '1'
            ET.SubElement(cmd1, 'Path').text = 'reg add HKLM\\SYSTEM\\Setup\\LabConfig /v BypassTPMCheck /t REG_DWORD /d 1 /f'
            
            # セキュアブートバイパス
            cmd2 = ET.SubElement(run_sync, 'RunSynchronousCommand')
            ET.SubElement(cmd2, 'Order').text = '2'
            ET.SubElement(cmd2, 'Path').text = 'reg add HKLM\\SYSTEM\\Setup\\LabConfig /v BypassSecureBootCheck /t REG_DWORD /d 1 /f'
            
            # CPU要件バイパス
            cmd3 = ET.SubElement(run_sync, 'RunSynchronousCommand')
            ET.SubElement(cmd3, 'Order').text = '3'
            ET.SubElement(cmd3, 'Path').text = 'reg add HKLM\\SYSTEM\\Setup\\LabConfig /v BypassCPUCheck /t REG_DWORD /d 1 /f'
            
            # RAM要件バイパス
            cmd4 = ET.SubElement(run_sync, 'RunSynchronousCommand')
            ET.SubElement(cmd4, 'Order').text = '4'
            ET.SubElement(cmd4, 'Path').text = 'reg add HKLM\\SYSTEM\\Setup\\LabConfig /v BypassRAMCheck /t REG_DWORD /d 1 /f'
    
    def _add_winpe_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """Windows PE固有の設定"""
        pe_config = config.get('windows_pe', {})
        
        if pe_config:
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-Setup',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            if pe_config.get('disable_firewall'):
                ET.SubElement(component, 'EnableFirewall').text = 'false'
            
            if pe_config.get('enable_network'):
                ET.SubElement(component, 'EnableNetwork').text = 'true'
    
    def _add_disk_configuration(self, settings: ET.Element, config: Dict[str, Any]):
        """ディスク構成"""
        disk_config = config.get('disk_config', {})
        
        if disk_config and disk_config.get('wipe_disk'):
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-Setup',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            disk_cfg = ET.SubElement(component, 'DiskConfiguration')
            disk = ET.SubElement(disk_cfg, 'Disk')
            
            ET.SubElement(disk, 'DiskID').text = str(disk_config.get('disk_id', 0))
            ET.SubElement(disk, 'WillWipeDisk').text = 'true'
            
            # パーティション作成
            create_partitions = ET.SubElement(disk, 'CreatePartitions')
            partitions = disk_config.get('partitions', [])
            
            for i, part in enumerate(partitions, 1):
                partition = ET.SubElement(create_partitions, 'CreatePartition')
                ET.SubElement(partition, 'Order').text = str(i)
                
                if part['type'] == 'EFI':
                    ET.SubElement(partition, 'Type').text = 'EFI'
                    ET.SubElement(partition, 'Size').text = str(part.get('size', 100))
                elif part['type'] == 'MSR':
                    ET.SubElement(partition, 'Type').text = 'MSR'
                    ET.SubElement(partition, 'Size').text = str(part.get('size', 16))
                elif part['type'] == 'Primary':
                    ET.SubElement(partition, 'Type').text = 'Primary'
                    if part.get('size') == 'remaining':
                        ET.SubElement(partition, 'Extend').text = 'true'
                    else:
                        ET.SubElement(partition, 'Size').text = str(part['size'])
    
    def _add_computer_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """コンピューター設定"""
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Shell-Setup',
            processorArchitecture=config.get('architecture', 'amd64'),
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        # コンピューター名設定（*も含めて設定）
        computer_name = config.get('computer_name', '*')
        if computer_name:
            ET.SubElement(component, 'ComputerName').text = computer_name
        
        if config.get('timezone'):
            ET.SubElement(component, 'TimeZone').text = config['timezone']
        
        if config.get('product_key'):
            ET.SubElement(component, 'ProductKey').text = config['product_key']
    
    def _add_oobe_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """OOBE設定"""
        component = ET.SubElement(
            settings,
            'component',
            name='Microsoft-Windows-Shell-Setup',
            processorArchitecture=config.get('architecture', 'amd64'),
            publicKeyToken='31bf3856ad364e35',
            language='neutral',
            versionScope='nonSxS'
        )
        
        oobe = ET.SubElement(component, 'OOBE')
        
        ET.SubElement(oobe, 'SkipMachineOOBE').text = str(config.get('skip_machine_oobe', True)).lower()
        ET.SubElement(oobe, 'SkipUserOOBE').text = str(config.get('skip_user_oobe', False)).lower()
        ET.SubElement(oobe, 'HideEULAPage').text = str(config.get('hide_eula_page', True)).lower()
        ET.SubElement(oobe, 'HideOEMRegistrationScreen').text = str(config.get('hide_oem_registration', True)).lower()
        ET.SubElement(oobe, 'HideOnlineAccountScreens').text = str(config.get('hide_online_account_screens', True)).lower()
        ET.SubElement(oobe, 'HideWirelessSetupInOOBE').text = str(config.get('hide_wireless_setup', False)).lower()
        ET.SubElement(oobe, 'ProtectYourPC').text = str(config.get('protect_your_pc', 3))
        
        if config.get('bypass_network_check'):
            ET.SubElement(oobe, 'BypassNetworkCheck').text = 'true'
    
    def _add_user_accounts(self, settings: ET.Element, config: Dict[str, Any]):
        """ユーザーアカウント設定"""
        component = None
        for child in settings:
            if child.get('name') == 'Microsoft-Windows-Shell-Setup':
                component = child
                break
        
        if component is None:
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-Shell-Setup',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
        
        accounts = config.get('local_accounts', [])
        if accounts:
            user_accounts = ET.SubElement(component, 'UserAccounts')
            local_accounts = ET.SubElement(user_accounts, 'LocalAccounts')
            
            for account in accounts:
                local_account = ET.SubElement(local_accounts, 'LocalAccount')
                
                password_elem = ET.SubElement(local_account, 'Password')
                ET.SubElement(password_elem, 'Value').text = self._encode_password(account.get('password', 'password'))
                ET.SubElement(password_elem, 'PlainText').text = 'false'
                
                ET.SubElement(local_account, 'Description').text = account.get('description', '')
                ET.SubElement(local_account, 'DisplayName').text = account.get('display_name', account.get('name', ''))
                ET.SubElement(local_account, 'Group').text = account.get('group', 'Users')
                ET.SubElement(local_account, 'Name').text = account.get('name', 'user')
            
            # 自動ログオン設定
            if config.get('auto_logon_count', 0) > 0:
                auto_logon = ET.SubElement(component, 'AutoLogon')
                ET.SubElement(auto_logon, 'Enabled').text = 'true'
                ET.SubElement(auto_logon, 'LogonCount').text = str(config['auto_logon_count'])
                ET.SubElement(auto_logon, 'Username').text = accounts[0].get('name', 'user')
                
                password_elem = ET.SubElement(auto_logon, 'Password')
                ET.SubElement(password_elem, 'Value').text = self._encode_password(accounts[0].get('password', 'password'))
                ET.SubElement(password_elem, 'PlainText').text = 'false'
    
    def _add_wifi_config(self, settings: ET.Element, config: Dict[str, Any]):
        """Wi-Fi設定"""
        wifi = config.get('wifi_settings', {})
        
        if wifi and wifi.get('ssid'):
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-WiFi-ConfigSP',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            wifi_profiles = ET.SubElement(component, 'WiFiProfiles')
            wifi_profile = ET.SubElement(wifi_profiles, 'WiFiProfile')
            
            ET.SubElement(wifi_profile, 'ProfileName').text = wifi['ssid']
            
            ssid_config = ET.SubElement(wifi_profile, 'SSIDConfig')
            ssid = ET.SubElement(ssid_config, 'SSID')
            ET.SubElement(ssid, 'name').text = wifi['ssid']
            
            ET.SubElement(wifi_profile, 'ConnectionType').text = 'ESS'
            ET.SubElement(wifi_profile, 'ConnectionMode').text = 'auto' if wifi.get('connect_automatically', True) else 'manual'
            
            msm = ET.SubElement(wifi_profile, 'MSM')
            security = ET.SubElement(msm, 'security')
            
            auth_encryption = ET.SubElement(security, 'authEncryption')
            ET.SubElement(auth_encryption, 'authentication').text = wifi.get('auth_type', 'WPA2PSK')
            ET.SubElement(auth_encryption, 'encryption').text = wifi.get('encryption', 'AES')
            
            if wifi.get('password'):
                shared_key = ET.SubElement(security, 'sharedKey')
                ET.SubElement(shared_key, 'keyType').text = 'passPhrase'
                ET.SubElement(shared_key, 'protected').text = 'false'
                ET.SubElement(shared_key, 'keyMaterial').text = wifi['password']
    
    def _add_custom_scripts(self, settings: ET.Element, config: Dict[str, Any]):
        """カスタムスクリプトと包括的設定"""
        # コンポーネントを取得または作成
        component = None
        for child in settings:
            if child.get('name') == 'Microsoft-Windows-Shell-Setup':
                component = child
                break
        
        if component is None:
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-Shell-Setup',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
        
        # 包括的なFirstLogonCommandsを構築
        self._build_comprehensive_first_logon_commands(component, config)
    
    def _build_comprehensive_first_logon_commands(self, component: ET.Element, config: Dict[str, Any]):
        """全設定項目を統合したFirstLogonCommandsを構築"""
        first_logon = ET.SubElement(component, 'FirstLogonCommands')
        command_order = 1
        
        # 9. エクスプローラー設定
        explorer = config.get('explorer_settings', {})
        if explorer:
            if explorer.get('show_file_extensions'):
                self._add_command(first_logon, command_order, 
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f',
                    'Show file extensions')
                command_order += 1
            
            if explorer.get('show_hidden_files'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 1 /f',
                    'Show hidden files')
                command_order += 1
            
            if explorer.get('launch_to') == 'ThisPC':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f',
                    'Set Explorer launch to This PC')
                command_order += 1
        
        # 10. スタート/タスクバー設定
        taskbar = config.get('start_taskbar', {})
        if taskbar:
            if taskbar.get('taskbar_alignment') == 'Left':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarAl /t REG_DWORD /d 0 /f',
                    'Align taskbar to left')
                command_order += 1
            
            if not taskbar.get('taskbar_widgets'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarDa /t REG_DWORD /d 0 /f',
                    'Hide taskbar widgets')
                command_order += 1
            
            if not taskbar.get('taskbar_chat'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarMn /t REG_DWORD /d 0 /f',
                    'Hide taskbar chat')
                command_order += 1
        
        # 11. システム調整
        tweaks = config.get('system_tweaks', {})
        if tweaks:
            if tweaks.get('disable_telemetry'):
                self._add_command(first_logon, command_order,
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                    'Disable telemetry')
                command_order += 1
            
            if tweaks.get('disable_cortana'):
                self._add_command(first_logon, command_order,
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f',
                    'Disable Cortana')
                command_order += 1
            
            if tweaks.get('disable_search_web'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
                    'Disable web search')
                command_order += 1
            
            if tweaks.get('disable_game_bar'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
                    'Disable Game Bar')
                command_order += 1
        
        # 14. 仮想マシンサポート
        vm_support = config.get('vm_support', {})
        if vm_support:
            if vm_support.get('enable_hyperv'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart',
                    'Enable Hyper-V')
                command_order += 1
            
            if vm_support.get('enable_wsl'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart',
                    'Enable WSL')
                command_order += 1
        
        # 12. 視覚効果
        visual = config.get('visual_effects', {})
        if visual:
            if visual.get('performance_mode') == 'Performance':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f',
                    'Set visual effects for performance')
                command_order += 1
            elif visual.get('performance_mode') == 'Appearance':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 1 /f',
                    'Set visual effects for appearance')
                command_order += 1
            
            if not visual.get('transparency'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f',
                    'Disable transparency effects')
                command_order += 1
            
            if not visual.get('animations'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f',
                    'Disable animations')
                command_order += 1
        
        # 13. デスクトップ設定
        desktop = config.get('desktop_settings', {})
        if desktop:
            desktop_icons = config.get('desktop_icons', {})
            if desktop_icons.get('computer'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel" /v {20D04FE0-3AEA-1069-A2D8-08002B30309D} /t REG_DWORD /d 0 /f',
                    'Show This PC on desktop')
                command_order += 1
            
            if desktop_icons.get('user_files'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel" /v {59031a47-3f72-44a7-89c5-5595fe6b30ee} /t REG_DWORD /d 0 /f',
                    'Show User Files on desktop')
                command_order += 1
            
            if desktop_icons.get('network'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel" /v {F02C1A0D-BE21-4350-88B0-7367FC96EF3C} /t REG_DWORD /d 0 /f',
                    'Show Network on desktop')
                command_order += 1
            
            if desktop_icons.get('recycle_bin'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel" /v {645FF040-5081-101B-9F08-00AA002F954E} /t REG_DWORD /d 0 /f',
                    'Show Recycle Bin on desktop')
                command_order += 1
            
            if desktop_icons.get('control_panel'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\HideDesktopIcons\\NewStartPanel" /v {5399E694-6CE5-4D6C-8FCE-1D8870FDCBA0} /t REG_DWORD /d 0 /f',
                    'Show Control Panel on desktop')
                command_order += 1
        
        # 16. Express Settings（プライバシー設定）
        express = config.get('express_settings', {})
        if express:
            if not express.get('send_diagnostic_data'):
                self._add_command(first_logon, command_order,
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                    'Disable diagnostic data')
                command_order += 1
            
            if not express.get('advertising_id'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
                    'Disable advertising ID')
                command_order += 1
            
            if not express.get('location_services'):
                self._add_command(first_logon, command_order,
                    'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 1 /f',
                    'Disable location services')
                command_order += 1
            
            if not express.get('tailored_experiences'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Privacy" /v TailoredExperiencesWithDiagnosticDataEnabled /t REG_DWORD /d 0 /f',
                    'Disable tailored experiences')
                command_order += 1
        
        # 17. ロックキー設定
        lock_keys = config.get('lock_keys', {})
        if lock_keys:
            if lock_keys.get('num_lock'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Control Panel\\Keyboard" /v InitialKeyboardIndicators /t REG_SZ /d 2 /f',
                    'Enable NumLock on startup')
                command_order += 1
            
            if not lock_keys.get('caps_lock'):
                self._add_command(first_logon, command_order,
                    'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Keyboard Layout" /v "Scancode Map" /t REG_BINARY /d 00000000000000000200000000003A0000000000 /f',
                    'Disable CapsLock')
                command_order += 1
        
        # 18. 固定キー
        sticky = config.get('sticky_keys', {})
        if sticky:
            if not sticky.get('enabled'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Control Panel\\Accessibility\\StickyKeys" /v Flags /t REG_SZ /d 506 /f',
                    'Disable sticky keys')
                command_order += 1
            else:
                flags = 510  # Base value for enabled
                if sticky.get('lock_modifier'):
                    flags |= 1
                if sticky.get('turn_off_on_two_keys'):
                    flags |= 4
                if sticky.get('feedback'):
                    flags |= 32
                if sticky.get('beep'):
                    flags |= 64
                
                self._add_command(first_logon, command_order,
                    f'reg add "HKCU\\Control Panel\\Accessibility\\StickyKeys" /v Flags /t REG_SZ /d {flags} /f',
                    'Configure sticky keys')
                command_order += 1
        
        # 19. 個人用設定
        personal = config.get('personalization', {})
        if personal:
            if personal.get('theme') == 'Dark':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f',
                    'Set dark theme for apps')
                command_order += 1
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 0 /f',
                    'Set dark theme for system')
                command_order += 1
            elif personal.get('theme') == 'Light':
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 1 /f',
                    'Set light theme for apps')
                command_order += 1
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v SystemUsesLightTheme /t REG_DWORD /d 1 /f',
                    'Set light theme for system')
                command_order += 1
            
            if personal.get('accent_color'):
                # Convert hex color to DWORD (BGR format)
                color = personal['accent_color'].replace('#', '')
                if len(color) == 6:
                    bgr = f"0x00{color[4:6]}{color[2:4]}{color[0:2]}"
                    self._add_command(first_logon, command_order,
                        f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent" /v AccentColorMenu /t REG_DWORD /d {bgr} /f',
                        'Set accent color')
                    command_order += 1
            
            if personal.get('start_color'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v ColorPrevalence /t REG_DWORD /d 1 /f',
                    'Enable color on Start and Action Center')
                command_order += 1
            
            if personal.get('taskbar_color'):
                self._add_command(first_logon, command_order,
                    'reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v ColorPrevalence /t REG_DWORD /d 1 /f',
                    'Enable color on taskbar')
                command_order += 1
            
            # アクセントカラーの設定
            accent_color = personal.get('accent_color', '')
            if accent_color:
                # DWORD値に変換（FF0078D4 -> 0xD47800FF）
                if accent_color.startswith('FF'):
                    accent_color = accent_color[2:]  # FFを削除
                if len(accent_color) == 6:
                    # BGR形式に変換
                    r, g, b = accent_color[0:2], accent_color[2:4], accent_color[4:6]
                    bgr_value = f"0x{b}{g}{r}FF"
                    decimal_value = int(bgr_value, 16)
                    self._add_command(first_logon, command_order,
                        f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Accent" /v AccentColorMenu /t REG_DWORD /d {decimal_value} /f',
                        'Set accent color')
                    command_order += 1
        
        # 20. 不要なアプリの削除
        remove_apps = config.get('remove_apps', [])
        for app in remove_apps:
            self._add_command(first_logon, command_order,
                f'powershell -Command "Get-AppxPackage *{app}* | Remove-AppxPackage"',
                f'Remove {app}')
            command_order += 1
        
        # 21. カスタムスクリプト
        custom_scripts = config.get('customScripts', {})
        if custom_scripts:
            # 初回ログオン時のカスタムコマンド
            first_logon_scripts = custom_scripts.get('firstLogon', [])
            for script in first_logon_scripts:
                if script.get('command'):
                    self._add_command(first_logon, command_order,
                        script['command'],
                        script.get('description', 'Custom script'))
                    command_order += 1
        
        # 旧形式のカスタムコマンドもサポート
        custom_commands = config.get('first_logon_commands', [])
        for cmd in custom_commands:
            self._add_command(first_logon, command_order,
                cmd.get('command', ''),
                cmd.get('description', 'Custom command'))
            command_order += 1
        
        # 22. WDAC設定 (Windows Defender Application Control)
        wdac = config.get('wdac', {})
        if wdac and wdac.get('enabled'):
            policy_mode = wdac.get('policy_mode', 'Audit')
            
            # WDAC基本ポリシーの作成
            wdac_cmd = 'powershell -Command "'
            wdac_cmd += '$PolicyPath = "$env:TEMP\\WDACPolicy.xml"; '
            wdac_cmd += 'New-CIPolicy -Level Publisher -FilePath $PolicyPath -UserPEs; '
            
            if wdac.get('allow_microsoft_apps'):
                wdac_cmd += 'Set-RuleOption -FilePath $PolicyPath -Option 8; '  # Allow Microsoft apps
            
            if wdac.get('allow_store_apps'):
                wdac_cmd += 'Set-RuleOption -FilePath $PolicyPath -Option 9; '  # Allow Store apps
            
            if policy_mode == 'Audit':
                wdac_cmd += 'Set-RuleOption -FilePath $PolicyPath -Option 3; '  # Audit mode
            elif policy_mode == 'Enforce':
                wdac_cmd += 'Set-RuleOption -FilePath $PolicyPath -Option 0 -Delete; '  # Enforce mode
            
            wdac_cmd += 'ConvertFrom-CIPolicy -XmlFilePath $PolicyPath -BinaryFilePath $env:windir\\System32\\CodeIntegrity\\SIPolicy.p7b"'
            
            self._add_command(first_logon, command_order,
                wdac_cmd,
                f'Configure WDAC in {policy_mode} mode')
            command_order += 1
            
            # WDAC有効化
            self._add_command(first_logon, command_order,
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard\\Scenarios\\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 1 /f',
                'Enable WDAC/HVCI')
            command_order += 1
        
        # 23. その他のコンポーネント
        # Config processorがroot levelに配置しているので直接取得
        if config.get('enable_dotnet35'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:NetFx3 /all /norestart',
                    'Enable .NET Framework 3.5')
                command_order += 1
            
        if config.get('enable_dotnet48'):
                # .NET 4.8は通常プリインストールされているが、念のため
                self._add_command(first_logon, command_order,
                    'powershell -Command "if (-not (Get-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full\' -Name Release -ErrorAction SilentlyContinue).Release -ge 528040) { Write-Host \'.NET 4.8 not installed\' }"',
                    'Check .NET Framework 4.8')
                command_order += 1
            
        if config.get('enable_iis'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:IIS-WebServerRole /featurename:IIS-WebServer /all /norestart',
                    'Enable IIS')
                command_order += 1
            
        if config.get('enable_telnet_client'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:TelnetClient /all /norestart',
                    'Enable Telnet Client')
                command_order += 1
            
        if config.get('enable_tftp_client'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:TFTP /all /norestart',
                    'Enable TFTP Client')
                command_order += 1
            
        if config.get('enable_smb1'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:SMB1Protocol /all /norestart',
                    'Enable SMB 1.0')
                command_order += 1
            
        if config.get('enable_powershell2'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:MicrosoftWindowsPowerShellV2 /all /norestart',
                    'Enable PowerShell 2.0')
                command_order += 1
            
        if config.get('enable_directplay'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:DirectPlay /all /norestart',
                    'Enable DirectPlay')
                command_order += 1
            
        if config.get('enable_print_to_pdf'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:Printing-PrintToPDFServices-Features /all /norestart',
                    'Enable Print to PDF')
                command_order += 1
            
        if config.get('enable_xps_viewer'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:Xps-Foundation-Xps-Viewer /all /norestart',
                    'Enable XPS Viewer')
                command_order += 1
            
        if config.get('enable_media_features'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:MediaPlayback /all /norestart',
                    'Enable Media Features')
                command_order += 1
            
        if config.get('enable_work_folders'):
                self._add_command(first_logon, command_order,
                    'dism /online /enable-feature /featurename:WorkFolders-Client /all /norestart',
                    'Enable Work Folders')
                command_order += 1
    
    def _add_command(self, parent: ET.Element, order: int, command: str, description: str):
        """FirstLogonCommandsにコマンドを追加"""
        sync_command = ET.SubElement(parent, 'SynchronousCommand')
        ET.SubElement(sync_command, 'Order').text = str(order)
        ET.SubElement(sync_command, 'CommandLine').text = command
        ET.SubElement(sync_command, 'Description').text = description
        ET.SubElement(sync_command, 'RequiresUserInput').text = 'false'
    
    def _add_remove_apps(self, settings: ET.Element, config: Dict[str, Any]):
        """不要なアプリの削除（FirstLogonCommandsで処理済み）"""
        # この処理は_build_comprehensive_first_logon_commandsに統合されました
        pass
    
    def _add_explorer_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """エクスプローラー設定"""
        explorer = config.get('explorer_settings', {})
        
        if explorer:
            # レジストリ設定として実装
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-Shell-Setup',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            # エクスプローラー設定はレジストリで設定
            # FirstLogonCommandsで設定することも可能
    
    def _add_system_tweaks(self, settings: ET.Element, config: Dict[str, Any]):
        """システム調整"""
        tweaks = config.get('system_tweaks', {})
        
        if tweaks:
            # システム調整はレジストリやサービス設定で実装
            pass
    
    def _add_visual_effects(self, settings: ET.Element, config: Dict[str, Any]):
        """視覚効果設定"""
        visual = config.get('visual_effects', {})
        
        if visual:
            # 視覚効果はレジストリで設定
            pass
    
    def _add_desktop_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """デスクトップ設定"""
        desktop = config.get('desktop_settings', {})
        icons = config.get('desktop_icons', {})
        
        if desktop or icons:
            # デスクトップ設定はレジストリで設定
            pass
    
    def _add_start_taskbar_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """スタート/タスクバー設定"""
        start_taskbar = config.get('start_taskbar', {})
        
        if start_taskbar:
            # スタートメニューとタスクバーはレジストリで設定
            pass
    
    def _add_vm_features(self, settings: ET.Element, config: Dict[str, Any]):
        """仮想マシンサポート機能"""
        vm = config.get('vm_support', {})
        
        if vm and any(vm.values()):
            component = ET.SubElement(
                settings,
                'component',
                name='Microsoft-Windows-ServerManager-SvrMgrNc',
                processorArchitecture=config.get('architecture', 'amd64'),
                publicKeyToken='31bf3856ad364e35',
                language='neutral',
                versionScope='nonSxS'
            )
            
            # Windows機能の有効化
            if vm.get('enable_hyperv'):
                # Hyper-V有効化のコマンド
                pass
    
    def _add_express_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """Express Settings（プライバシー設定）"""
        express = config.get('express_settings', {})
        
        if express:
            # プライバシー設定はOOBEで設定
            pass
    
    def _add_lock_keys(self, settings: ET.Element, config: Dict[str, Any]):
        """ロックキー設定"""
        lock_keys = config.get('lock_keys', {})
        
        if lock_keys:
            # ロックキーはレジストリで設定
            pass
    
    def _add_sticky_keys(self, settings: ET.Element, config: Dict[str, Any]):
        """固定キー設定"""
        sticky = config.get('sticky_keys', {})
        
        if sticky:
            # 固定キーはアクセシビリティ設定で設定
            pass
    
    def _add_personalization(self, settings: ET.Element, config: Dict[str, Any]):
        """個人用設定"""
        personal = config.get('personalization', {})
        
        if personal:
            # 個人用設定はレジストリで設定
            pass
    
    def _add_wdac_settings(self, settings: ET.Element, config: Dict[str, Any]):
        """WDAC設定"""
        wdac = config.get('wdac', {})
        
        if wdac and wdac.get('enabled'):
            # WDACポリシー設定
            pass
    
    def _add_additional_components(self, settings: ET.Element, config: Dict[str, Any]):
        """その他のコンポーネント"""
        # Windows機能の有効化
        if config.get('enable_dotnet35'):
            # .NET Framework 3.5の有効化
            pass
        
        if config.get('enable_iis'):
            # IISの有効化
            pass
    
    def _encode_password(self, password: str) -> str:
        """パスワードをBase64エンコード（Windows形式）"""
        if not password:
            password = "password"
        
        # Windowsのunattend.xmlでは "Password" サフィックスを追加
        password_with_suffix = password + "Password"
        
        # UTF-16LEでエンコード
        password_bytes = password_with_suffix.encode('utf-16le')
        
        # Base64エンコード
        return base64.b64encode(password_bytes).decode('ascii')
    
    def _prettify_xml(self, element: ET.Element) -> str:
        """XMLを整形して文字列に変換"""
        from xml.dom import minidom
        
        rough_string = ET.tostring(element, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # XML宣言を追加
        return reparsed.toprettyxml(indent='    ', encoding='utf-8').decode('utf-8')