"""
SubAgent基底クラス

すべてのSubAgentの基底となるクラス。
共通の機能とインターフェースを提供します。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import json


class AgentStatus(Enum):
    """Agentのステータス"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentPriority(Enum):
    """Agent実行優先度"""
    CRITICAL = 0  # 最優先
    HIGH = 1      # 高優先度
    NORMAL = 2    # 通常
    LOW = 3       # 低優先度


class BaseAgent(ABC):
    """SubAgent基底クラス"""
    
    def __init__(self, name: str, priority: AgentPriority = AgentPriority.NORMAL):
        """
        初期化
        
        Args:
            name: Agent名
            priority: 実行優先度
        """
        self.name = name
        self.priority = priority
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # 実行統計
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "retry_count": 0,
            "error_count": 0
        }
        
        # 結果とエラー
        self.result: Optional[Any] = None
        self.errors: List[str] = []
        
        # 依存関係
        self.dependencies: List[str] = []
        self.dependent_agents: List[str] = []
        
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Any:
        """
        Agentのメイン処理を実行
        
        Args:
            context: 実行コンテキスト
            
        Returns:
            実行結果
        """
        pass
    
    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        設定の妥当性を検証
        
        Args:
            context: 検証コンテキスト
            
        Returns:
            (検証成功フラグ, エラーメッセージリスト)
        """
        pass
    
    async def pre_execute(self, context: Dict[str, Any]) -> bool:
        """
        実行前処理
        
        Args:
            context: 実行コンテキスト
            
        Returns:
            実行可能フラグ
        """
        self.logger.info(f"実行前処理開始: {self.name}")
        
        # ステータス更新
        self.status = AgentStatus.RUNNING
        self.execution_stats["start_time"] = datetime.now()
        
        # 依存関係チェック
        if not await self._check_dependencies(context):
            self.logger.error(f"依存関係チェック失敗: {self.name}")
            return False
        
        # 事前検証
        is_valid, errors = await self.validate(context)
        if not is_valid:
            self.errors.extend(errors)
            self.logger.error(f"事前検証失敗: {self.name} - {errors}")
            return False
        
        return True
    
    async def post_execute(self, context: Dict[str, Any], result: Any) -> Any:
        """
        実行後処理
        
        Args:
            context: 実行コンテキスト
            result: 実行結果
            
        Returns:
            処理後の結果
        """
        self.logger.info(f"実行後処理開始: {self.name}")
        
        # 統計更新
        self.execution_stats["end_time"] = datetime.now()
        if self.execution_stats["start_time"]:
            duration = self.execution_stats["end_time"] - self.execution_stats["start_time"]
            self.execution_stats["duration"] = duration.total_seconds()
        
        # 結果保存
        self.result = result
        
        # ステータス更新
        if self.errors:
            self.status = AgentStatus.FAILED
        else:
            self.status = AgentStatus.COMPLETED
        
        # 結果を共有コンテキストに保存
        if "agent_results" not in context:
            context["agent_results"] = {}
        context["agent_results"][self.name] = result
        
        self.logger.info(f"実行完了: {self.name} (所要時間: {self.execution_stats['duration']}秒)")
        
        return result
    
    async def run(self, context: Dict[str, Any]) -> Any:
        """
        Agentを実行（前処理・メイン処理・後処理を含む）
        
        Args:
            context: 実行コンテキスト
            
        Returns:
            実行結果
        """
        try:
            # 前処理
            if not await self.pre_execute(context):
                self.status = AgentStatus.FAILED
                return None
            
            # メイン処理
            result = await self.execute(context)
            
            # 後処理
            return await self.post_execute(context, result)
            
        except Exception as e:
            self.logger.error(f"実行エラー: {self.name} - {str(e)}")
            self.errors.append(str(e))
            self.status = AgentStatus.FAILED
            self.execution_stats["error_count"] += 1
            raise
    
    async def run_with_retry(self, context: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        リトライ機能付きでAgentを実行
        
        Args:
            context: 実行コンテキスト
            max_retries: 最大リトライ回数
            
        Returns:
            実行結果
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                self.execution_stats["retry_count"] = attempt
                self.logger.info(f"実行試行 {attempt + 1}/{max_retries}: {self.name}")
                
                result = await self.run(context)
                return result
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"実行失敗 (試行 {attempt + 1}/{max_retries}): {self.name} - {str(e)}")
                
                if attempt < max_retries - 1:
                    # エクスポネンシャルバックオフ
                    wait_time = 2 ** attempt
                    self.logger.info(f"{wait_time}秒待機後にリトライ: {self.name}")
                    await asyncio.sleep(wait_time)
        
        # すべてのリトライが失敗
        self.logger.error(f"最大リトライ回数到達: {self.name}")
        if last_error is not None:
            raise last_error
        else:
            raise RuntimeError(f"Agent {self.name} failed after {max_retries} retries")
    
    async def _check_dependencies(self, context: Dict[str, Any]) -> bool:
        """
        依存関係をチェック
        
        Args:
            context: 実行コンテキスト
            
        Returns:
            依存関係が満たされているかのフラグ
        """
        if not self.dependencies:
            return True
        
        agent_results = context.get("agent_results", {})
        
        for dep in self.dependencies:
            if dep not in agent_results:
                self.logger.warning(f"依存Agent未実行: {dep}")
                return False
            
            # 依存Agentが成功しているかチェック
            # （agent_resultsに結果が存在すれば成功とみなす）
            if agent_results[dep] is None:
                self.logger.warning(f"依存Agent実行失敗: {dep}")
                return False
        
        return True
    
    def add_dependency(self, agent_name: str):
        """依存関係を追加"""
        if agent_name not in self.dependencies:
            self.dependencies.append(agent_name)
    
    def remove_dependency(self, agent_name: str):
        """依存関係を削除"""
        if agent_name in self.dependencies:
            self.dependencies.remove(agent_name)
    
    def get_status(self) -> Dict[str, Any]:
        """Agent状態を取得"""
        return {
            "name": self.name,
            "status": self.status.value,
            "priority": self.priority.value,
            "execution_stats": self.execution_stats,
            "errors": self.errors,
            "dependencies": self.dependencies
        }
    
    def reset(self):
        """Agentをリセット"""
        self.status = AgentStatus.IDLE
        self.result = None
        self.errors = []
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "duration": None,
            "retry_count": 0,
            "error_count": 0
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', status={self.status.value})"