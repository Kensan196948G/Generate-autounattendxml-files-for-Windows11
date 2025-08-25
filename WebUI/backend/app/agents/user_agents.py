#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
ユーザー管理エージェント群

ユーザーアカウントの作成、権限設定、グループ管理などを担当する
5つのSubAgentを実装します。
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, XMLGeneratingAgent


class UserCreationAgent(XMLGeneratingAgent):
    """ユーザー作成エージェント
    
    Windows 11のユーザーアカウント作成設定を生成します。
    """
    
    def get_description(self) -> str:
        return "Windows 11システムでのユーザーアカウント作成設定を生成"
    
    def get_supported_tasks(self) -> List[str]:
        return ["user_creation", "local_accounts", "administrator_setup"]
    
    def get_required_inputs(self) -> List[str]:
        return ["users"]
    
    async def _validate_input(self, input_data: Dict[str, Any]) -> None:
        await super()._validate_input(input_data)
        
        if "users" not in input_data:
            raise ValueError("usersフィールドが必要です")
        
        users = input_data["users"]
        if not isinstance(users, list) or len(users) == 0:
            raise ValueError("少なくとも1つのユーザーアカウントが必要です")
        
        for user in users:
            if not isinstance(user, dict):
                raise ValueError("ユーザー情報は辞書形式である必要があります")
            
            if "name" not in user or "password" not in user:
                raise ValueError("ユーザー名とパスワードは必須です")
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー作成XML設定を生成"""
        users = input_data["users"]
        
        local_accounts = []
        administrator_password = None
        
        for user in users:
            user_name = user["name"]
            password = user["password"]
            display_name = user.get("display_name", user_name)
            groups = user.get("groups", ["Users"])
            
            # administratorアカウントの場合は別途処理
            if user_name.lower() == "administrator":
                administrator_password = password
                continue
            
            # 一般ユーザーアカウント設定
            account_config = {
                "name": user_name,
                "password": password,
                "display_name": display_name,
                "group": "Administrators" if "Administrators" in groups else "Users",
                "description": user.get("description", f"{display_name}のアカウント")
            }
            
            local_accounts.append(account_config)
        
        # XML生成用のデータ構造
        xml_data = {
            "local_accounts": local_accounts
        }
        
        if administrator_password:
            xml_data["administrator_password"] = administrator_password
        
        return {
            "xml_content": xml_data,
            "xml_section": "oobeSystem",
            "description": f"{len(local_accounts)}個のローカルアカウントを作成",
            "accounts_created": [acc["name"] for acc in local_accounts]
        }


class UserPermissionAgent(XMLGeneratingAgent):
    """ユーザー権限設定エージェント
    
    ユーザーアカウントの詳細な権限設定を生成します。
    """
    
    def get_description(self) -> str:
        return "ユーザーアカウントの詳細権限設定を生成"
    
    def get_supported_tasks(self) -> List[str]:
        return ["user_permissions", "user_rights", "privilege_settings"]
    
    def get_required_inputs(self) -> List[str]:
        return ["users"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザー権限設定XML生成"""
        users = input_data["users"]
        
        permission_settings = []
        
        for user in users:
            user_name = user["name"]
            groups = user.get("groups", ["Users"])
            
            # 管理者権限設定
            if "Administrators" in groups:
                permission_settings.extend([
                    {
                        "type": "UserRightAssignment",
                        "policy": "SeServiceLogonRight",
                        "user": user_name,
                        "description": "サービスとしてログオン権限"
                    },
                    {
                        "type": "UserRightAssignment", 
                        "policy": "SeBackupPrivilege",
                        "user": user_name,
                        "description": "ファイルとディレクトリのバックアップ権限"
                    },
                    {
                        "type": "UserRightAssignment",
                        "policy": "SeRestorePrivilege", 
                        "user": user_name,
                        "description": "ファイルとディレクトリの復元権限"
                    }
                ])
            
            # パワーユーザー権限設定
            if "Power Users" in groups:
                permission_settings.append({
                    "type": "UserRightAssignment",
                    "policy": "SeShutdownPrivilege",
                    "user": user_name,
                    "description": "システムのシャットダウン権限"
                })
            
            # 自動ログオン設定
            if user.get("auto_logon", False):
                permission_settings.append({
                    "type": "AutoLogon",
                    "user": user_name,
                    "password": user["password"],
                    "description": "自動ログオン設定"
                })
        
        return {
            "xml_content": {
                "permission_settings": permission_settings
            },
            "xml_section": "specialize",
            "description": f"{len(permission_settings)}個の権限設定を生成",
            "permissions_count": len(permission_settings)
        }


