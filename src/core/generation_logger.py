"""
生成ログシステム - unattend.xml生成プロセスの詳細ログ記録
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum
import traceback


class LogLevel(Enum):
    """ログレベル定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class LogCategory(Enum):
    """ログカテゴリー定義"""
    SYSTEM = "システム"
    USER_CONFIG = "ユーザー設定"
    NETWORK = "ネットワーク"
    WINDOWS_FEATURES = "Windows機能"
    APPLICATIONS = "アプリケーション"
    WIFI = "Wi-Fi設定"
    DESKTOP = "デスクトップ設定"
    VALIDATION = "検証"
    XML_GENERATION = "XML生成"


class GenerationLogger:
    """
    unattend.xml生成プロセスの詳細ログを記録するクラス
    """
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.selected_items: Dict[str, Any] = {}
        self.generation_result: Dict[str, Any] = {
            'success': False,
            'xml_path': None,
            'errors': [],
            'warnings': []
        }
        self.start_time = None
        self.end_time = None
        
        # Pythonロガーも設定
        self.logger = logging.getLogger(__name__)
        
    def start_generation(self, config: Dict[str, Any]):
        """生成プロセス開始"""
        self.start_time = datetime.now()
        self.selected_items = self._extract_selected_items(config)
        
        self.add_log(
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            message="unattend.xml生成プロセスを開始しました",
            details={
                'start_time': self.start_time.isoformat(),
                'selected_items_count': len(self.selected_items)
            }
        )
        
    def end_generation(self, success: bool, xml_path: Optional[str] = None):
        """生成プロセス終了"""
        self.end_time = datetime.now()
        duration = (self.end_time - (self.start_time or self.end_time)).total_seconds()
        
        self.generation_result['success'] = success
        self.generation_result['xml_path'] = xml_path
        
        self.add_log(
            level=LogLevel.SUCCESS if success else LogLevel.ERROR,
            category=LogCategory.SYSTEM,
            message=f"unattend.xml生成プロセスが{'成功しました' if success else '失敗しました'}",
            details={
                'end_time': self.end_time.isoformat(),
                'duration_seconds': duration,
                'xml_path': xml_path
            }
        )
        
    def add_log(self, level: LogLevel, category: LogCategory, message: str, 
                details: Optional[Dict[str, Any]] = None):
        """ログエントリを追加"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'details': details or {}
        }
        
        self.logs.append(log_entry)
        
        # Pythonロガーにも出力
        log_message = f"[{category.value}] {message}"
        if details:
            log_message += f" - {json.dumps(details, ensure_ascii=False, indent=2)}"
            
        if level == LogLevel.ERROR:
            self.logger.error(log_message)
            self.generation_result['errors'].append({
                'category': category.value,
                'message': message,
                'details': details
            })
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
            self.generation_result['warnings'].append({
                'category': category.value,
                'message': message,
                'details': details
            })
        elif level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)
            
    def add_section_log(self, section_name: str, success: bool, 
                       items_processed: List[str], error: Optional[str] = None):
        """セクション処理のログを追加"""
        category_map = {
            'ユーザーアカウント': LogCategory.USER_CONFIG,
            'ネットワーク設定': LogCategory.NETWORK,
            'Windows機能': LogCategory.WINDOWS_FEATURES,
            'アプリケーション': LogCategory.APPLICATIONS,
            'Wi-Fi設定': LogCategory.WIFI,
            'デスクトップ設定': LogCategory.DESKTOP,
        }
        
        category = category_map.get(section_name, LogCategory.SYSTEM)
        
        if success:
            self.add_log(
                level=LogLevel.SUCCESS,
                category=category,
                message=f"{section_name}の処理が完了しました",
                details={
                    'items_processed': items_processed,
                    'items_count': len(items_processed)
                }
            )
        else:
            self.add_log(
                level=LogLevel.ERROR,
                category=category,
                message=f"{section_name}の処理中にエラーが発生しました",
                details={
                    'error': str(error),
                    'traceback': traceback.format_exc() if error else None,
                    'items_attempted': items_processed
                }
            )
            
    def add_validation_log(self, validation_type: str, success: bool, 
                          details: Optional[Dict[str, Any]] = None):
        """検証ログを追加"""
        if success:
            self.add_log(
                level=LogLevel.SUCCESS,
                category=LogCategory.VALIDATION,
                message=f"{validation_type}の検証に成功しました",
                details=details
            )
        else:
            self.add_log(
                level=LogLevel.ERROR,
                category=LogCategory.VALIDATION,
                message=f"{validation_type}の検証に失敗しました",
                details=details
            )
            
    def add_exception(self, exception: Exception, context: str):
        """例外情報をログに追加"""
        self.add_log(
            level=LogLevel.ERROR,
            category=LogCategory.SYSTEM,
            message=f"{context}で例外が発生しました",
            details={
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc()
            }
        )
        
    def _extract_selected_items(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """設定から選択された項目を抽出"""
        selected = {}
        
        # ユーザーアカウント
        if config.get('user_accounts'):
            selected['user_accounts'] = [
                {
                    'username': user.get('username'),
                    'groups': user.get('groups', [])
                }
                for user in config['user_accounts']
            ]
            
        # ネットワーク設定
        network_settings = []
        if config.get('disable_ipv6'):
            network_settings.append('IPv6無効化')
        if config.get('disable_firewall'):
            network_settings.append('ファイアウォール無効化')
        if config.get('enable_smb1'):
            network_settings.append('SMB1.0有効化')
        if network_settings:
            selected['network_settings'] = network_settings
            
        # Windows機能
        if config.get('windows_features'):
            selected['windows_features'] = config['windows_features']
            
        # アプリケーション
        if config.get('applications'):
            selected['applications'] = config['applications']
            
        # Wi-Fi設定
        if 'wifi_config' in config and config.get('wifi_config', {}).get('setup_mode') != 'skip':
            selected['wifi_config'] = {
                'setup_mode': config['wifi_config'].get('setup_mode'),
                'ssid': config['wifi_config'].get('ssid') if config['wifi_config'].get('setup_mode') == 'configure' else None
            }
            
        # デスクトップ設定
        if config.get('desktop_config'):
            desktop = config['desktop_config']
            selected['desktop_config'] = {
                'desktop_icons': [
                    key for key, value in desktop.get('desktop_icons', {}).items() 
                    if value
                ],
                'start_menu': [
                    key for key, value in desktop.get('start_menu', {}).items() 
                    if value
                ]
            }
            
        return selected
        
    def get_summary(self) -> Dict[str, Any]:
        """生成ログのサマリーを取得"""
        error_count = len([log for log in self.logs if log['level'] == LogLevel.ERROR.value])
        warning_count = len([log for log in self.logs if log['level'] == LogLevel.WARNING.value])
        
        return {
            'generation_time': self.start_time.isoformat() if self.start_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else None,
            'success': self.generation_result['success'],
            'xml_path': self.generation_result['xml_path'],
            'selected_items': self.selected_items,
            'error_count': error_count,
            'warning_count': warning_count,
            'total_logs': len(self.logs)
        }
        
    def export_json(self) -> str:
        """JSON形式でログをエクスポート"""
        export_data = {
            'summary': self.get_summary(),
            'selected_configuration': self.selected_items,
            'generation_result': self.generation_result,
            'detailed_logs': self.logs
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2, default=str)
        
    def export_text(self) -> str:
        """テキスト形式でログをエクスポート"""
        lines = []
        lines.append("=" * 80)
        lines.append("Windows 11 Unattend.xml 生成ログ")
        lines.append("=" * 80)
        lines.append("")
        
        # サマリー
        summary = self.get_summary()
        lines.append("【生成サマリー】")
        lines.append(f"  生成日時: {summary['generation_time']}")
        lines.append(f"  処理時間: {summary['duration_seconds']:.2f}秒" if summary['duration_seconds'] else "  処理時間: N/A")
        lines.append(f"  生成結果: {'成功' if summary['success'] else '失敗'}")
        lines.append(f"  XMLパス: {summary['xml_path'] or 'N/A'}")
        lines.append(f"  エラー数: {summary['error_count']}")
        lines.append(f"  警告数: {summary['warning_count']}")
        lines.append("")
        
        # 選択された設定項目
        lines.append("【選択された設定項目】")
        for category, items in self.selected_items.items():
            lines.append(f"  ■ {category}")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            lines.append(f"    - {key}: {value}")
                    else:
                        lines.append(f"    - {item}")
            elif isinstance(items, dict):
                for key, value in items.items():
                    lines.append(f"    - {key}: {value}")
        lines.append("")
        
        # エラーサマリー
        if self.generation_result['errors']:
            lines.append("【エラー一覧】")
            for error in self.generation_result['errors']:
                lines.append(f"  ✗ [{error['category']}] {error['message']}")
                if error.get('details'):
                    for key, value in error['details'].items():
                        if key != 'traceback':  # トレースバックは詳細ログに含める
                            lines.append(f"      {key}: {value}")
            lines.append("")
            
        # 警告サマリー
        if self.generation_result['warnings']:
            lines.append("【警告一覧】")
            for warning in self.generation_result['warnings']:
                lines.append(f"  ⚠ [{warning['category']}] {warning['message']}")
            lines.append("")
            
        # 詳細ログ
        lines.append("【処理詳細ログ】")
        for log in self.logs:
            timestamp = log['timestamp'].split('T')[1].split('.')[0]  # 時刻のみ抽出
            level_icon = {
                'DEBUG': '🔍',
                'INFO': 'ℹ',
                'SUCCESS': '✓',
                'WARNING': '⚠',
                'ERROR': '✗'
            }.get(log['level'], '•')
            
            lines.append(f"  [{timestamp}] {level_icon} [{log['category']}] {log['message']}")
            
            if log.get('details') and log['level'] in ['ERROR', 'WARNING']:
                for key, value in log['details'].items():
                    if value and key != 'traceback':
                        lines.append(f"      {key}: {value}")
                        
        lines.append("")
        lines.append("=" * 80)
        lines.append("ログ終了")
        lines.append("=" * 80)
        
        return "\n".join(lines)
        
    def clear(self):
        """ログをクリア"""
        self.logs.clear()
        self.selected_items.clear()
        self.generation_result = {
            'success': False,
            'xml_path': None,
            'errors': [],
            'warnings': []
        }
        self.start_time = None
        self.end_time = None


# グローバルインスタンス
generation_logger = GenerationLogger()