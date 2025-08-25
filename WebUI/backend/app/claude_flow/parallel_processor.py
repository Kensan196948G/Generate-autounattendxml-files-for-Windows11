#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
Claude-flow並列処理エンジン

SubAgent群を効率的に並列実行し、リアルタイムで進捗を管理する
高性能な並列処理システムを実装します。
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID
import time

# import structlog  # temporary disable
from asyncio import Semaphore, Queue
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.models.schemas import SubAgentTaskModel, StatusEnum, PriorityEnum
# from app.agents import get_agent, get_agent_count
# from app.agents.base_agent import BaseAgent, AgentResult, AgentStatus

# 一時的にスタブ関数を定義（agents実装時に実際の関数に置き換え）
def get_agent(agent_name: str):
    """エージェント取得（仮実装）"""
    return None

def get_agent_count() -> int:
    """エージェント数取得（仮実装）"""
    return 30

class AgentStatus:
    """エージェント状態（仮実装）"""
    COMPLETED = "completed"
    FAILED = "failed"
    
class AgentResult:
    """エージェント結果（仮実装）"""
    def __init__(self):
        self.status = AgentStatus.FAILED
        self.output_data = {}
        self.error_message = None
        self.start_time = None
        self.end_time = None


logger = logging.getLogger(__name__)


@dataclass
class WorkerStats:
    """ワーカー統計情報"""
    worker_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    current_task: Optional[str] = None
    last_activity: Optional[datetime] = None
    
    @property
    def average_execution_time(self) -> float:
        """平均実行時間を計算"""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.tasks_completed


