"""
ユーザーアカウント管理モジュールのテスト
"""

import pytest
import asyncio
from lxml import etree
from src.modules.user_management import (
    UserAccount,
    UserGroup,
    UserAccountManager,
    UserAccountAgent
)


class TestUserAccount:
    """UserAccountクラスのテスト"""
    
    def test_user_account_creation(self):
        """ユーザーアカウント作成のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            description="Test Account",
            groups=[UserGroup.ADMINISTRATORS],
            password="TestP@ss123!"
        )
        
        assert user.name == "test-user"
        assert user.display_name == "Test User"
        assert UserGroup.ADMINISTRATORS in user.groups
        assert user.encrypted_password is not None
        assert user.password_never_expires is True
    
    def test_password_encryption(self):
        """パスワード暗号化のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            password="TestP@ss123!"
        )
        
        # パスワードが暗号化されていることを確認
        assert user.encrypted_password != "TestP@ss123!"
        assert len(user.encrypted_password) > 0
    
    def test_to_xml_element(self):
        """XML要素への変換テスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            groups=[UserGroup.ADMINISTRATORS],
            password="TestP@ss123!"
        )
        
        xml_elem = user.to_xml_element()
        
        assert xml_elem.tag == "LocalAccount"
        assert xml_elem.find("Name").text == "test-user"
        assert xml_elem.find("DisplayName").text == "Test User"
        assert xml_elem.find("Group").text == "Administrators"


class TestUserAccountManager:
    """UserAccountManagerクラスのテスト"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.manager = UserAccountManager()
    
    def test_add_account(self):
        """アカウント追加のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            password="TestP@ss123!"
        )
        
        self.manager.add_account(user)
        assert len(self.manager.accounts) == 1
        assert self.manager.accounts[0].name == "test-user"
    
    def test_validate_account_invalid_name(self):
        """無効なユーザー名の検証テスト"""
        # 予約された名前
        user = UserAccount(
            name="CON",
            display_name="Invalid User",
            password="TestP@ss123!"
        )
        
        with pytest.raises(ValueError):
            self.manager.add_account(user)
    
    def test_validate_password(self):
        """パスワードポリシー検証のテスト"""
        # 弱いパスワード
        assert self.manager._validate_password("weak") is False
        
        # 文字数不足
        assert self.manager._validate_password("Sh0rt!") is False
        
        # 強いパスワード
        assert self.manager._validate_password("StrongP@ssw0rd123!") is True
    
    def test_disable_administrator(self):
        """Administrator無効化のテスト"""
        self.manager.disable_administrator()
        assert self.manager.administrator_disabled is True
    
    def test_set_autologon(self):
        """自動ログオン設定のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            password="TestP@ss123!"
        )
        
        self.manager.add_account(user)
        self.manager.set_autologon(user, count=2)
        
        assert self.manager.autologon_user == user
        assert self.manager.autologon_count == 2
    
    def test_generate_xml(self):
        """XML生成のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            groups=[UserGroup.ADMINISTRATORS],
            password="TestP@ss123!"
        )
        
        self.manager.add_account(user)
        self.manager.disable_administrator()
        
        xml_elem = self.manager.generate_xml()
        
        assert xml_elem.tag == "UserAccounts"
        assert xml_elem.find(".//LocalAccount") is not None
        assert xml_elem.find("AdministratorPassword") is not None
    
    def test_generate_autologon_xml(self):
        """自動ログオンXML生成のテスト"""
        user = UserAccount(
            name="test-user",
            display_name="Test User",
            password="TestP@ss123!"
        )
        
        self.manager.add_account(user)
        self.manager.set_autologon(user, count=1)
        
        autologon_xml = self.manager.generate_autologon_xml()
        
        assert autologon_xml is not None
        assert autologon_xml.tag == "AutoLogon"
        assert autologon_xml.find("Username").text == "test-user"
        assert autologon_xml.find("Enabled").text == "true"
        assert autologon_xml.find("LogonCount").text == "1"


@pytest.mark.asyncio
class TestUserAccountAgent:
    """UserAccountAgentクラスのテスト"""
    
    async def test_create_user(self):
        """非同期ユーザー作成のテスト"""
        manager = UserAccountManager()
        agent = UserAccountAgent(manager)
        
        user_config = {
            "name": "async-user",
            "display_name": "Async User",
            "description": "Async Test User",
            "groups": ["Administrators"],
            "password": "AsyncP@ss123!",
            "password_never_expires": True
        }
        
        account = await agent.create_user(user_config)
        
        assert account.name == "async-user"
        assert len(manager.accounts) == 1
        assert manager.accounts[0] == account
    
    async def test_validate_all_accounts(self):
        """全アカウント検証のテスト"""
        manager = UserAccountManager()
        agent = UserAccountAgent(manager)
        
        # 有効なアカウントを追加
        user = UserAccount(
            name="valid-user",
            display_name="Valid User",
            password="ValidP@ss123!"
        )
        manager.add_account(user)
        
        is_valid = await agent.validate_all_accounts()
        assert is_valid is True
    
    async def test_generate_password(self):
        """パスワード生成のテスト"""
        manager = UserAccountManager()
        agent = UserAccountAgent(manager)
        
        password = await agent.generate_password(16)
        
        assert len(password) == 16
        assert manager._validate_password(password) is True
        
        # 複数回生成して異なることを確認
        password2 = await agent.generate_password(16)
        assert password != password2


@pytest.fixture
def sample_users():
    """サンプルユーザーのフィクスチャ"""
    return [
        UserAccount(
            name="mirai-user",
            display_name="Mirai User",
            description="Mirai User Account",
            groups=[UserGroup.ADMINISTRATORS],
            password="MiraiP@ss2024!"
        ),
        UserAccount(
            name="l-admin",
            display_name="Local Admin",
            description="Local Administrator Account",
            groups=[UserGroup.ADMINISTRATORS],
            password="LAdminP@ss2024!"
        )
    ]


def test_integration_scenario(sample_users):
    """統合シナリオテスト"""
    manager = UserAccountManager()
    
    # ユーザー追加
    for user in sample_users:
        manager.add_account(user)
    
    # Administrator無効化
    manager.disable_administrator()
    
    # 自動ログオン設定
    manager.set_autologon(sample_users[0], count=1)
    
    # XML生成
    xml_elem = manager.generate_xml()
    autologon_xml = manager.generate_autologon_xml()
    
    # XML検証
    assert xml_elem.tag == "UserAccounts"
    assert len(xml_elem.findall(".//LocalAccount")) == 2
    assert autologon_xml.find("Username").text == "mirai-user"
    
    # コマンド生成
    commands = manager.get_first_logon_commands()
    assert len(commands) > 0
    assert any("Administrator" in cmd["command"] for cmd in commands)