"""
ドメイン管理関連SubAgent群

Active Directory参加、グループポリシー、DNS設定などを管理する
5つの専門的なSubAgentを提供します。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from .base_agent import BaseAgent, AgentPriority
from lxml import etree


class DomainJoinAgent(BaseAgent):
    """ドメイン参加を管理するAgent"""
    
    def __init__(self):
        super().__init__("DomainJoinAgent", AgentPriority.HIGH)
        self.domain_config = {
            "domain_name": None,
            "ou_path": None,
            "domain_admin": None,
            "domain_password": None,
            "join_options": 3  # ドメイン参加とコンピューターアカウント作成
        }
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ドメイン参加設定を実行"""
        self.logger.info("ドメイン参加設定開始")
        
        config = context.get("domain", {})
        
        # ドメイン設定を更新
        if config.get("domain_name"):
            self.domain_config["domain_name"] = config["domain_name"]
            self.domain_config["ou_path"] = config.get("ou_path", "")
            self.domain_config["domain_admin"] = config.get("admin_user")
            self.domain_config["domain_password"] = config.get("admin_password")
        
        # XML要素を生成
        domain_element = self._generate_domain_xml()
        
        # PowerShellコマンドを生成
        commands = self._generate_join_commands()
        
        result = {
            "xml_element": domain_element,
            "commands": commands,
            "domain_name": self.domain_config["domain_name"],
            "ou_path": self.domain_config["ou_path"]
        }
        
        self.logger.info(f"ドメイン参加設定完了: {self.domain_config['domain_name']}")
        return result
    
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """ドメイン設定の検証"""
        errors = []
        config = context.get("domain", {})
        
        if config.get("enable_domain_join"):
            if not config.get("domain_name"):
                errors.append("ドメイン名が指定されていません")
            if not config.get("admin_user"):
                errors.append("ドメイン管理者ユーザーが指定されていません")
            if not config.get("admin_password"):
                errors.append("ドメイン管理者パスワードが指定されていません")
        
        return len(errors) == 0, errors
    
    def _generate_domain_xml(self) -> Optional[etree.Element]:
        """ドメイン参加用XML要素を生成"""
        if not self.domain_config["domain_name"]:
            return None
        
        identification = etree.Element("Identification")
        
        # ドメイン参加設定
        join_domain = etree.SubElement(identification, "JoinDomain")
        join_domain.text = self.domain_config["domain_name"]
        
        # OU指定（オプション）
        if self.domain_config["ou_path"]:
            machine_object_ou = etree.SubElement(identification, "MachineObjectOU")
            machine_object_ou.text = self.domain_config["ou_path"]
        
        # 認証情報
        if self.domain_config["domain_admin"]:
            credentials = etree.SubElement(identification, "Credentials")
            
            domain_elem = etree.SubElement(credentials, "Domain")
            domain_elem.text = self.domain_config["domain_name"]
            
            username = etree.SubElement(credentials, "Username")
            username.text = self.domain_config["domain_admin"]
            
            password = etree.SubElement(credentials, "Password")
            password.text = self.domain_config["domain_password"]
        
        return identification
    
    def _generate_join_commands(self) -> List[Dict[str, Any]]:
        """ドメイン参加コマンドを生成"""
        commands = []
        
        if self.domain_config["domain_name"]:
            # ドメイン参加コマンド
            join_cmd = f"""
            $domain = '{self.domain_config["domain_name"]}'
            $username = '{self.domain_config["domain_admin"]}'
            $password = ConvertTo-SecureString '{self.domain_config["domain_password"]}' -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential($username, $password)
            """
            
            if self.domain_config["ou_path"]:
                join_cmd += f"Add-Computer -DomainName $domain -OUPath '{self.domain_config['ou_path']}' -Credential $credential -Force"
            else:
                join_cmd += "Add-Computer -DomainName $domain -Credential $credential -Force"
            
            commands.append({
                "order": 100,
                "command": join_cmd,
                "description": f"ドメイン {self.domain_config['domain_name']} への参加",
                "shell": "powershell",
                "requires_restart": True
            })
        
        return commands


