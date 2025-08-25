# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル生成システム - バリデーターモジュール

このモジュールは以下の検証機能を提供します：
- XMLスキーマ検証
- 設定ファイル検証
- 依存関係チェック
- エラーレポート生成

Author: Windows 11 Sysprep応答ファイル生成システム
Version: 1.0.0
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from xml.etree import ElementTree as ET
from xml.dom import minidom
import yaml
# from cerberus import Validator  # Optional dependency - commented out for now


class XMLValidator:
    """
    XML応答ファイルの検証を行うクラス
    
    Windows 11のunattend.xmlファイルの構造と内容を検証し、
    エラーや警告を報告します。
    """
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.validation_errors = []
        self.validation_warnings = []
        
        # Windows 11で必須の名前空間
        self.required_namespaces = {
            'urn:schemas-microsoft-com:unattend',
            'urn:schemas-microsoft-com:asm.v3'
        }
        
        # サポートされているWindows 11アーキテクチャ
        self.supported_architectures = {'amd64', 'arm64'}
        
        # 必須のpassesとその順序
        self.required_passes = [
            'windowsPE',
            'offlineServicing', 
            'generalize',
            'specialize',
            'auditSystem',
            'auditUser',
            'oobeSystem'
        ]
    
    def validate_xml(self, xml_file_path: str) -> bool:
        """
        XMLファイルの包括的な検証を実行
        
        Args:
            xml_file_path (str): 検証するXMLファイルのパス
            
        Returns:
            bool: 検証が成功した場合はTrue、エラーがある場合はFalse
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        try:
            self.logger.info(f"XML検証開始: {xml_file_path}")
            
            # ファイル存在確認
            if not Path(xml_file_path).exists():
                self.validation_errors.append(f"XMLファイルが見つかりません: {xml_file_path}")
                return False
            
            # XML構文解析
            try:
                tree = ET.parse(xml_file_path)
                root = tree.getroot()
            except ET.ParseError as e:
                self.validation_errors.append(f"XML構文エラー: {e}")
                return False
            
            # 基本構造検証
            self._validate_root_structure(root)
            
            # 名前空間検証
            self._validate_namespaces(root)
            
            # passes構造検証
            self._validate_passes_structure(root)
            
            # コンポーネント検証
            self._validate_components(root)
            
            # セキュリティ設定検証
            self._validate_security_settings(root)
            
            # 整合性検証
            self._validate_consistency(root)
            
            # 検証結果のログ出力
            if self.validation_errors:
                self.logger.error(f"XML検証エラー: {len(self.validation_errors)}件のエラーが見つかりました")
                for error in self.validation_errors:
                    self.logger.error(f"  - {error}")
            
            if self.validation_warnings:
                self.logger.warning(f"XML検証警告: {len(self.validation_warnings)}件の警告があります")
                for warning in self.validation_warnings:
                    self.logger.warning(f"  - {warning}")
            
            success = len(self.validation_errors) == 0
            self.logger.info(f"XML検証完了: {'成功' if success else '失敗'}")
            
            return success
            
        except Exception as e:
            self.validation_errors.append(f"XML検証中に予期しないエラーが発生しました: {e}")
            self.logger.error(f"XML検証エラー: {e}")
            return False
    
    def _validate_root_structure(self, root: ET.Element):
        """ルート要素の構造を検証"""
        if root.tag != 'unattend':
            self.validation_errors.append("ルート要素は'unattend'である必要があります")
        
        # 必要な属性の確認
        xmlns = root.get('xmlns')
        if not xmlns:
            self.validation_errors.append("ルート要素にxmlns属性が必要です")
        elif xmlns != 'urn:schemas-microsoft-com:unattend':
            self.validation_errors.append(f"不正なxmlns値: {xmlns}")
    
    def _validate_namespaces(self, root: ET.Element):
        """名前空間の検証"""
        # 使用されている名前空間を収集
        used_namespaces = set()
        
        # ルート要素の属性から名前空間を取得
        for attr_name, attr_value in root.attrib.items():
            if attr_name.startswith('xmlns'):
                used_namespaces.add(attr_value)
        
        # 必須名前空間の確認
        missing_namespaces = self.required_namespaces - used_namespaces
        if missing_namespaces:
            for ns in missing_namespaces:
                self.validation_warnings.append(f"推奨される名前空間が見つかりません: {ns}")
    
    def _validate_passes_structure(self, root: ET.Element):
        """passes構造の検証"""
        settings_elements = root.findall('./settings')
        
        if not settings_elements:
            self.validation_errors.append("settings要素が見つかりません")
            return
        
        found_passes = set()
        for settings in settings_elements:
            pass_name = settings.get('pass')
            if pass_name:
                found_passes.add(pass_name)
                
                # アーキテクチャの確認
                arch = settings.get('processorArchitecture')
                if arch and arch not in self.supported_architectures:
                    self.validation_warnings.append(f"サポートされていないアーキテクチャ: {arch}")
        
        # 重要なpassesの存在確認
        critical_passes = {'windowsPE', 'specialize', 'oobeSystem'}
        missing_critical_passes = critical_passes - found_passes
        
        if missing_critical_passes:
            for pass_name in missing_critical_passes:
                self.validation_warnings.append(f"推奨されるpass '{pass_name}' が見つかりません")
    
    def _validate_components(self, root: ET.Element):
        """コンポーネントの検証"""
        components = root.findall('.//component')
        
        if not components:
            self.validation_warnings.append("コンポーネントが定義されていません")
            return
        
        component_names = set()
        
        for component in components:
            # コンポーネント名の確認
            name = component.get('name')
            if not name:
                self.validation_errors.append("コンポーネントにname属性が必要です")
                continue
            
            component_names.add(name)
            
            # 公開キーとアーキテクチャの確認
            public_key_token = component.get('publicKeyToken')
            if not public_key_token:
                self.validation_warnings.append(f"コンポーネント '{name}' にpublicKeyToken属性がありません")
            
            processor_arch = component.get('processorArchitecture')
            if not processor_arch:
                self.validation_warnings.append(f"コンポーネント '{name}' にprocessorArchitecture属性がありません")
        
        # 推奨コンポーネントの確認
        recommended_components = {
            'Microsoft-Windows-Setup',
            'Microsoft-Windows-Shell-Setup',
            'Microsoft-Windows-International-Core'
        }
        
        missing_recommended = recommended_components - component_names
        if missing_recommended:
            for comp_name in missing_recommended:
                self.validation_warnings.append(f"推奨コンポーネント '{comp_name}' が見つかりません")
    
    def _validate_security_settings(self, root: ET.Element):
        """セキュリティ設定の検証"""
        # 自動ログオン設定の確認
        auto_logon_elements = root.findall('.//AutoLogon')
        for auto_logon in auto_logon_elements:
            enabled = auto_logon.find('Enabled')
            if enabled is not None and enabled.text == 'true':
                self.validation_warnings.append(
                    "自動ログオンが有効になっています。セキュリティ上のリスクを考慮してください"
                )
        
        # パスワード設定の確認
        password_elements = root.findall('.//Password')
        for password in password_elements:
            plain_text = password.find('PlainText')
            if plain_text is not None and plain_text.text == 'true':
                self.validation_warnings.append(
                    "平文パスワードが使用されています。セキュリティ上のリスクを考慮してください"
                )
        
        # Administrator アカウントの確認
        user_accounts = root.findall('.//UserAccounts')
        for user_accounts_elem in user_accounts:
            admin_password = user_accounts_elem.find('.//AdministratorPassword')
            if admin_password is not None:
                plain_text = admin_password.find('PlainText')
                if plain_text is not None and plain_text.text == 'true':
                    self.validation_warnings.append(
                        "Administrator パスワードが平文で設定されています"
                    )
    
    def _validate_consistency(self, root: ET.Element):
        """設定の整合性を検証"""
        # コンピューター名の重複チェック
        computer_names = []
        computer_name_elements = root.findall('.//ComputerName')
        
        for elem in computer_name_elements:
            if elem.text:
                computer_names.append(elem.text)
        
        if len(set(computer_names)) > 1:
            self.validation_warnings.append(
                f"複数の異なるコンピューター名が指定されています: {set(computer_names)}"
            )
        
        # ユーザーアカウントの重複チェック
        usernames = []
        local_account_elements = root.findall('.//LocalAccount')
        
        for account in local_account_elements:
            name_elem = account.find('Name')
            if name_elem is not None and name_elem.text:
                usernames.append(name_elem.text)
        
        if len(usernames) != len(set(usernames)):
            duplicates = [name for name in set(usernames) if usernames.count(name) > 1]
            self.validation_errors.append(
                f"重複するユーザー名があります: {duplicates}"
            )
    
    def get_validation_report(self) -> str:
        """
        検証レポートを文字列として取得
        
        Returns:
            str: エラーと警告を含む検証レポート
        """
        report_lines = []
        
        if self.validation_errors:
            report_lines.append("=== エラー ===")
            for i, error in enumerate(self.validation_errors, 1):
                report_lines.append(f"{i}. {error}")
            report_lines.append("")
        
        if self.validation_warnings:
            report_lines.append("=== 警告 ===")
            for i, warning in enumerate(self.validation_warnings, 1):
                report_lines.append(f"{i}. {warning}")
        
        return "\n".join(report_lines) if report_lines else "検証エラーや警告はありません。"
    
    def get_validation_errors(self) -> List[str]:
        """検証エラーのリストを取得"""
        return self.validation_errors.copy()
    
    def get_validation_warnings(self) -> List[str]:
        """検証警告のリストを取得"""
        return self.validation_warnings.copy()


class ConfigValidator:
    """
    設定ファイルの検証を行うクラス
    
    YAML設定ファイルの構造、型、値の範囲などを検証します。
    """
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # 設定スキーマの定義
        self.config_schema = {
            'metadata': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'version': {'type': 'string'},
                    'author': {'type': 'string'}
                }
            },
            'general': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'computer_name': {
                        'type': 'string',
                        'minlength': 1,
                        'maxlength': 15,
                        'regex': r'^[a-zA-Z0-9\-]+$'
                    },
                    'time_zone': {'type': 'string'},
                    'locale': {'type': 'string'},
                    'keyboard_layout': {'type': 'string'},
                    'input_language': {'type': 'string'}
                }
            },
            'user_accounts': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'administrator': {
                        'type': 'dict',
                        'schema': {
                            'username': {'type': 'string', 'required': True},
                            'password': {'type': 'string', 'required': True},
                            'enabled': {'type': 'boolean'},
                            'auto_logon': {'type': 'boolean'},
                            'full_name': {'type': 'string'},
                            'description': {'type': 'string'}
                        }
                    },
                    'local_accounts': {
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'username': {'type': 'string', 'required': True},
                                'password': {'type': 'string', 'required': True},
                                'group': {'type': 'string'},
                                'enabled': {'type': 'boolean'},
                                'full_name': {'type': 'string'},
                                'description': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            'network': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'static_ip': {
                        'type': 'dict',
                        'schema': {
                            'ip_address': {'type': 'string', 'required': True, 'regex': r'^(\d{1,3}\.){3}\d{1,3}$'},
                            'subnet_mask': {'type': 'string', 'required': True, 'regex': r'^(\d{1,3}\.){3}\d{1,3}$'},
                            'gateway': {'type': 'string', 'regex': r'^(\d{1,3}\.){3}\d{1,3}$'},
                            'dns_servers': {
                                'type': 'list',
                                'schema': {'type': 'string', 'regex': r'^(\d{1,3}\.){3}\d{1,3}$'}
                            }
                        }
                    },
                    'domain_join': {
                        'type': 'dict',
                        'schema': {
                            'domain_name': {'type': 'string', 'required': True},
                            'username': {'type': 'string', 'required': True},
                            'password': {'type': 'string', 'required': True},
                            'ou_path': {'type': 'string'},
                            'machine_account_ou': {'type': 'string'}
                        }
                    },
                    'workgroup': {
                        'type': 'dict',
                        'schema': {
                            'workgroup_name': {'type': 'string', 'required': True}
                        }
                    }
                }
            },
            'applications': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'install_packages': {
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'name': {'type': 'string', 'required': True},
                                'source': {'type': 'string', 'required': True},
                                'arguments': {'type': 'string'},
                                'condition': {'type': 'string'}
                            }
                        }
                    },
                    'run_commands': {
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'command': {'type': 'string', 'required': True},
                                'description': {'type': 'string'},
                                'order': {'type': 'integer'},
                                'condition': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            'windows_features': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'enable': {
                        'type': 'list',
                        'schema': {'type': 'string'}
                    },
                    'disable': {
                        'type': 'list',
                        'schema': {'type': 'string'}
                    }
                }
            },
            'registry': {
                'type': 'dict',
                'required': False,
                'schema': {
                    'keys': {
                        'type': 'list',
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'path': {'type': 'string', 'required': True},
                                'name': {'type': 'string'},
                                'value': {'type': 'string'},
                                'type': {'type': 'string', 'allowed': ['REG_SZ', 'REG_DWORD', 'REG_BINARY']},
                                'action': {'type': 'string', 'allowed': ['add', 'delete', 'modify']}
                            }
                        }
                    }
                }
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        設定辞書を検証
        
        Args:
            config (Dict[str, Any]): 検証する設定辞書
            
        Returns:
            Tuple[bool, List[str]]: (検証成功フラグ, エラーメッセージのリスト)
        """
        try:
            # validator = Validator(self.config_schema)  # cerberus dependency removed
            # is_valid = validator.validate(config)
            
            # Basic validation without cerberus
            is_valid = isinstance(config, dict) and len(config) > 0
            errors = []
            
            if not is_valid:
                errors.append("Configuration must be a non-empty dictionary")
            
            # Additional basic validation checks can be added here
            
            # カスタム検証ルール
            custom_errors = self._validate_custom_rules(config)
            errors.extend(custom_errors)
            
            if errors:
                self.logger.error(f"設定検証エラー: {len(errors)}件のエラーが見つかりました")
                for error in errors:
                    self.logger.error(f"  - {error}")
            else:
                self.logger.info("設定検証: 成功")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            error_msg = f"設定検証中にエラーが発生しました: {e}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def _validate_custom_rules(self, config: Dict[str, Any]) -> List[str]:
        """カスタム検証ルールを適用"""
        errors = []
        
        # コンピューター名の検証
        general = config.get('general', {})
        computer_name = general.get('computer_name')
        if computer_name:
            if len(computer_name) > 15:
                errors.append("コンピューター名は15文字以下である必要があります")
            if not re.match(r'^[a-zA-Z0-9\-]+$', computer_name):
                errors.append("コンピューター名には英数字とハイフンのみ使用できます")
            if computer_name.startswith('-') or computer_name.endswith('-'):
                errors.append("コンピューター名はハイフンで開始または終了できません")
        
        # ネットワーク設定の検証
        network = config.get('network', {})
        
        # ドメイン参加とワークグループの同時設定チェック
        if 'domain_join' in network and 'workgroup' in network:
            errors.append("ドメイン参加とワークグループ設定を同時に指定することはできません")
        
        # IPアドレス形式の検証
        static_ip = network.get('static_ip', {})
        if static_ip:
            for ip_field in ['ip_address', 'subnet_mask', 'gateway']:
                ip_value = static_ip.get(ip_field)
                if ip_value and not self._is_valid_ip(ip_value):
                    errors.append(f"不正なIPアドレス形式: {ip_field} = {ip_value}")
            
            dns_servers = static_ip.get('dns_servers', [])
            for dns in dns_servers:
                if not self._is_valid_ip(dns):
                    errors.append(f"不正なDNSサーバーIPアドレス: {dns}")
        
        # ユーザーアカウントの検証
        user_accounts = config.get('user_accounts', {})
        
        # パスワード強度チェック
        administrator = user_accounts.get('administrator', {})
        admin_password = administrator.get('password')
        if admin_password and not self._is_strong_password(admin_password):
            errors.append("管理者パスワードは最低8文字で、大文字、小文字、数字を含む必要があります")
        
        # ローカルアカウントのユーザー名重複チェック
        local_accounts = user_accounts.get('local_accounts', [])
        usernames = [acc.get('username') for acc in local_accounts if acc.get('username')]
        if len(usernames) != len(set(usernames)):
            errors.append("ローカルアカウントのユーザー名が重複しています")
        
        return errors
    
    def _is_valid_ip(self, ip_address: str) -> bool:
        """IPアドレスの形式を検証"""
        try:
            parts = ip_address.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            return True
        except ValueError:
            return False
    
    def _is_strong_password(self, password: str) -> bool:
        """パスワードの強度を検証"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit


class DependencyChecker:
    """
    設定間の依存関係をチェックするクラス
    
    設定項目間の依存関係や競合を検出します。
    """
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
    
    def check_dependencies(self, config: Dict[str, Any]) -> List[str]:
        """
        設定の依存関係をチェック
        
        Args:
            config (Dict[str, Any]): チェックする設定辞書
            
        Returns:
            List[str]: 依存関係エラーのリスト
        """
        errors = []
        
        # ドメイン参加とネットワーク設定の依存関係
        network = config.get('network', {})
        if 'domain_join' in network:
            if 'static_ip' not in network:
                errors.append("ドメイン参加にはスタティックIP設定が推奨されます")
        
        # Windows機能の依存関係
        windows_features = config.get('windows_features', {})
        enabled_features = windows_features.get('enable', [])
        
        # Hyper-V関連の依存関係
        hyper_v_features = [f for f in enabled_features if 'Hyper-V' in f]
        if hyper_v_features:
            required_features = ['Microsoft-Hyper-V-All', 'Microsoft-Hyper-V-Management-Clients']
            for required in required_features:
                if required not in enabled_features:
                    errors.append(f"Hyper-V機能には {required} が必要です")
        
        # IIS関連の依存関係
        iis_features = [f for f in enabled_features if 'IIS' in f]
        if iis_features:
            if 'IIS-WebServerRole' not in enabled_features:
                errors.append("IIS機能にはIIS-WebServerRoleが必要です")
        
        return errors