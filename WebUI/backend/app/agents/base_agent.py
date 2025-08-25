#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
SubAgent基底クラス

すべてのSubAgentの基底となるクラスとインターフェースを定義します。
Claude-flow並列処理に対応した高性能な実装を提供します。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum

import structlog


logger = structlog.get_logger()


class AgentStatus(str, Enum):
    """エージェント実行状態"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentResult:
    """エージェント実行結果"""
    agent_name: str
    task_id: UUID
    status: AgentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        """実行時間を秒で取得"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で結果を取得"""
        return {
            "agent_name": self.agent_name,
            "task_id": str(self.task_id),
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "warnings": self.warnings or []
        }


class BaseAgent(ABC):
    """SubAgent基底クラス
    
    すべてのSubAgentはこのクラスを継承し、
    特定の設定処理を実装します。
    """
    
    def __init__(self, agent_name: str):
        """
        Args:
            agent_name: エージェント名
        """
        self.agent_name = agent_name
        self.logger = structlog.get_logger().bind(agent=agent_name)
    
    async def execute(
        self,
        task_id: UUID,
        input_data: Dict[str, Any],
        session_id: Optional[UUID] = None
    ) -> AgentResult:
        """
        エージェントタスクを実行
        
        Args:
            task_id: タスクID
            input_data: 入力データ
            session_id: セッションID（オプション）
            
        Returns:
            AgentResult: 実行結果
        """
        result = AgentResult(
            agent_name=self.agent_name,
            task_id=task_id,
            status=AgentStatus.PENDING,
            input_data=input_data
        )
        
        try:
            await self.logger.ainfo("エージェント実行開始", 
                                   task_id=str(task_id),
                                   session_id=str(session_id) if session_id else None)
            
            result.status = AgentStatus.RUNNING
            result.start_time = datetime.utcnow()
            
            # 入力データのバリデーション
            await self._validate_input(input_data)
            
            # メイン処理実行
            output_data = await self._execute_main(input_data)
            
            # 出力データのバリデーション
            await self._validate_output(output_data)
            
            result.output_data = output_data
            result.status = AgentStatus.COMPLETED
            result.end_time = datetime.utcnow()
            
            await self.logger.ainfo("エージェント実行完了",
                                   task_id=str(task_id),
                                   execution_time=result.execution_time)
            
        except ValueError as e:
            # バリデーションエラー
            result.status = AgentStatus.FAILED
            result.error_message = f"入力データエラー: {str(e)}"
            result.end_time = datetime.utcnow()
            
            await self.logger.aerror("エージェント実行エラー（バリデーション）",
                                    task_id=str(task_id),
                                    error=str(e))
        
        except NotImplementedError:
            # 未実装エラー
            result.status = AgentStatus.FAILED
            result.error_message = "エージェントが未実装です"
            result.end_time = datetime.utcnow()
            
            await self.logger.aerror("エージェント実行エラー（未実装）",
                                    task_id=str(task_id))
        
        except asyncio.CancelledError:
            # キャンセル
            result.status = AgentStatus.CANCELLED
            result.error_message = "処理がキャンセルされました"
            result.end_time = datetime.utcnow()
            
            await self.logger.awarn("エージェント実行キャンセル",
                                   task_id=str(task_id))
            raise
        
        except Exception as e:
            # その他のエラー
            result.status = AgentStatus.FAILED
            result.error_message = f"予期しないエラー: {str(e)}"
            result.end_time = datetime.utcnow()
            
            await self.logger.aerror("エージェント実行エラー（予期しない）",
                                    task_id=str(task_id),
                                    error=str(e))
        
        return result
    
    @abstractmethod
    async def _execute_main(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        メイン処理を実行（サブクラスで実装）
        
        Args:
            input_data: 入力データ
            
        Returns:
            Dict[str, Any]: 出力データ
        """
        raise NotImplementedError("サブクラスで_execute_mainを実装してください")
    
    async def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        入力データのバリデーション（サブクラスでオーバーライド可能）
        
        Args:
            input_data: 入力データ
            
        Raises:
            ValueError: バリデーションエラー時
        """
        if not isinstance(input_data, dict):
            raise ValueError("入力データは辞書形式である必要があります")
    
    async def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """
        出力データのバリデーション（サブクラスでオーバーライド可能）
        
        Args:
            output_data: 出力データ
            
        Raises:
            ValueError: バリデーションエラー時
        """
        if not isinstance(output_data, dict):
            raise ValueError("出力データは辞書形式である必要があります")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        エージェント情報を取得
        
        Returns:
            Dict[str, Any]: エージェント情報
        """
        return {
            "name": self.agent_name,
            "description": self.get_description(),
            "version": self.get_version(),
            "supported_tasks": self.get_supported_tasks(),
            "required_inputs": self.get_required_inputs(),
            "output_format": self.get_output_format()
        }
    
    def get_description(self) -> str:
        """エージェントの説明を取得（サブクラスでオーバーライド）"""
        return f"{self.agent_name}の説明"
    
    def get_version(self) -> str:
        """エージェントのバージョンを取得（サブクラスでオーバーライド）"""
        return "1.0.0"
    
    def get_supported_tasks(self) -> List[str]:
        """サポートするタスク一覧を取得（サブクラスでオーバーライド）"""
        return ["default"]
    
    def get_required_inputs(self) -> List[str]:
        """必須入力パラメータ一覧を取得（サブクラスでオーバーライド）"""
        return []
    
    def get_output_format(self) -> Dict[str, str]:
        """出力データフォーマットを取得（サブクラスでオーバーライド）"""
        return {"result": "処理結果"}


class XMLGeneratingAgent(BaseAgent):
    """XML生成機能付きエージェント基底クラス
    
    XML出力を行うエージェント用の基底クラス
    """
    
    async def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """XML生成エージェント用の出力バリデーション"""
        await super()._validate_output(output_data)
        
        # XML生成エージェントは xml_content フィールドが必須
        if "xml_content" not in output_data:
            raise ValueError("XML生成エージェントはxml_contentフィールドが必要です")
    
    def get_output_format(self) -> Dict[str, str]:
        """XML生成エージェント用の出力フォーマット"""
        return {
            "xml_content": "生成されたXMLコンテンツ",
            "xml_section": "対象XMLセクション（specialize/oobeSystem/auditSystem/servicing）",
            "description": "生成されたXMLの説明"
        }


class RegistryAgent(BaseAgent):
    """レジストリ操作エージェント基底クラス
    
    レジストリ設定を行うエージェント用の基底クラス
    """
    
    async def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """レジストリエージェント用の出力バリデーション"""
        await super()._validate_output(output_data)
        
        # レジストリエージェントは registry_settings フィールドが必須
        if "registry_settings" not in output_data:
            raise ValueError("レジストリエージェントはregistry_settingsフィールドが必要です")
    
    def get_output_format(self) -> Dict[str, str]:
        """レジストリエージェント用の出力フォーマット"""
        return {
            "registry_settings": "レジストリ設定一覧",
            "commands": "実行コマンド一覧",
            "description": "レジストリ設定の説明"
        }


class ValidationAgent(BaseAgent):
    """バリデーションエージェント基底クラス
    
    設定検証を行うエージェント用の基底クラス
    """
    
    async def _validate_output(self, output_data: Dict[str, Any]) -> None:
        """バリデーションエージェント用の出力バリデーション"""
        await super()._validate_output(output_data)
        
        # バリデーションエージェントは validation_result フィールドが必須
        if "validation_result" not in output_data:
            raise ValueError("バリデーションエージェントはvalidation_resultフィールドが必要です")
    
    def get_output_format(self) -> Dict[str, str]:
        """バリデーションエージェント用の出力フォーマット"""
        return {
            "validation_result": "バリデーション結果",
            "is_valid": "有効性フラグ",
            "errors": "エラー一覧",
            "warnings": "警告一覧",
            "suggestions": "改善提案"
        }


class AgentFactory:
    """エージェントファクトリクラス
    
    エージェントインスタンスの生成と管理を行います。
    """
    
    _agent_registry: Dict[str, type] = {}
    
    @classmethod
    def register_agent(cls, agent_name: str, agent_class: type) -> None:
        """エージェントクラスを登録"""
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"エージェントクラス {agent_class} はBaseAgentを継承していません")
        
        cls._agent_registry[agent_name] = agent_class
    
    @classmethod
    def create_agent(cls, agent_name: str) -> Optional[BaseAgent]:
        """エージェントインスタンスを作成"""
        agent_class = cls._agent_registry.get(agent_name)
        
        if not agent_class:
            return None
        
        return agent_class(agent_name)
    
    @classmethod
    def list_registered_agents(cls) -> List[str]:
        """登録されているエージェント一覧を取得"""
        return list(cls._agent_registry.keys())
    
    @classmethod
    def get_agent_info(cls, agent_name: str) -> Optional[Dict[str, Any]]:
        """エージェント情報を取得"""
        agent = cls.create_agent(agent_name)
        return agent.get_agent_info() if agent else None


# エクスポート用
__all__ = [
    "AgentStatus", "AgentResult", "BaseAgent", 
    "XMLGeneratingAgent", "RegistryAgent", "ValidationAgent",
    "AgentFactory"
]