class GroupPolicyAgent(BaseAgent):
    """グループポリシー設定を管理するAgent"""
    
    def __init__(self):
        super().__init__("GroupPolicyAgent", AgentPriority.NORMAL)
        self.gpo_settings = {}
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """グループポリシー設定を実行"""
        self.logger.info("グループポリシー設定開始")
        
        gpo_config = context.get("group_policy", {})
        
        # 各種GPO設定
        commands = []
        
        # Windows Update設定
        if gpo_config.get("disable_auto_update"):
            commands.append({
                "order": 201,
                "command": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoUpdate /t REG_DWORD /d 1 /f',
                "description": "Windows自動更新の無効化",
                "shell": "cmd"
            })
        
        # Windows Defender設定
        if gpo_config.get("configure_defender"):
            commands.append({
                "order": 202,
                "command": 'Set-MpPreference -DisableRealtimeMonitoring $false -DisableBehaviorMonitoring $false',
                "description": "Windows Defenderリアルタイム保護の設定",
                "shell": "powershell"
            })
        
        # ユーザーアカウント制御（UAC）
        if gpo_config.get("configure_uac"):
            uac_level = gpo_config.get("uac_level", 2)
            commands.append({
                "order": 203,
                "command": f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v ConsentPromptBehaviorAdmin /t REG_DWORD /d {uac_level} /f',
                "description": "UAC設定の構成",
                "shell": "cmd"
            })
        
        # リモートデスクトップ設定
        if gpo_config.get("enable_rdp"):
            commands.extend([
                {
                    "order": 204,
                    "command": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f',
                    "description": "リモートデスクトップの有効化",
                    "shell": "cmd"
                },
                {
                    "order": 205,
                    "command": 'netsh advfirewall firewall set rule group="remote desktop" new enable=Yes',
                    "description": "リモートデスクトップのファイアウォール規則設定",
                    "shell": "cmd"
                }
            ])
        
        # パスワードポリシー
        if gpo_config.get("password_policy"):
            policy = gpo_config["password_policy"]
            if policy.get("complexity"):
                commands.append({
                    "order": 206,
                    "command": 'net accounts /MINPWLEN:8 /UNIQUEPW:5',
                    "description": "パスワードポリシーの設定",
                    "shell": "cmd"
                })
        
        result = {
            "commands": commands,
            "settings_count": len(commands),
            "gpo_config": gpo_config
        }
        
        self.logger.info(f"グループポリシー設定完了: {len(commands)}個の設定")
        return result
    
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """グループポリシー設定の検証"""
        errors = []
        gpo_config = context.get("group_policy", {})
        
        # UAC設定の検証
        if gpo_config.get("configure_uac"):
            uac_level = gpo_config.get("uac_level", 2)
            if uac_level not in [0, 1, 2, 3, 4]:
                errors.append(f"無効なUACレベル: {uac_level}")
        
        return len(errors) == 0, errors


