"""
ユーザーアカウント管理モジュール

Windows 11のunattend.xmlファイル用のユーザーアカウント設定を生成します。
"""

import base64
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from lxml import etree

logger = logging.getLogger(__name__)


class UserGroup(Enum):
    """ユーザーグループの定義"""
    ADMINISTRATORS = "Administrators"
    USERS = "Users"
    POWER_USERS = "Power Users"
    GUESTS = "Guests"
    REMOTE_DESKTOP_USERS = "Remote Desktop Users"


@dataclass
class UserAccount:
    """ユーザーアカウントのデータクラス"""
    name: str
    display_name: str
    description: str = ""
    groups: List[UserGroup] = field(default_factory=lambda: [UserGroup.USERS])
    password: Optional[str] = None
    encrypted_password: Optional[str] = None
    password_never_expires: bool = True
    account_never_expires: bool = True
    change_password_at_logon: bool = False
    enabled: bool = True
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.password and not self.encrypted_password:
            self.encrypted_password = self._encrypt_password(self.password)
    
    def _encrypt_password(self, password: str) -> str:
        """
        パスワードを暗号化（Windows互換形式）
        
        注: 実際のWindows環境では、より安全な暗号化が必要です。
        これは例示的な実装です。
        """
        # Base64エンコード（実際はWindows DPAPIを使用すべき）
        encoded = base64.b64encode(password.encode('utf-16-le')).decode('ascii')
        return encoded
    
    def to_xml_element(self, namespace: Optional[str] = None) -> etree.Element:
        """XMLエレメントへの変換"""
        ns = {"wcm": "http://schemas.microsoft.com/WMIConfig/2002/State"} if namespace else {}
        
        account_elem = etree.Element("LocalAccount")
        if namespace:
            account_elem.set("{http://schemas.microsoft.com/WMIConfig/2002/State}action", "add")
        
        # パスワード設定
        password_elem = etree.SubElement(account_elem, "Password")
        value_elem = etree.SubElement(password_elem, "Value")
        value_elem.text = self.encrypted_password or ""
        plain_elem = etree.SubElement(password_elem, "PlainText")
        plain_elem.text = "false" if self.encrypted_password else "true"
        
        # アカウント情報
        if self.description:
            desc_elem = etree.SubElement(account_elem, "Description")
            desc_elem.text = self.description
        
        display_elem = etree.SubElement(account_elem, "DisplayName")
        display_elem.text = self.display_name
        
        # グループ設定
        for group in self.groups:
            group_elem = etree.SubElement(account_elem, "Group")
            group_elem.text = group.value
        
        # アカウント名
        name_elem = etree.SubElement(account_elem, "Name")
        name_elem.text = self.name
        
        return account_elem


class UserAccountManager:
    """ユーザーアカウント管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.accounts: List[UserAccount] = []
        self.administrator_disabled = False
        self.autologon_user: Optional[UserAccount] = None
        self.autologon_count: int = 1
    
    def add_account(self, account: UserAccount) -> None:
        """アカウントを追加"""
        if self._validate_account(account):
            self.accounts.append(account)
            logger.info(f"アカウント追加: {account.name}")
        else:
            logger.error(f"アカウント検証失敗: {account.name}")
            raise ValueError(f"Invalid account: {account.name}")
    
    def _validate_account(self, account: UserAccount) -> bool:
        """アカウントの検証"""
        # ユーザー名の検証
        if not account.name or len(account.name) > 20:
            logger.error("ユーザー名が無効です")
            return False
        
        # 予約されたユーザー名のチェック
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        if account.name.upper() in reserved_names:
            logger.error(f"予約されたユーザー名: {account.name}")
            return False
        
        # パスワードの検証（設定されている場合）
        if account.password and not self._validate_password(account.password):
            logger.error("パスワードが要件を満たしていません")
            return False
        
        return True
    
    def _validate_password(self, password: str) -> bool:
        """パスワードポリシーの検証"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def disable_administrator(self) -> None:
        """Administratorアカウントを無効化"""
        self.administrator_disabled = True
        logger.info("Administratorアカウントを無効化設定")
    
    def set_autologon(self, user: UserAccount, count: int = 1) -> None:
        """自動ログオンの設定"""
        if user not in self.accounts:
            raise ValueError(f"User {user.name} not in accounts list")
        
        self.autologon_user = user
        self.autologon_count = count
        logger.info(f"自動ログオン設定: {user.name} (回数: {count})")
    
    def generate_xml(self) -> etree.Element:
        """XML要素の生成"""
        # UserAccounts要素
        user_accounts = etree.Element("UserAccounts")
        
        # LocalAccounts要素
        if self.accounts:
            local_accounts = etree.SubElement(user_accounts, "LocalAccounts")
            for account in self.accounts:
                local_accounts.append(account.to_xml_element(namespace="wcm"))
        
        # AdministratorPassword（無効化用）
        if self.administrator_disabled:
            admin_pwd = etree.SubElement(user_accounts, "AdministratorPassword")
            value = etree.SubElement(admin_pwd, "Value")
            value.text = ""
            plain = etree.SubElement(admin_pwd, "PlainText")
            plain.text = "true"
        
        return user_accounts
    
    def generate_autologon_xml(self) -> Optional[etree.Element]:
        """自動ログオンXMLの生成"""
        if not self.autologon_user:
            return None
        
        autologon = etree.Element("AutoLogon")
        
        # パスワード
        password = etree.SubElement(autologon, "Password")
        value = etree.SubElement(password, "Value")
        value.text = self.autologon_user.password or ""
        plain = etree.SubElement(password, "PlainText")
        plain.text = "true"
        
        # 有効化
        enabled = etree.SubElement(autologon, "Enabled")
        enabled.text = "true"
        
        # ログオン回数
        count = etree.SubElement(autologon, "LogonCount")
        count.text = str(self.autologon_count)
        
        # ユーザー名
        username = etree.SubElement(autologon, "Username")
        username.text = self.autologon_user.name
        
        return autologon
    
    def get_first_logon_commands(self) -> List[Dict[str, Any]]:
        """初回ログオン時のコマンドリストを取得"""
        commands = []
        
        # Administratorアカウント無効化コマンド
        if self.administrator_disabled:
            commands.append({
                "order": 1,
                "command": "net user Administrator /active:no",
                "description": "Disable Administrator account",
                "requires_user_input": False
            })
        
        # パスワード無期限設定
        for i, account in enumerate(self.accounts, start=2):
            if account.password_never_expires:
                commands.append({
                    "order": i,
                    "command": f"wmic useraccount where name='{account.name}' set PasswordExpires=FALSE",
                    "description": f"Set password never expires for {account.name}",
                    "requires_user_input": False
                })
        
        return commands