@dataclass
class SessionContext:
    """セッション実行コンテキスト"""
    session_id: UUID
    tasks: List[SubAgentTaskModel] = field(default_factory=list)
    completed_tasks: List[SubAgentTaskModel] = field(default_factory=list)
    failed_tasks: List[SubAgentTaskModel] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_cancelled: bool = False
    progress_callback: Optional[Callable[[int], None]] = None
    
    @property
    def completion_rate(self) -> float:
        """完了率を計算"""
        if not self.tasks:
            return 0.0
        return len(self.completed_tasks) / len(self.tasks)
    
    @property
    def total_execution_time(self) -> Optional[float]:
        """総実行時間を計算"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class ParallelProcessor:
    """Claude-flow並列処理エンジン
    
    30体以上のSubAgentを効率的に並列実行し、
    リアルタイムで進捗を監視・管理します。
    """
    
    def __init__(self):
        """並列処理エンジンを初期化"""
        self.settings = get_settings()
        
        # 並列実行制御
        self.max_workers = self.settings.claude_flow.max_workers
        self.semaphore = Semaphore(self.max_workers)
        self.task_queue: Queue = Queue(maxsize=self.settings.claude_flow.queue_size)
        
        # 実行コンテキスト管理
        self.active_sessions: Dict[UUID, SessionContext] = {}
        self.worker_stats: Dict[str, WorkerStats] = {}
        
        # スレッドプールエグゼキュータ
        self.thread_executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="claude_flow_worker"
        )
        
        # システム状態
        self.is_initialized = False
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> None:
        """並列処理エンジンを初期化"""
        try:
            logger.info("Claude-flow並列処理エンジンを初期化中...")
            
            # ワーカー統計の初期化
            for i in range(self.max_workers):
                worker_id = f"worker_{i:03d}"
                self.worker_stats[worker_id] = WorkerStats(worker_id=worker_id)
            
            # バックグラウンドワーカーを開始
            await self._start_workers()
            
            self.is_initialized = True
            self.is_running = True
            
            available_agents = get_agent_count()
            
            logger.info(
                "Claude-flow並列処理エンジン初期化完了",
                max_workers=self.max_workers,
                available_agents=available_agents,
                queue_size=self.settings.claude_flow.queue_size
            )
            
        except Exception as e:
            logger.error("並列処理エンジン初期化エラー", error=str(e))
            raise
    
    async def _start_workers(self) -> None:
        """バックグラウンドワーカーを開始"""
        for worker_id, stats in self.worker_stats.items():
            worker_task = asyncio.create_task(
                self._worker_loop(worker_id, stats),
                name=f"claude_flow_{worker_id}"
            )
            self.worker_tasks.append(worker_task)
    
    async def _worker_loop(self, worker_id: str, stats: WorkerStats) -> None:
        """ワーカーループ処理"""
        logger.info(f"ワーカー {worker_id} を開始")
        
        try:
            while self.is_running:
                try:
                    # タスクをキューから取得（タイムアウト付き）
                    task_item = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=5.0
                    )
                    
                    if task_item is None:  # 終了シグナル
                        break
                    
                    session_id, task = task_item
                    
                    # タスクを実行
                    await self._execute_task(worker_id, stats, session_id, task)
                    
                    # タスク完了通知
                    self.task_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # タイムアウト時は継続（キューが空の場合の正常動作）
                    continue
                    
                except Exception as e:
                    logger.error(f"ワーカー {worker_id} でエラー発生", error=str(e))
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"ワーカー {worker_id} がキャンセルされました")
            raise
        finally:
            logger.info(f"ワーカー {worker_id} を終了")
    
    async def _execute_task(
        self,
        worker_id: str,
        stats: WorkerStats,
        session_id: UUID,
        task: SubAgentTaskModel
    ) -> None:
        """個別タスクを実行"""
        
        async with self.semaphore:  # 並列実行数を制限
            start_time = time.time()
            stats.current_task = task.agent_name
            stats.last_activity = datetime.utcnow()
            
            try:
                logger.info(
                    f"タスク実行開始 [{worker_id}]",
                    session_id=str(session_id),
                    agent=task.agent_name,
                    task_id=str(task.task_id)
                )
                
                # セッションコンテキスト確認
                if session_id not in self.active_sessions:
                    raise ValueError(f"セッション {session_id} が見つかりません")
                
                session_context = self.active_sessions[session_id]
                
                # キャンセルチェック
                if session_context.is_cancelled:
                    task.status = StatusEnum.CANCELLED
                    return
                
                # エージェントクラスを取得
                agent_class = get_agent(task.agent_name)
                if not agent_class:
                    raise ValueError(f"エージェント '{task.agent_name}' が見つかりません")
                
                # エージェントインスタンスを作成して実行
                agent_instance = agent_class(task.agent_name)
                
                # タスクを非同期実行
                result = await agent_instance.execute(
                    task_id=task.task_id,
                    input_data=task.input_data,
                    session_id=session_id
                )
                
                # 結果をタスクに反映
                task.status = StatusEnum(result.status.value)
                task.output_data = result.output_data
                task.error_message = result.error_message
                task.start_time = result.start_time
                task.end_time = result.end_time
                
                # セッションコンテキストを更新
                if result.status == AgentStatus.COMPLETED:
                    session_context.completed_tasks.append(task)
                    stats.tasks_completed += 1
                else:
                    session_context.failed_tasks.append(task)
                    stats.tasks_failed += 1
                
                # 進捗コールバック実行
                if session_context.progress_callback:
                    await session_context.progress_callback(len(session_context.completed_tasks))
                
                execution_time = time.time() - start_time
                stats.total_execution_time += execution_time
                
                logger.info(
                    f"タスク実行完了 [{worker_id}]",
                    session_id=str(session_id),
                    agent=task.agent_name,
                    status=result.status.value,
                    execution_time=f"{execution_time:.2f}s"
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # エラー情報をタスクに記録
                task.status = StatusEnum.FAILED
                task.error_message = str(e)
                task.end_time = datetime.utcnow()
                
                # 統計を更新
                stats.tasks_failed += 1
                stats.total_execution_time += execution_time
                
                # セッションコンテキストを更新
                if session_id in self.active_sessions:
                    self.active_sessions[session_id].failed_tasks.append(task)
                
                logger.error(
                    f"タスク実行エラー [{worker_id}]",
                    session_id=str(session_id),
                    agent=task.agent_name,
                    error=str(e),
                    execution_time=f"{execution_time:.2f}s"
                )
            
            finally:
                stats.current_task = None
    
    async def execute_agents_parallel(
        self,
        tasks: List[SubAgentTaskModel],
        session_id: UUID,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[SubAgentTaskModel]:
        """
        エージェント群を並列実行
        
        Args:
            tasks: 実行するタスク一覧
            session_id: セッションID
            progress_callback: 進捗コールバック関数
            
        Returns:
            List[SubAgentTaskModel]: 実行結果
        """
        
        if not self.is_initialized:
            raise RuntimeError("並列処理エンジンが初期化されていません")
        
        # セッションコンテキストを作成
        session_context = SessionContext(
            session_id=session_id,
            tasks=tasks.copy(),
            start_time=datetime.utcnow(),
            progress_callback=progress_callback
        )
        
        self.active_sessions[session_id] = session_context
        
        try:
            logger.info(
                "並列エージェント実行開始",
                session_id=str(session_id),
                task_count=len(tasks),
                max_workers=self.max_workers
            )
            
            # 優先度でタスクをソート
            sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)
            
            # タスクをキューに追加
            for task in sorted_tasks:
                task.status = StatusEnum.PENDING
                await self.task_queue.put((session_id, task))
            
            # すべてのタスクが完了するまで待機
            total_tasks = len(tasks)
            timeout = self.settings.claude_flow.task_timeout
            
            start_wait = time.time()
            while True:
                completed_count = len(session_context.completed_tasks) + len(session_context.failed_tasks)
                
                # 完了チェック
                if completed_count >= total_tasks:
                    break
                
                # タイムアウトチェック
                if time.time() - start_wait > timeout:
                    logger.warn(
                        "並列実行タイムアウト",
                        session_id=str(session_id),
                        completed=completed_count,
                        total=total_tasks
                    )
                    break
                
                # キャンセルチェック
                if session_context.is_cancelled:
                    logger.info("並列実行がキャンセルされました", session_id=str(session_id))
                    break
                
                # 短時間待機
                await asyncio.sleep(0.1)
            
            session_context.end_time = datetime.utcnow()
            
            # 結果統計
            completed_tasks = len(session_context.completed_tasks)
            failed_tasks = len(session_context.failed_tasks)
            total_time = session_context.total_execution_time
            
            logger.info(
                "並列エージェント実行完了",
                session_id=str(session_id),
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                success_rate=f"{(completed_tasks/total_tasks)*100:.1f}%",
                total_time=f"{total_time:.2f}s" if total_time else "計算中"
            )
            
            # すべてのタスク（完了・失敗問わず）を返す
            return session_context.completed_tasks + session_context.failed_tasks
            
        except Exception as e:
            logger.error("並列実行エラー", session_id=str(session_id), error=str(e))
            raise
        
        finally:
            # セッションをクリーンアップ（一定時間後）
            asyncio.create_task(self._cleanup_session_later(session_id, delay_minutes=30))
    
    async def _cleanup_session_later(self, session_id: UUID, delay_minutes: int = 30) -> None:
        """セッションを遅延クリーンアップ"""
        try:
            await asyncio.sleep(delay_minutes * 60)
            
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info("セッションをクリーンアップしました", session_id=str(session_id))
                
        except Exception as e:
            logger.error("セッションクリーンアップエラー", 
                               session_id=str(session_id), error=str(e))
    
    async def cancel_session(self, session_id: UUID) -> bool:
        """セッションをキャンセル"""
        if session_id not in self.active_sessions:
            return False
        
        session_context = self.active_sessions[session_id]
        session_context.is_cancelled = True
        
        logger.info("セッションキャンセル要求", session_id=str(session_id))
        return True
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """エージェント全体の状態を取得"""
        
        total_completed = sum(stats.tasks_completed for stats in self.worker_stats.values())
        total_failed = sum(stats.tasks_failed for stats in self.worker_stats.values())
        total_execution_time = sum(stats.total_execution_time for stats in self.worker_stats.values())
        
        active_workers = sum(1 for stats in self.worker_stats.values() if stats.current_task)
        
        return {
            "system_status": "running" if self.is_running else "stopped",
            "total_workers": len(self.worker_stats),
            "active_workers": active_workers,
            "available_agents": get_agent_count(),
            "queue_size": self.task_queue.qsize(),
            "max_queue_size": self.settings.claude_flow.queue_size,
            "statistics": {
                "total_tasks_completed": total_completed,
                "total_tasks_failed": total_failed,
                "total_execution_time": total_execution_time,
                "average_execution_time": total_execution_time / max(total_completed, 1)
            },
            "active_sessions": len(self.active_sessions),
            "worker_details": [
                {
                    "worker_id": worker_id,
                    "tasks_completed": stats.tasks_completed,
                    "tasks_failed": stats.tasks_failed,
                    "average_execution_time": stats.average_execution_time,
                    "current_task": stats.current_task,
                    "last_activity": stats.last_activity.isoformat() if stats.last_activity else None
                }
                for worker_id, stats in self.worker_stats.items()
            ]
        }
    
    async def get_agent_tasks(self, agent_name: str) -> List[Dict[str, Any]]:
        """特定エージェントのタスク履歴を取得"""
        agent_tasks = []
        
        for session_context in self.active_sessions.values():
            for task in session_context.completed_tasks + session_context.failed_tasks:
                if task.agent_name == agent_name:
                    agent_tasks.append({
                        "session_id": str(session_context.session_id),
                        "task_id": str(task.task_id),
                        "status": task.status.value,
                        "start_time": task.start_time.isoformat() if task.start_time else None,
                        "end_time": task.end_time.isoformat() if task.end_time else None,
                        "execution_time": (
                            (task.end_time - task.start_time).total_seconds() 
                            if task.start_time and task.end_time else None
                        ),
                        "error_message": task.error_message
                    })
        
        return sorted(agent_tasks, key=lambda x: x["start_time"] or "", reverse=True)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """ヘルスチェック状態を取得"""
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "initialized": self.is_initialized,
            "running": self.is_running,
            "worker_count": len(self.worker_stats),
            "active_sessions": len(self.active_sessions),
            "queue_utilization": self.task_queue.qsize() / self.settings.claude_flow.queue_size
        }
    
    async def get_agent_count(self) -> int:
        """利用可能なエージェント数を取得"""
        return get_agent_count()
    
    async def cleanup(self) -> None:
        """リソースクリーンアップ"""
        try:
            logger.info("Claude-flow並列処理エンジンをシャットダウン中...")
            
            self.is_running = False
            
            # アクティブセッションをキャンセル
            for session_id in list(self.active_sessions.keys()):
                await self.cancel_session(session_id)
            
            # ワーカータスクを停止
            for _ in range(len(self.worker_tasks)):
                await self.task_queue.put(None)  # 終了シグナル
            
            # ワーカータスクの完了を待機
            if self.worker_tasks:
                await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
            # スレッドプールを停止
            self.thread_executor.shutdown(wait=True)
            
            logger.info("Claude-flow並列処理エンジンのシャットダウン完了")
            
        except Exception as e:
            logger.error("並列処理エンジンシャットダウンエラー", error=str(e))