class UserGroupAgent(XMLGeneratingAgent):
    """ユーザーグループ管理エージェント
    
    ユーザーのグループ所属とグループ権限設定を管理します。
    """
    
    def get_description(self) -> str:
        return "ユーザーグループの所属とグループ権限設定を管理"
    
    def get_supported_tasks(self) -> List[str]:
        return ["user_groups", "group_membership", "group_policies"]
    
    def get_required_inputs(self) -> List[str]:
        return ["users"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ユーザーグループ設定XML生成"""
        users = input_data["users"]
        
        group_memberships = {}
        
        # ユーザーをグループごとに分類
        for user in users:
            user_name = user["name"]
            groups = user.get("groups", ["Users"])
            
            for group in groups:
                if group not in group_memberships:
                    group_memberships[group] = []
                group_memberships[group].append(user_name)
        
        group_settings = []
        
        # グループごとの設定生成
        for group_name, members in group_memberships.items():
            group_config = {
                "group_name": group_name,
                "members": members,
                "description": f"{group_name}グループのメンバー設定"
            }
            
            # グループ特有の設定
            if group_name == "Administrators":
                group_config.update({
                    "privileges": [
                        "SeBackupPrivilege",
                        "SeRestorePrivilege",
                        "SeSystemtimePrivilege",
                        "SeShutdownPrivilege"
                    ]
                })
            elif group_name == "Power Users":
                group_config.update({
                    "privileges": [
                        "SeShutdownPrivilege",
                        "SeSystemTimePrivilege"
                    ]
                })
            elif group_name == "Remote Desktop Users":
                group_config.update({
                    "privileges": [
                        "SeRemoteInteractiveLogonRight"
                    ]
                })
            
            group_settings.append(group_config)
        
        return {
            "xml_content": {
                "group_settings": group_settings,
                "group_count": len(group_settings),
                "total_users": len(users)
            },
            "xml_section": "specialize",
            "description": f"{len(group_settings)}個のグループ設定を生成",
            "groups_configured": list(group_memberships.keys())
        }


class AdministratorAgent(XMLGeneratingAgent):
    """管理者アカウント設定エージェント
    
    ビルトインAdministratorアカウントの設定を管理します。
    """
    
    def get_description(self) -> str:
        return "ビルトインAdministratorアカウントの有効化・無効化設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["administrator_config", "builtin_admin", "admin_security"]
    
    def get_required_inputs(self) -> List[str]:
        return ["users"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """管理者アカウント設定XML生成"""
        users = input_data["users"]
        
        # ビルトインAdministratorの設定を確認
        admin_config = None
        disable_builtin_admin = True
        
        for user in users:
            if user["name"].lower() == "administrator":
                admin_config = user
                disable_builtin_admin = False
                break
        
        admin_settings = []
        
        if disable_builtin_admin:
            # ビルトインAdministratorを無効化
            admin_settings.append({
                "type": "DisableBuiltinAdmin",
                "enabled": False,
                "description": "セキュリティ向上のためビルトインAdministratorを無効化"
            })
        else:
            # ビルトインAdministratorを有効化・設定
            admin_settings.extend([
                {
                    "type": "EnableBuiltinAdmin",
                    "enabled": True,
                    "password": admin_config["password"],
                    "description": "ビルトインAdministratorを有効化"
                },
                {
                    "type": "AdminSecurity",
                    "rename_admin": admin_config.get("rename_to"),
                    "password_never_expires": admin_config.get("password_expires", True) == False,
                    "description": "管理者アカウントのセキュリティ設定"
                }
            ])
        
        # 管理者権限を持つ他のユーザーの確認
        admin_users = [
            user["name"] for user in users
            if "Administrators" in user.get("groups", [])
        ]
        
        if len(admin_users) == 0 and disable_builtin_admin:
            # 警告: 管理者アカウントが存在しない
            admin_settings.append({
                "type": "Warning",
                "message": "管理者権限を持つアカウントが存在しません",
                "recommendation": "少なくとも1つの管理者アカウントを作成してください"
            })
        
        return {
            "xml_content": {
                "admin_settings": admin_settings,
                "builtin_admin_disabled": disable_builtin_admin,
                "admin_users": admin_users
            },
            "xml_section": "specialize",
            "description": "ビルトインAdministratorアカウント設定",
            "builtin_admin_enabled": not disable_builtin_admin
        }


class AutoLogonAgent(XMLGeneratingAgent):
    """自動ログオン設定エージェント
    
    Windows自動ログオン機能の設定を管理します。
    """
    
    def get_description(self) -> str:
        return "Windows自動ログオン機能の設定"
    
    def get_supported_tasks(self) -> List[str]:
        return ["auto_logon", "automatic_login", "user_authentication"]
    
    def get_required_inputs(self) -> List[str]:
        return ["users"]
    
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """自動ログオン設定XML生成"""
        users = input_data["users"]
        
        auto_logon_user = None
        auto_logon_settings = []
        
        # 自動ログオンが設定されているユーザーを検索
        for user in users:
            if user.get("auto_logon", False):
                if auto_logon_user:
                    # 複数のユーザーで自動ログオンが設定されている場合の警告
                    auto_logon_settings.append({
                        "type": "Warning",
                        "message": "複数のユーザーで自動ログオンが設定されています",
                        "recommendation": "自動ログオンは1つのユーザーのみに設定してください"
                    })
                else:
                    auto_logon_user = user
        
        if auto_logon_user:
            # 自動ログオン設定を生成
            auto_logon_config = {
                "type": "AutoLogon",
                "enabled": True,
                "username": auto_logon_user["name"],
                "password": auto_logon_user["password"],
                "domain": auto_logon_user.get("domain", "."),  # ローカルドメイン
                "logon_count": auto_logon_user.get("logon_count", 1),
                "description": f"ユーザー '{auto_logon_user['name']}' の自動ログオン設定"
            }
            
            auto_logon_settings.append(auto_logon_config)
            
            # セキュリティに関する警告
            auto_logon_settings.append({
                "type": "SecurityWarning",
                "message": "自動ログオンはセキュリティリスクを伴います",
                "recommendation": "本番環境では無効にすることを推奨します",
                "details": [
                    "パスワードがレジストリに保存されます",
                    "物理的なアクセスがあると不正利用される可能性があります"
                ]
            })
        else:
            # 自動ログオンが無効
            auto_logon_settings.append({
                "type": "AutoLogon",
                "enabled": False,
                "description": "自動ログオンは無効に設定"
            })
        
        return {
            "xml_content": {
                "auto_logon_settings": auto_logon_settings,
                "auto_logon_enabled": auto_logon_user is not None,
                "auto_logon_user": auto_logon_user["name"] if auto_logon_user else None
            },
            "xml_section": "specialize",
            "description": "自動ログオン設定",
            "security_warnings_count": sum(1 for s in auto_logon_settings if s.get("type") in ["Warning", "SecurityWarning"])
        }