class DNSConfigAgent(BaseAgent):
    """DNS設定を管理するAgent"""
    
    def __init__(self):
        super().__init__("DNSConfigAgent", AgentPriority.HIGH)
        self.dns_servers = []
        self.dns_suffix = None
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """DNS設定を実行"""
        self.logger.info("DNS設定開始")
        
        network_config = context.get("network", {})
        dns_config = network_config.get("dns", {})
        
        commands = []
        
        # DNSサーバー設定
        if dns_config.get("servers"):
            self.dns_servers = dns_config["servers"]
            primary_dns = self.dns_servers[0] if self.dns_servers else "8.8.8.8"
            secondary_dns = self.dns_servers[1] if len(self.dns_servers) > 1 else "8.8.4.4"
            
            commands.append({
                "order": 301,
                "command": f'netsh interface ipv4 set dnsservers "Ethernet" static {primary_dns} primary validate=no',
                "description": f"プライマリDNSサーバー設定: {primary_dns}",
                "shell": "cmd"
            })
            
            if secondary_dns:
                commands.append({
                    "order": 302,
                    "command": f'netsh interface ipv4 add dnsservers "Ethernet" {secondary_dns} index=2 validate=no',
                    "description": f"セカンダリDNSサーバー設定: {secondary_dns}",
                    "shell": "cmd"
                })
        
        # DNSサフィックス設定
        if dns_config.get("suffix"):
            self.dns_suffix = dns_config["suffix"]
            commands.append({
                "order": 303,
                "command": f'netsh interface ipv4 set dnsservers "Ethernet" suffix {self.dns_suffix}',
                "description": f"DNSサフィックス設定: {self.dns_suffix}",
                "shell": "cmd"
            })
        
        # DNS登録設定
        if dns_config.get("register_in_dns", True):
            commands.append({
                "order": 304,
                "command": 'netsh interface ipv4 set dnsservers "Ethernet" register=PRIMARY',
                "description": "DNSへの自動登録有効化",
                "shell": "cmd"
            })
        
        # DNSキャッシュクリア
        commands.append({
            "order": 305,
            "command": 'ipconfig /flushdns',
            "description": "DNSキャッシュのクリア",
            "shell": "cmd"
        })
        
        result = {
            "commands": commands,
            "dns_servers": self.dns_servers,
            "dns_suffix": self.dns_suffix
        }
        
        self.logger.info(f"DNS設定完了: サーバー {self.dns_servers}")
        return result
    
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """DNS設定の検証"""
        errors = []
        dns_config = context.get("network", {}).get("dns", {})
        
        # DNSサーバーの検証
        if dns_config.get("servers"):
            for server in dns_config["servers"]:
                if not self._is_valid_ip(server):
                    errors.append(f"無効なDNSサーバーアドレス: {server}")
        
        return len(errors) == 0, errors
    
    def _is_valid_ip(self, ip: str) -> bool:
        """IPアドレスの妥当性チェック"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False


class CredentialManagerAgent(BaseAgent):
    """資格情報管理を行うAgent"""
    
    def __init__(self):
        super().__init__("CredentialManagerAgent", AgentPriority.HIGH)
        self.credentials = []
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """資格情報の設定を実行"""
        self.logger.info("資格情報管理開始")
        
        cred_config = context.get("credentials", {})
        commands = []
        
        # Windows資格情報の追加
        if cred_config.get("windows_credentials"):
            for cred in cred_config["windows_credentials"]:
                target = cred.get("target")
                username = cred.get("username")
                password = cred.get("password")
                
                if target and username and password:
                    commands.append({
                        "order": 401,
                        "command": f'cmdkey /add:{target} /user:{username} /pass:{password}',
                        "description": f"Windows資格情報の追加: {target}",
                        "shell": "cmd"
                    })
                    self.credentials.append({"type": "windows", "target": target})
        
        # 汎用資格情報の追加
        if cred_config.get("generic_credentials"):
            for cred in cred_config["generic_credentials"]:
                target = cred.get("target")
                username = cred.get("username")
                password = cred.get("password")
                
                if target and username and password:
                    commands.append({
                        "order": 402,
                        "command": f'cmdkey /generic:{target} /user:{username} /pass:{password}',
                        "description": f"汎用資格情報の追加: {target}",
                        "shell": "cmd"
                    })
                    self.credentials.append({"type": "generic", "target": target})
        
        # 証明書のインポート
        if cred_config.get("certificates"):
            for cert in cred_config["certificates"]:
                cert_path = cert.get("path")
                store = cert.get("store", "LocalMachine\\My")
                
                if cert_path:
                    commands.append({
                        "order": 403,
                        "command": f'certutil -addstore {store} "{cert_path}"',
                        "description": f"証明書のインポート: {cert_path}",
                        "shell": "cmd"
                    })
        
        result = {
            "commands": commands,
            "credentials_count": len(self.credentials),
            "credentials": self.credentials
        }
        
        self.logger.info(f"資格情報管理完了: {len(self.credentials)}個の資格情報")
        return result
    
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """資格情報設定の検証"""
        errors = []
        cred_config = context.get("credentials", {})
        
        # Windows資格情報の検証
        if cred_config.get("windows_credentials"):
            for cred in cred_config["windows_credentials"]:
                if not cred.get("target"):
                    errors.append("Windows資格情報のターゲットが指定されていません")
                if not cred.get("username"):
                    errors.append("Windows資格情報のユーザー名が指定されていません")
        
        return len(errors) == 0, errors


class DirectoryServiceAgent(BaseAgent):
    """ディレクトリサービス設定を管理するAgent"""
    
    def __init__(self):
        super().__init__("DirectoryServiceAgent", AgentPriority.NORMAL)
        self.ldap_config = {}
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ディレクトリサービス設定を実行"""
        self.logger.info("ディレクトリサービス設定開始")
        
        ds_config = context.get("directory_service", {})
        commands = []
        
        # LDAP設定
        if ds_config.get("ldap"):
            ldap = ds_config["ldap"]
            self.ldap_config = {
                "server": ldap.get("server"),
                "port": ldap.get("port", 389),
                "base_dn": ldap.get("base_dn"),
                "bind_dn": ldap.get("bind_dn"),
                "use_ssl": ldap.get("use_ssl", False)
            }
            
            # LDAP接続設定
            if self.ldap_config["server"]:
                commands.append({
                    "order": 501,
                    "command": f'''
                    $ldapServer = "{self.ldap_config['server']}"
                    $ldapPort = {self.ldap_config['port']}
                    $baseDN = "{self.ldap_config['base_dn']}"
                    New-ItemProperty -Path "HKLM:\\Software\\Policies\\Microsoft\\Windows\\LDAP" -Name "Server" -Value $ldapServer -Force
                    New-ItemProperty -Path "HKLM:\\Software\\Policies\\Microsoft\\Windows\\LDAP" -Name "Port" -Value $ldapPort -Force
                    New-ItemProperty -Path "HKLM:\\Software\\Policies\\Microsoft\\Windows\\LDAP" -Name "BaseDN" -Value $baseDN -Force
                    ''',
                    "description": f"LDAP設定: {self.ldap_config['server']}",
                    "shell": "powershell"
                })
        
        # Active Directory LDS設定
        if ds_config.get("ad_lds"):
            ad_lds = ds_config["ad_lds"]
            if ad_lds.get("enable"):
                commands.append({
                    "order": 502,
                    "command": 'dism /online /enable-feature /featurename:DirectoryServices-ADAM-Client',
                    "description": "AD LDSクライアントの有効化",
                    "shell": "cmd"
                })
        
        # ディレクトリ同期設定
        if ds_config.get("sync"):
            sync = ds_config["sync"]
            if sync.get("enable"):
                interval = sync.get("interval", 3600)
                commands.append({
                    "order": 503,
                    "command": f'schtasks /create /tn "DirectorySync" /tr "powershell -command Sync-Directory" /sc minute /mo {interval // 60}',
                    "description": f"ディレクトリ同期タスクの作成（{interval}秒間隔）",
                    "shell": "cmd"
                })
        
        result = {
            "commands": commands,
            "ldap_config": self.ldap_config,
            "settings_count": len(commands)
        }
        
        self.logger.info(f"ディレクトリサービス設定完了: {len(commands)}個の設定")
        return result
    
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """ディレクトリサービス設定の検証"""
        errors = []
        ds_config = context.get("directory_service", {})
        
        # LDAP設定の検証
        if ds_config.get("ldap"):
            ldap = ds_config["ldap"]
            if not ldap.get("server"):
                errors.append("LDAPサーバーが指定されていません")
            if not ldap.get("base_dn"):
                errors.append("LDAP Base DNが指定されていません")
            
            port = ldap.get("port", 389)
            if not (1 <= port <= 65535):
                errors.append(f"無効なLDAPポート番号: {port}")
        
        return len(errors) == 0, errors