class UserAccountAgent:
    """ユーザーアカウント管理用SubAgent"""
    
    def __init__(self, manager: UserAccountManager):
        """初期化"""
        self.manager = manager
        self.logger = logging.getLogger(f"{__name__}.Agent")
    
    async def create_user(self, user_config: Dict[str, Any]) -> UserAccount:
        """非同期でユーザーを作成"""
        self.logger.info(f"ユーザー作成開始: {user_config.get('name')}")
        
        # ユーザーグループの解析
        groups = []
        for group_name in user_config.get('groups', ['Users']):
            try:
                groups.append(UserGroup(group_name))
            except ValueError:
                self.logger.warning(f"未知のグループ: {group_name}")
        
        # UserAccountオブジェクトの作成
        account = UserAccount(
            name=user_config['name'],
            display_name=user_config.get('display_name', user_config['name']),
            description=user_config.get('description', ''),
            groups=groups or [UserGroup.USERS],
            password=user_config.get('password'),
            password_never_expires=user_config.get('password_never_expires', True),
            account_never_expires=user_config.get('account_never_expires', True),
            change_password_at_logon=user_config.get('change_password_at_logon', False),
            enabled=user_config.get('enabled', True)
        )
        
        # マネージャーに追加
        self.manager.add_account(account)
        
        self.logger.info(f"ユーザー作成完了: {account.name}")
        return account
    
    async def validate_all_accounts(self) -> bool:
        """すべてのアカウントを検証"""
        self.logger.info("全アカウントの検証開始")
        
        for account in self.manager.accounts:
            if not self.manager._validate_account(account):
                self.logger.error(f"アカウント検証失敗: {account.name}")
                return False
        
        self.logger.info("全アカウントの検証完了")
        return True
    
    async def generate_password(self, length: int = 16) -> str:
        """セキュアなパスワードを生成"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # パスワードポリシーを満たすことを確認
        while not self.manager._validate_password(password):
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return password


# サンプル使用例
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # マネージャーの初期化
        manager = UserAccountManager()
        agent = UserAccountAgent(manager)
        
        # ユーザー設定
        users_config = [
            {
                "name": "mirai-user",
                "display_name": "Mirai User",
                "description": "Mirai User Account",
                "groups": ["Administrators"],
                "password": await agent.generate_password(),
                "password_never_expires": True
            },
            {
                "name": "l-admin",
                "display_name": "Local Admin",
                "description": "Local Administrator Account",
                "groups": ["Administrators"],
                "password": await agent.generate_password(),
                "password_never_expires": True
            }
        ]
        
        # ユーザー作成
        for user_config in users_config:
            await agent.create_user(user_config)
        
        # Administratorアカウントの無効化
        manager.disable_administrator()
        
        # 自動ログオン設定
        if manager.accounts:
            manager.set_autologon(manager.accounts[0], count=1)
        
        # XML生成
        xml_element = manager.generate_xml()
        xml_string = etree.tostring(xml_element, pretty_print=True, encoding='unicode')
        print(xml_string)
        
        # 自動ログオンXML
        autologon_xml = manager.generate_autologon_xml()
        if autologon_xml is not None:
            autologon_string = etree.tostring(autologon_xml, pretty_print=True, encoding='unicode')
            print("\n自動ログオン設定:")
            print(autologon_string)
    
    # 実行
    asyncio.run(main())