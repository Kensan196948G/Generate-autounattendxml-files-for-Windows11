#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
XML生成サービス

このモジュールは、SubAgent機能とClaude-flow並列処理を活用して、
Windows 11のSysprep応答ファイル（unattend.xml）を高速かつ確実に生成します。
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID
import xml.etree.ElementTree as ET
from xml.dom import minidom

# import structlog  # temporary disable
from lxml import etree

from app.core.config import get_settings
from app.models.schemas import (
    XMLGenerationRequestModel, XMLGenerationResultModel, XMLGenerationProgressModel,
    SubAgentTaskModel, ConfigurationPresetModel, StatusEnum, PriorityEnum
)
from app.claude_flow.parallel_processor import ParallelProcessor


logger = logging.getLogger(__name__)


class XMLGeneratorService:
    """XML生成サービスクラス
    
    SubAgent機能と並列処理を活用して、包括的なSysprep応答ファイルを生成します。
    """
    
    def __init__(self, parallel_processor: ParallelProcessor):
        """
        Args:
            parallel_processor: Claude-flow並列処理エンジン
        """
        self.parallel_processor = parallel_processor
        self.settings = get_settings()
        
        # 進行中のセッションを管理
        self.active_sessions: Dict[UUID, XMLGenerationProgressModel] = {}
        self.session_results: Dict[UUID, XMLGenerationResultModel] = {}
        
        # XMLテンプレートとスキーマのパス
        self.template_dir = self.settings.xml.template_directory
        self.schema_dir = self.settings.xml.schema_directory
        self.output_dir = self.settings.xml.output_directory
    
    async def generate_xml_async(self, request: XMLGenerationRequestModel) -> None:
        """
        非同期でXML生成処理を実行
        
        Args:
            request: XML生成リクエスト
        """
        session_id = request.session_id
        
        try:
            # 進捗モデルを初期化
            progress = XMLGenerationProgressModel(
                session_id=session_id,
                overall_status=StatusEnum.RUNNING,
                current_stage="設定の準備中",
                total_agents=0,
                completed_agents=0
            )
            
            self.active_sessions[session_id] = progress
            
            logger.info("XML生成を開始しました", session_id=str(session_id))
            
            # 1. 設定データの準備
            await self._update_progress(session_id, "設定データの準備中", 5)
            
            if request.preset_name:
                config = await self._load_preset_config(request.preset_name)
            else:
                config = request.custom_config
            
            if not config:
                raise ValueError("設定データが不正です")
            
            # 2. SubAgentタスクの生成
            await self._update_progress(session_id, "エージェントタスクの準備中", 10)
            
            agent_tasks = await self._create_agent_tasks(config, session_id)
            progress.total_agents = len(agent_tasks)
            progress.agent_tasks = agent_tasks
            
            await self._update_progress(session_id, f"{len(agent_tasks)}個のエージェントを準備しました", 15)
            
            # 3. 並列処理でエージェント実行
            await self._update_progress(session_id, "エージェント処理を開始中", 20)
            
            agent_results = await self.parallel_processor.execute_agents_parallel(
                agent_tasks,
                session_id,
                progress_callback=lambda completed: self._update_agent_progress(session_id, completed)
            )
            
            await self._update_progress(session_id, "XMLコンテンツ生成中", 80)
            
            # 4. XML生成
            xml_content = await self._generate_xml_from_results(agent_results, config)
            
            await self._update_progress(session_id, "XMLバリデーション中", 90)
            
            # 5. バリデーション（有効な場合）
            validation_result = None
            if request.validation_enabled:
                validation_result = await self._validate_xml(xml_content)
            
            # 6. ファイル保存
            await self._update_progress(session_id, "ファイル保存中", 95)
            
            output_filename = request.output_filename or f"unattend_{session_id}.xml"
            output_path = self.output_dir / output_filename
            
            await self._save_xml_file(xml_content, output_path)
            
            # 7. 結果の保存
            end_time = datetime.utcnow()
            start_time = progress.created_at
            processing_time = (end_time - start_time).total_seconds()
            
            result = XMLGenerationResultModel(
                session_id=session_id,
                status=StatusEnum.COMPLETED,
                xml_content=xml_content,
                output_file_path=str(output_path),
                validation_result=validation_result,
                processing_time=processing_time,
                agent_results=agent_results,
                logs={
                    "summary": {"success": True, "error_count": 0, "warning_count": 0, "processing_time": processing_time},
                    "detailed_logs": [
                        {"timestamp": start_time.isoformat(), "level": "INFO", "message": "XML生成開始"},
                        {"timestamp": end_time.isoformat(), "level": "SUCCESS", "message": "XML生成完了"}
                    ]
                }
            )
            
            self.session_results[session_id] = result
            
            # 進捗を完了に更新
            await self._update_progress(session_id, "XML生成が完了しました", 100, StatusEnum.COMPLETED)
            
            logger.info("XML生成が正常に完了しました", 
                              session_id=str(session_id), 
                              processing_time=processing_time)
            
        except Exception as e:
            logger.error("XML生成エラー", 
                               session_id=str(session_id), error=str(e))
            
            # エラー結果を保存
            error_result = XMLGenerationResultModel(
                session_id=session_id,
                status=StatusEnum.FAILED,
                error_details={"error": str(e), "type": type(e).__name__},
                logs={
                    "summary": {"success": False, "error_count": 1, "warning_count": 0},
                    "error_details": [{"message": str(e), "type": type(e).__name__}],
                    "detailed_logs": [
                        {"timestamp": datetime.utcnow().isoformat(), "level": "ERROR", "message": f"XML生成エラー: {str(e)}"}
                    ]
                }
            )
            
            self.session_results[session_id] = error_result
            
            # 進捗をエラー状態に更新
            if session_id in self.active_sessions:
                self.active_sessions[session_id].overall_status = StatusEnum.FAILED
                self.active_sessions[session_id].messages.append(f"エラー: {str(e)}")
    
    async def _load_preset_config(self, preset_name: str) -> ConfigurationPresetModel:
        """プリセット設定を読み込み"""
        preset_file = self.settings.preset_directory / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise FileNotFoundError(f"プリセット '{preset_name}' が見つかりません")
        
        import yaml
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            preset_data = yaml.safe_load(f)
        
        return ConfigurationPresetModel.parse_obj(preset_data)
    
    async def _create_agent_tasks(
        self, 
        config: ConfigurationPresetModel, 
        session_id: UUID
    ) -> List[SubAgentTaskModel]:
        """設定からSubAgentタスクを生成"""
        
        tasks = []
        
        # 1. ユーザー管理エージェント群
        if config.users:
            tasks.append(SubAgentTaskModel(
                agent_name="UserCreationAgent",
                task_type="user_creation",
                priority=PriorityEnum.CRITICAL,
                input_data={"users": [user.dict() for user in config.users]}
            ))
            
            tasks.append(SubAgentTaskModel(
                agent_name="UserPermissionAgent", 
                task_type="user_permissions",
                priority=PriorityEnum.HIGH,
                input_data={"users": [user.dict() for user in config.users]}
            ))
            
            tasks.append(SubAgentTaskModel(
                agent_name="UserGroupAgent",
                task_type="user_groups",
                priority=PriorityEnum.HIGH,
                input_data={"users": [user.dict() for user in config.users]}
            ))
        
        # 2. ドメイン参加エージェント
        if config.domain_join and config.domain_join.enabled:
            tasks.append(SubAgentTaskModel(
                agent_name="DomainJoinAgent",
                task_type="domain_join",
                priority=PriorityEnum.CRITICAL,
                input_data={"domain_config": config.domain_join.dict()}
            ))
        
        # 3. ネットワーク設定エージェント群
        tasks.extend([
            SubAgentTaskModel(
                agent_name="NetworkConfigAgent",
                task_type="network_basic",
                priority=PriorityEnum.HIGH,
                input_data={"network": config.network.dict()}
            ),
            SubAgentTaskModel(
                agent_name="FirewallConfigAgent",
                task_type="firewall_config",
                priority=PriorityEnum.NORMAL,
                input_data={"enabled": config.network.firewall_enabled}
            ),
            SubAgentTaskModel(
                agent_name="IPv6ConfigAgent",
                task_type="ipv6_config",
                priority=PriorityEnum.NORMAL,
                input_data={"enabled": config.network.ipv6_enabled}
            ),
            SubAgentTaskModel(
                agent_name="BluetoothConfigAgent",
                task_type="bluetooth_config",
                priority=PriorityEnum.LOW,
                input_data={"enabled": config.network.bluetooth_enabled}
            )
        ])
        
        # 4. システム設定エージェント群
        tasks.extend([
            SubAgentTaskModel(
                agent_name="TimezoneAgent",
                task_type="timezone_config",
                priority=PriorityEnum.NORMAL,
                input_data={"timezone": config.system.timezone}
            ),
            SubAgentTaskModel(
                agent_name="LocaleAgent",
                task_type="locale_config",
                priority=PriorityEnum.NORMAL,
                input_data={
                    "locale": config.system.locale,
                    "keyboard_layout": config.system.keyboard_layout
                }
            ),
            SubAgentTaskModel(
                agent_name="AudioConfigAgent",
                task_type="audio_config",
                priority=PriorityEnum.LOW,
                input_data={"muted": config.system.audio_muted}
            ),
            SubAgentTaskModel(
                agent_name="TelemetryAgent",
                task_type="telemetry_config",
                priority=PriorityEnum.NORMAL,
                input_data={"level": config.system.telemetry_level}
            )
        ])
        
        # 5. Windows機能エージェント群
        if config.system.windows_features:
            for feature in config.system.windows_features:
                tasks.append(SubAgentTaskModel(
                    agent_name="WindowsFeatureAgent",
                    task_type="windows_feature",
                    priority=PriorityEnum.NORMAL,
                    input_data={"feature": feature.dict()}
                ))
        
        # 6. アプリケーション設定エージェント群
        if config.applications.office_settings:
            tasks.append(SubAgentTaskModel(
                agent_name="OfficeConfigAgent",
                task_type="office_config",
                priority=PriorityEnum.NORMAL,
                input_data={"settings": [s.dict() for s in config.applications.office_settings]}
            ))
        
        if config.applications.default_programs:
            tasks.append(SubAgentTaskModel(
                agent_name="DefaultProgramAgent",
                task_type="default_programs",
                priority=PriorityEnum.LOW,
                input_data={"programs": [p.dict() for p in config.applications.default_programs]}
            ))
        
        if config.applications.security_software_config:
            tasks.append(SubAgentTaskModel(
                agent_name="SecuritySoftwareAgent",
                task_type="security_software",
                priority=PriorityEnum.HIGH,
                input_data=config.applications.security_software_config
            ))
        
        # 7. デスクトップ設定エージェント群
        if config.desktop_settings:
            tasks.append(SubAgentTaskModel(
                agent_name="DesktopIconAgent",
                task_type="desktop_icons",
                priority=PriorityEnum.LOW,
                input_data={"desktop_icons": config.desktop_settings.get("desktop_icons", {})}
            ))
            tasks.append(SubAgentTaskModel(
                agent_name="StartMenuAgent",
                task_type="start_menu",
                priority=PriorityEnum.LOW,
                input_data={"start_menu": config.desktop_settings.get("start_menu", {})}
            ))
        
        # 8. 検証・最適化エージェント群
        tasks.extend([
            SubAgentTaskModel(
                agent_name="RegistryValidationAgent",
                task_type="registry_validation",
                priority=PriorityEnum.LOW,
                input_data={"config": config.dict()}
            ),
            SubAgentTaskModel(
                agent_name="DependencyCheckAgent",
                task_type="dependency_check",
                priority=PriorityEnum.NORMAL,
                input_data={"config": config.dict()}
            ),
            SubAgentTaskModel(
                agent_name="OptimizationAgent",
                task_type="performance_optimization",
                priority=PriorityEnum.LOW,
                input_data={"config": config.dict()}
            ),
            SubAgentTaskModel(
                agent_name="SecurityHardeningAgent",
                task_type="security_hardening",
                priority=PriorityEnum.HIGH,
                input_data={"config": config.dict()}
            ),
            SubAgentTaskModel(
                agent_name="ComplianceCheckAgent",
                task_type="compliance_check",
                priority=PriorityEnum.NORMAL,
                input_data={"config": config.dict()}
            )
        ])
        
        logger.info(f"{len(tasks)}個のエージェントタスクを作成しました", 
                          session_id=str(session_id))
        
        return tasks
    
    async def _generate_xml_from_results(
        self, 
        agent_results: List[SubAgentTaskModel], 
        config: ConfigurationPresetModel
    ) -> str:
        """エージェント結果からXMLを生成"""
        
        # XMLルート要素作成
        unattend = etree.Element("unattend")
        unattend.set("xmlns", "urn:schemas-microsoft-com:unattend")
        
        # servicing パス（オフラインサービシング）
        servicing = etree.SubElement(unattend, "servicing")
        
        # specialize パス（システムの専門化）
        specialize_settings = etree.SubElement(unattend, "settings")
        specialize_settings.set("pass", "specialize")
        
        # oobeSystem パス（Out-of-Box Experience）
        oobe_settings = etree.SubElement(unattend, "settings")
        oobe_settings.set("pass", "oobeSystem")
        
        # auditSystem パス（監査システム）
        audit_settings = etree.SubElement(unattend, "settings")
        audit_settings.set("pass", "auditSystem")
        
        # エージェント結果を各セクションに統合
        for result in agent_results:
            if result.status != StatusEnum.COMPLETED or not result.output_data:
                continue
            
            xml_data = result.output_data.get("xml_content")
            if not xml_data:
                continue
            
            # エージェントタイプに応じてXMLセクションを配置
            await self._integrate_agent_xml(
                result.agent_name,
                xml_data,
                specialize_settings,
                oobe_settings,
                audit_settings,
                servicing
            )
        
        # XMLを文字列に変換（整形済み）
        xml_string = etree.tostring(
            unattend, 
            encoding='unicode', 
            pretty_print=True,
            xml_declaration=True
        )
        
        return xml_string
    
    async def _integrate_agent_xml(
        self,
        agent_name: str,
        xml_data: Dict[str, Any],
        specialize: etree.Element,
        oobe: etree.Element,
        audit: etree.Element,
        servicing: etree.Element
    ) -> None:
        """エージェントXMLデータを適切なセクションに統合"""
        
        # エージェントタイプに応じた配置ロジック
        if agent_name in ["UserCreationAgent", "UserPermissionAgent", "UserGroupAgent"]:
            # ユーザー関連は oobeSystem に配置
            await self._add_user_xml(oobe, xml_data)
            
        elif agent_name == "DomainJoinAgent":
            # ドメイン参加は specialize に配置
            await self._add_domain_xml(specialize, xml_data)
            
        elif agent_name in ["NetworkConfigAgent", "FirewallConfigAgent", "IPv6ConfigAgent"]:
            # ネットワーク設定は specialize に配置
            await self._add_network_xml(specialize, xml_data)
            
        elif agent_name == "WindowsFeatureAgent":
            # Windows機能は servicing に配置
            await self._add_feature_xml(servicing, xml_data)
            
        elif agent_name in ["OfficeConfigAgent", "DefaultProgramAgent"]:
            # アプリケーション設定は specialize に配置
            await self._add_application_xml(specialize, xml_data)
            
        else:
            # その他は specialize に配置
            await self._add_generic_xml(specialize, xml_data)
    
    async def _add_user_xml(self, oobe_settings: etree.Element, xml_data: Dict[str, Any]) -> None:
        """ユーザー設定XMLを追加"""
        # UserAccounts コンポーネント
        component = etree.SubElement(oobe_settings, "component")
        component.set("name", "Microsoft-Windows-Shell-Setup")
        component.set("processorArchitecture", "amd64")
        component.set("publicKeyToken", "31bf3856ad364e35")
        component.set("language", "neutral")
        component.set("versionScope", "nonSxS")
        
        # UserAccounts セクション
        user_accounts = etree.SubElement(component, "UserAccounts")
        
        # AdministratorPassword
        if xml_data.get("administrator_password"):
            admin_password = etree.SubElement(user_accounts, "AdministratorPassword")
            value = etree.SubElement(admin_password, "Value")
            value.text = xml_data["administrator_password"]
            plain_text = etree.SubElement(admin_password, "PlainText")
            plain_text.text = "true"
        
        # LocalAccounts
        if xml_data.get("local_accounts"):
            local_accounts = etree.SubElement(user_accounts, "LocalAccounts")
            
            for account in xml_data["local_accounts"]:
                local_account = etree.SubElement(local_accounts, "LocalAccount")
                local_account.set("wcm:action", "add")
                
                password = etree.SubElement(local_account, "Password")
                value = etree.SubElement(password, "Value")
                value.text = account["password"]
                plain_text = etree.SubElement(password, "PlainText")
                plain_text.text = "true"
                
                name = etree.SubElement(local_account, "Name")
                name.text = account["name"]
                
                display_name = etree.SubElement(local_account, "DisplayName")
                display_name.text = account.get("display_name", account["name"])
                
                group = etree.SubElement(local_account, "Group")
                group.text = account.get("group", "Users")
    
    async def _add_domain_xml(self, specialize_settings: etree.Element, xml_data: Dict[str, Any]) -> None:
        """ドメイン参加設定XMLを追加"""
        component = etree.SubElement(specialize_settings, "component")
        component.set("name", "Microsoft-Windows-UnattendedJoin")
        component.set("processorArchitecture", "amd64")
        component.set("publicKeyToken", "31bf3856ad364e35")
        component.set("language", "neutral")
        component.set("versionScope", "nonSxS")
        
        identification = etree.SubElement(component, "Identification")
        
        credentials = etree.SubElement(identification, "Credentials")
        domain_elem = etree.SubElement(credentials, "Domain")
        domain_elem.text = xml_data["domain_name"]
        
        username = etree.SubElement(credentials, "Username")
        username.text = xml_data["username"]
        
        password = etree.SubElement(credentials, "Password")
        password.text = xml_data["password"]
        
        join_domain = etree.SubElement(identification, "JoinDomain")
        join_domain.text = xml_data["domain_name"]
        
        if xml_data.get("organizational_unit"):
            machine_ou = etree.SubElement(identification, "MachineObjectOU")
            machine_ou.text = xml_data["organizational_unit"]
    
    async def _add_network_xml(self, specialize_settings: etree.Element, xml_data: Dict[str, Any]) -> None:
        """ネットワーク設定XMLを追加"""
        # コンピューター名設定
        if xml_data.get("hostname"):
            component = etree.SubElement(specialize_settings, "component")
            component.set("name", "Microsoft-Windows-Shell-Setup")
            component.set("processorArchitecture", "amd64")
            component.set("publicKeyToken", "31bf3856ad364e35")
            component.set("language", "neutral")
            component.set("versionScope", "nonSxS")
            
            computer_name = etree.SubElement(component, "ComputerName")
            computer_name.text = xml_data["hostname"]
    
    async def _add_feature_xml(self, servicing: etree.Element, xml_data: Dict[str, Any]) -> None:
        """Windows機能設定XMLを追加"""
        if xml_data.get("feature_name"):
            package = etree.SubElement(servicing, "package")
            package.set("action", "install" if xml_data.get("enabled", True) else "remove")
            
            assembly_identity = etree.SubElement(package, "assemblyIdentity")
            assembly_identity.set("name", xml_data["feature_name"])
            assembly_identity.set("version", "10.0.22000.1")
            assembly_identity.set("processorArchitecture", "amd64")
            assembly_identity.set("publicKeyToken", "31bf3856ad364e35")
    
    async def _add_application_xml(self, specialize_settings: etree.Element, xml_data: Dict[str, Any]) -> None:
        """アプリケーション設定XMLを追加"""
        # レジストリ設定として追加
        if xml_data.get("registry_settings"):
            for setting in xml_data["registry_settings"]:
                # RunOnce コマンドとして設定
                component = etree.SubElement(specialize_settings, "component")
                component.set("name", "Microsoft-Windows-Shell-Setup")
                component.set("processorArchitecture", "amd64")
                component.set("publicKeyToken", "31bf3856ad364e35")
                component.set("language", "neutral")
                component.set("versionScope", "nonSxS")
                
                first_logon_commands = etree.SubElement(component, "FirstLogonCommands")
                
                command = etree.SubElement(first_logon_commands, "SynchronousCommand")
                command.set("wcm:action", "add")
                
                command_line = etree.SubElement(command, "CommandLine")
                command_line.text = setting.get("command", "")
                
                order = etree.SubElement(command, "Order")
                order.text = str(setting.get("order", 1))
    
    async def _add_generic_xml(self, specialize_settings: etree.Element, xml_data: Dict[str, Any]) -> None:
        """汎用XML設定を追加"""
        # 基本的なレジストリ設定やコマンド実行として処理
        pass
    
    async def _validate_xml(self, xml_content: str) -> Dict[str, Any]:
        """XML内容をバリデーション"""
        try:
            # XML構文チェック
            etree.fromstring(xml_content)
            
            # スキーマバリデーション（スキーマファイルがある場合）
            schema_file = self.schema_dir / "unattend.xsd"
            if schema_file.exists():
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_doc = etree.parse(f)
                    schema = etree.XMLSchema(schema_doc)
                    
                    xml_doc = etree.fromstring(xml_content)
                    is_valid = schema.validate(xml_doc)
                    
                    return {
                        "is_valid": is_valid,
                        "errors": [str(error) for error in schema.error_log] if not is_valid else [],
                        "warnings": []
                    }
            
            return {
                "is_valid": True,
                "errors": [],
                "warnings": ["スキーマファイルが見つからないため、基本的な構文チェックのみ実行しました"]
            }
            
        except etree.XMLSyntaxError as e:
            return {
                "is_valid": False,
                "errors": [f"XML構文エラー: {str(e)}"],
                "warnings": []
            }
    
    async def _save_xml_file(self, xml_content: str, output_path: Path) -> None:
        """XMLファイルを保存"""
        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info("XMLファイルを保存しました", path=str(output_path))
    
    async def _update_progress(
        self,
        session_id: UUID,
        message: str,
        percentage: int,
        status: Optional[StatusEnum] = None
    ) -> None:
        """進捗を更新"""
        if session_id in self.active_sessions:
            progress = self.active_sessions[session_id]
            progress.current_stage = message
            progress.progress_percentage = percentage
            progress.messages.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {message}")
            progress.updated_at = datetime.utcnow()
            
            if status:
                progress.overall_status = status
            
            # WebSocketで進捗通知 (必要に応じて実装)
            # TODO: WebSocket通知機能を実装
    
    async def _update_agent_progress(self, session_id: UUID, completed_count: int) -> None:
        """エージェント完了進捗を更新"""
        if session_id in self.active_sessions:
            progress = self.active_sessions[session_id]
            progress.completed_agents = completed_count
            
            # 進捗率計算（20%～80%の範囲でエージェント進捗を表示）
            if progress.total_agents > 0:
                agent_progress = (completed_count / progress.total_agents) * 60  # 60%分をエージェント処理に割り当て
                total_progress = 20 + agent_progress  # 20%から開始
                progress.progress_percentage = min(int(total_progress), 80)
            
            progress.updated_at = datetime.utcnow()
    
    async def get_progress(self, session_id: UUID) -> Optional[XMLGenerationProgressModel]:
        """進捗状況を取得"""
        return self.active_sessions.get(session_id)
    
    async def get_result(self, session_id: UUID) -> Optional[XMLGenerationResultModel]:
        """生成結果を取得"""
        return self.session_results.get(session_id)
    
    async def cancel_generation(self, session_id: UUID) -> bool:
        """XML生成をキャンセル"""
        if session_id in self.active_sessions:
            progress = self.active_sessions[session_id]
            progress.overall_status = StatusEnum.CANCELLED
            progress.current_stage = "処理をキャンセルしました"
            progress.updated_at = datetime.utcnow()
            
            # 並列処理エンジンにキャンセル要求
            await self.parallel_processor.cancel_session(session_id)
            
            return True
        
        return False
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """古いセッションをクリーンアップ"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        # 古い進捗データを削除
        old_sessions = [
            sid for sid, progress in self.active_sessions.items()
            if progress.created_at.timestamp() < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.active_sessions[session_id]
            if session_id in self.session_results:
                del self.session_results[session_id]
            cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"{cleaned_count}個の古いセッションをクリーンアップしました")
        
        return cleaned_count