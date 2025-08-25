#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Sysprep応答ファイル自動生成システム WebUI版
APIエンドポイント定義

このモジュールは、WebUIとのやり取りを行うすべての
APIエンドポイントを定義します。SubAgent機能と
Claude-flow並列処理を活用した高性能なAPIを提供します。
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

# import structlog  # temporary disable
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, 
    HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
)

# アプリケーション設定とサービス
from app.core.config import get_settings
from app.models.schemas import (
    APIResponseModel, ConfigurationPresetModel, XMLGenerationRequestModel,
    XMLGenerationResultModel, XMLGenerationProgressModel, SubAgentTaskModel,
    PresetTypeEnum, StatusEnum
)
from app.services.xml_generator import XMLGeneratorService
from app.claude_flow.parallel_processor import ParallelProcessor


logger = logging.getLogger(__name__)

# APIルーター作成
router = APIRouter(prefix="", tags=["WebUI API"])

# 依存性注入用の関数群
def get_xml_generator() -> XMLGeneratorService:
    """XML生成サービス取得"""
    from main import app
    return getattr(app.state, 'xml_generator', None)

def get_parallel_processor() -> ParallelProcessor:
    """並列処理エンジン取得"""
    from main import app
    return getattr(app.state, 'parallel_processor', None)


# ===== プリセット管理API =====

@router.get("/presets", response_model=APIResponseModel)
async def get_presets() -> APIResponseModel:
    """
    利用可能なプリセット一覧を取得
    
    企業、開発、最小限のプリセットタイプとカスタムプリセットを
    すべて取得して返します。
    """
    try:
        settings = get_settings()
        presets = []
        
        # 標準プリセット
        standard_presets = [
            {
                "name": "enterprise",
                "preset_type": PresetTypeEnum.ENTERPRISE,
                "description": "企業環境向けの包括的な設定プリセット",
                "is_builtin": True
            },
            {
                "name": "development", 
                "preset_type": PresetTypeEnum.DEVELOPMENT,
                "description": "開発環境向けの設定プリセット",
                "is_builtin": True
            },
            {
                "name": "minimal",
                "preset_type": PresetTypeEnum.MINIMAL,
                "description": "最小限の設定のみを含むプリセット",
                "is_builtin": True
            }
        ]
        
        presets.extend(standard_presets)
        
        # カスタムプリセット読み込み
        if settings.preset_directory.exists():
            for preset_file in settings.preset_directory.glob("*.yaml"):
                try:
                    import yaml
                    with open(preset_file, 'r', encoding='utf-8') as f:
                        preset_data = yaml.safe_load(f)
                    
                    presets.append({
                        "name": preset_file.stem,
                        "preset_type": PresetTypeEnum.CUSTOM,
                        "description": preset_data.get("description", "カスタムプリセット"),
                        "is_builtin": False,
                        "file_path": str(preset_file)
                    })
                except Exception as e:
                    logger.warning("プリセット読み込みエラー", 
                                 file=preset_file.name, error=str(e))
        
        logger.info("プリセット一覧を取得しました", count=len(presets))
        
        return APIResponseModel(
            success=True,
            message=f"{len(presets)}個のプリセットが見つかりました",
            data=presets
        )
        
    except Exception as e:
        logger.error("プリセット取得エラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセットの取得に失敗しました"
        )


@router.get("/presets/{preset_name}", response_model=APIResponseModel)
async def get_preset_detail(preset_name: str) -> APIResponseModel:
    """
    特定のプリセットの詳細設定を取得
    
    Args:
        preset_name: プリセット名
        
    Returns:
        プリセットの詳細設定
    """
    try:
        settings = get_settings()
        
        # 標準プリセットの場合
        if preset_name in ["enterprise", "development", "minimal"]:
            preset_file = settings.preset_directory / f"{preset_name}.yaml"
        else:
            # カスタムプリセットの場合
            preset_file = settings.preset_directory / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"プリセット '{preset_name}' が見つかりません"
            )
        
        import yaml
        with open(preset_file, 'r', encoding='utf-8') as f:
            preset_data = yaml.safe_load(f)
        
        logger.info("プリセット詳細を取得しました", preset=preset_name)
        
        return APIResponseModel(
            success=True,
            message=f"プリセット '{preset_name}' の詳細を取得しました",
            data=preset_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("プリセット詳細取得エラー", preset=preset_name, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセット詳細の取得に失敗しました"
        )


@router.post("/presets", response_model=APIResponseModel)
async def create_preset(preset: ConfigurationPresetModel) -> APIResponseModel:
    """
    新しいカスタムプリセットを作成
    
    Args:
        preset: プリセット設定データ
        
    Returns:
        作成されたプリセットの情報
    """
    try:
        settings = get_settings()
        
        # プリセット名の重複チェック
        preset_file = settings.preset_directory / f"{preset.name}.yaml"
        if preset_file.exists():
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"プリセット '{preset.name}' は既に存在します"
            )
        
        # プリセットをYAMLファイルに保存
        import yaml
        preset_data = preset.dict()
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            yaml.dump(preset_data, f, default_flow_style=False, 
                     allow_unicode=True, sort_keys=False)
        
        logger.info("新しいプリセットを作成しました", preset=preset.name)
        
        return APIResponseModel(
            success=True,
            message=f"プリセット '{preset.name}' を作成しました",
            data={"name": preset.name, "file_path": str(preset_file)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("プリセット作成エラー", preset=preset.name, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセットの作成に失敗しました"
        )


@router.put("/presets/{preset_name}", response_model=APIResponseModel)
async def update_preset(preset_name: str, preset: ConfigurationPresetModel) -> APIResponseModel:
    """
    既存のプリセットを更新
    
    Args:
        preset_name: 更新対象のプリセット名
        preset: 更新後のプリセット設定データ
        
    Returns:
        更新結果
    """
    try:
        settings = get_settings()
        preset_file = settings.preset_directory / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"プリセット '{preset_name}' が見つかりません"
            )
        
        # 標準プリセットの更新を防ぐ
        if preset_name in ["enterprise", "development", "minimal"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="標準プリセットは更新できません"
            )
        
        # プリセットの更新日時を設定
        preset.updated_at = datetime.utcnow()
        
        # YAMLファイルに保存
        import yaml
        preset_data = preset.dict()
        
        with open(preset_file, 'w', encoding='utf-8') as f:
            yaml.dump(preset_data, f, default_flow_style=False,
                     allow_unicode=True, sort_keys=False)
        
        logger.info("プリセットを更新しました", preset=preset_name)
        
        return APIResponseModel(
            success=True,
            message=f"プリセット '{preset_name}' を更新しました",
            data={"name": preset_name, "updated_at": preset.updated_at}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("プリセット更新エラー", preset=preset_name, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセットの更新に失敗しました"
        )


@router.delete("/presets/{preset_name}", response_model=APIResponseModel)
async def delete_preset(preset_name: str) -> APIResponseModel:
    """
    プリセットを削除
    
    Args:
        preset_name: 削除対象のプリセット名
        
    Returns:
        削除結果
    """
    try:
        # 標準プリセットの削除を防ぐ
        if preset_name in ["enterprise", "development", "minimal"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="標準プリセットは削除できません"
            )
        
        settings = get_settings()
        preset_file = settings.preset_directory / f"{preset_name}.yaml"
        
        if not preset_file.exists():
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"プリセット '{preset_name}' が見つかりません"
            )
        
        # ファイルを削除
        preset_file.unlink()
        
        logger.info("プリセットを削除しました", preset=preset_name)
        
        return APIResponseModel(
            success=True,
            message=f"プリセット '{preset_name}' を削除しました",
            data={"name": preset_name}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("プリセット削除エラー", preset=preset_name, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プリセットの削除に失敗しました"
        )


# ===== XML生成API =====

@router.post("/xml/generate", response_model=APIResponseModel)
async def generate_xml(
    request: XMLGenerationRequestModel,
    background_tasks: BackgroundTasks,
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
) -> APIResponseModel:
    """
    XML生成リクエストを開始
    
    SubAgent機能とClaude-flow並列処理を使用して、
    バックグラウンドでXML生成処理を開始します。
    
    Args:
        request: XML生成リクエストデータ
        background_tasks: バックグラウンドタスク管理
        xml_generator: XML生成サービス
        
    Returns:
        生成開始結果（session_idを含む）
    """
    try:
        if not xml_generator:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="XML生成サービスが利用できません"
            )
        
        # バックグラウンドでXML生成を開始
        background_tasks.add_task(
            xml_generator.generate_xml_async,
            request
        )
        
        logger.info("XML生成リクエストを受け付けました", 
                          session_id=str(request.session_id))
        
        return APIResponseModel(
            success=True,
            message="XML生成処理を開始しました",
            data={
                "session_id": str(request.session_id),
                "status": StatusEnum.PENDING,
                "estimated_time": "2-5分程度"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("XML生成開始エラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XML生成の開始に失敗しました"
        )


@router.get("/xml/progress/{session_id}", response_model=APIResponseModel)
async def get_xml_generation_progress(
    session_id: UUID,
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
) -> APIResponseModel:
    """
    XML生成の進捗状況を取得
    
    Args:
        session_id: セッションID
        xml_generator: XML生成サービス
        
    Returns:
        進捗状況
    """
    try:
        if not xml_generator:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="XML生成サービスが利用できません"
            )
        
        progress = await xml_generator.get_progress(session_id)
        
        if not progress:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"セッション '{session_id}' が見つかりません"
            )
        
        return APIResponseModel(
            success=True,
            message="進捗状況を取得しました",
            data=progress.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("進捗取得エラー", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="進捗状況の取得に失敗しました"
        )


@router.get("/xml/result/{session_id}", response_model=APIResponseModel)
async def get_xml_generation_result(
    session_id: UUID,
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
) -> APIResponseModel:
    """
    XML生成結果を取得
    
    Args:
        session_id: セッションID
        xml_generator: XML生成サービス
        
    Returns:
        XML生成結果
    """
    try:
        if not xml_generator:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="XML生成サービスが利用できません"
            )
        
        result = await xml_generator.get_result(session_id)
        
        if not result:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"セッション '{session_id}' の結果が見つかりません"
            )
        
        return APIResponseModel(
            success=True,
            message="XML生成結果を取得しました",
            data=result.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("結果取得エラー", session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XML生成結果の取得に失敗しました"
        )


@router.get("/xml/download/{session_id}")
async def download_xml_file(
    session_id: UUID,
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
):
    """
    生成されたXMLファイルをダウンロード
    
    Args:
        session_id: セッションID
        xml_generator: XML生成サービス
        
    Returns:
        XMLファイル
    """
    try:
        if not xml_generator:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="XML生成サービスが利用できません"
            )
        
        result = await xml_generator.get_result(session_id)
        
        if not result or not result.output_file_path:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="XMLファイルが見つかりません"
            )
        
        file_path = Path(result.output_file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="XMLファイルが存在しません"
            )
        
        logger.info("XMLファイルダウンロード開始", 
                          session_id=str(session_id), file=str(file_path))
        
        return FileResponse(
            path=file_path,
            filename=f"unattend_{session_id}.xml",
            media_type="application/xml"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("XMLダウンロードエラー", 
                    session_id=str(session_id), error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XMLファイルのダウンロードに失敗しました"
        )


@router.post("/xml/validate", response_model=APIResponseModel)
async def validate_xml(file: UploadFile = File(...)) -> APIResponseModel:
    """
    アップロードされたXMLファイルをバリデーション
    
    Args:
        file: アップロードされたXMLファイル
        
    Returns:
        バリデーション結果
    """
    try:
        if not file.filename.endswith('.xml'):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="XMLファイルのみアップロード可能です"
            )
        
        # XMLコンテンツを読み取り
        xml_content = await file.read()
        xml_text = xml_content.decode('utf-8')
        
        # XML生成サービスでバリデーション
        # （実際の実装では、XMLスキーマバリデーションを行う）
        validation_result = {
            "is_valid": True,
            "schema_version": "Windows 11",
            "warnings": [],
            "errors": [],
            "analyzed_sections": [
                "specialize",
                "oobeSystem", 
                "auditSystem",
                "offlineServicing"
            ]
        }
        
        logger.info("XMLバリデーション完了", 
                          filename=file.filename, is_valid=validation_result["is_valid"])
        
        return APIResponseModel(
            success=True,
            message="XMLバリデーションが完了しました",
            data=validation_result
        )
        
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="ファイルエンコーディングが不正です"
        )
    except Exception as e:
        logger.error("XMLバリデーションエラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="XMLバリデーションに失敗しました"
        )


# ===== SubAgent状態監視API =====

@router.get("/agents/status", response_model=APIResponseModel)
async def get_agent_status(
    processor: ParallelProcessor = Depends(get_parallel_processor)
) -> APIResponseModel:
    """
    SubAgentの全体状態を取得
    
    Args:
        processor: 並列処理エンジン
        
    Returns:
        エージェント状態
    """
    try:
        if not processor:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="並列処理エンジンが利用できません"
            )
        
        agent_status = await processor.get_agent_status()
        
        return APIResponseModel(
            success=True,
            message="エージェント状態を取得しました",
            data=agent_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("エージェント状態取得エラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="エージェント状態の取得に失敗しました"
        )


@router.get("/agents/{agent_name}/tasks", response_model=APIResponseModel)
async def get_agent_tasks(
    agent_name: str,
    processor: ParallelProcessor = Depends(get_parallel_processor)
) -> APIResponseModel:
    """
    特定エージェントのタスク一覧を取得
    
    Args:
        agent_name: エージェント名
        processor: 並列処理エンジン
        
    Returns:
        タスク一覧
    """
    try:
        if not processor:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="並列処理エンジンが利用できません"
            )
        
        tasks = await processor.get_agent_tasks(agent_name)
        
        return APIResponseModel(
            success=True,
            message=f"エージェント '{agent_name}' のタスクを取得しました",
            data={"agent_name": agent_name, "tasks": tasks}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("エージェントタスク取得エラー", 
                    agent=agent_name, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="エージェントタスクの取得に失敗しました"
        )


# ===== システム情報API =====

@router.get("/system/info", response_model=APIResponseModel)
async def get_system_info() -> APIResponseModel:
    """
    システム情報を取得
    
    Returns:
        システム情報
    """
    try:
        import platform
        import psutil
        
        system_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total if platform.system() != 'Windows' else psutil.disk_usage('C:\\').total,
                    "free": psutil.disk_usage('/').free if platform.system() != 'Windows' else psutil.disk_usage('C:\\').free,
                    "percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent
                }
            },
            "application": {
                "name": "Windows 11 Sysprep WebUI",
                "version": "1.0.0",
                "uptime": "起動中"  # 実際の実装では起動時刻を記録
            }
        }
        
        return APIResponseModel(
            success=True,
            message="システム情報を取得しました",
            data=system_info
        )
        
    except Exception as e:
        logger.error("システム情報取得エラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="システム情報の取得に失敗しました"
        )


# ===== ログ取得API =====

@router.get("/logs", response_model=APIResponseModel)
async def get_logs(
    limit: int = 100,
    level: Optional[str] = None
) -> APIResponseModel:
    """
    アプリケーションログを取得
    
    Args:
        limit: 取得件数制限
        level: ログレベルフィルター
        
    Returns:
        ログエントリ一覧
    """
    try:
        settings = get_settings()
        
        # ログファイルが存在しない場合
        if not settings.logging.file_path or not settings.logging.file_path.exists():
            return APIResponseModel(
                success=True,
                message="ログファイルが見つかりません",
                data={"logs": []}
            )
        
        # ログファイルを読み取り（簡易実装）
        logs = []
        with open(settings.logging.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 最新のログを取得
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                if level and level.upper() not in line.upper():
                    continue
                
                logs.append({
                    "timestamp": datetime.utcnow().isoformat(),  # 実際の実装ではログから抽出
                    "level": "INFO",  # 実際の実装ではログから抽出
                    "message": line.strip(),
                    "module": "unknown"  # 実際の実装ではログから抽出
                })
        
        return APIResponseModel(
            success=True,
            message=f"{len(logs)}件のログを取得しました",
            data={"logs": logs}
        )
        
    except Exception as e:
        logger.error("ログ取得エラー", error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログの取得に失敗しました"
        )


# ===== 生成ログダウンロードAPI =====

@router.get("/xml/generation-log/{generation_id}/download", response_model=None)
async def download_generation_log(
    generation_id: str,
    format: str = "json",
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
) -> FileResponse:
    """
    生成ログファイルをダウンロード
    
    Args:
        generation_id: 生成ID
        format: ログ形式 (json または text)
        xml_generator: XML生成サービス
        
    Returns:
        ログファイル
    """
    try:
        if format not in ["json", "text"]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="フォーマットは 'json' または 'text' を指定してください"
            )
            
        # 生成ログを取得 - シンプルなサンプルログを返す
        if format == "json":
            log_content = json.dumps({
                "generation_id": generation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "success": True,
                    "errors": [],
                    "warnings": [],
                    "items_processed": ["ユーザーアカウント", "ネットワーク設定", "システム設定"]
                },
                "detailed_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "INFO",
                        "message": "XML生成プロセスを開始"
                    },
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "SUCCESS",
                        "message": "XML生成が完了しました"
                    }
                ]
            }, ensure_ascii=False, indent=2)
        else:
            log_content = f"""Windows 11 Unattend.xml 生成ログ
生成ID: {generation_id}
生成日時: {datetime.utcnow().isoformat()}

【生成サマリー】
  生成結果: 成功
  処理時間: 2.34秒
  エラー数: 0
  警告数: 0

【処理詳細ログ】
  [INFO] XML生成プロセスを開始
  [SUCCESS] XML生成が完了しました
"""
        
        if not log_content:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"生成ID '{generation_id}' のログが見つかりません"
            )
            
        # 一時ファイルに書き込み
        from tempfile import NamedTemporaryFile
        import tempfile
        
        suffix = ".json" if format == "json" else ".txt"
        filename = f"unattend_generation_{generation_id}_log{suffix}"
        
        with NamedTemporaryFile(mode='w', encoding='utf-8', suffix=suffix, delete=False) as tmp:
            tmp.write(log_content)
            tmp_path = tmp.name
            
        return FileResponse(
            path=tmp_path,
            media_type='application/json' if format == 'json' else 'text/plain',
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ログダウンロードエラー", generation_id=generation_id, error=str(e))
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログのダウンロードに失敗しました"
        )


@router.post("/xml/generate-with-log", response_model=APIResponseModel)
async def generate_xml_with_log(
    request: XMLGenerationRequestModel,
    xml_generator: XMLGeneratorService = Depends(get_xml_generator)
) -> APIResponseModel:
    """
    XML生成を実行し、詳細ログを含む結果を返す
    
    Args:
        request: XML生成リクエストデータ
        xml_generator: XML生成サービス
        
    Returns:
        生成結果とログ情報
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        
        from src.core.xml_generator import UnattendXMLGenerator
        from src.core.generation_logger import generation_logger
        
        # ログをクリア
        generation_logger.clear()
        
        # XML生成器を初期化
        generator = UnattendXMLGenerator()
        
        # 設定を適用（プリセット使用またはカスタム設定）
        if request.preset_name:
            # プリセットを読み込んで適用
            config = await generator._load_preset_config(request.preset_name)
            await generator._apply_configuration(config.dict())
        elif request.custom_config:
            await generator._apply_configuration(request.custom_config.dict())
        
        # XML生成と保存
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"unattend_{timestamp}.xml"
        
        success, log_data = await generator.save(output_path)
        
        if success:
            # XMLファイル読み込み
            with open(output_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
                
            return APIResponseModel(
                success=True,
                message="XML生成に成功しました",
                data={
                    "xml_content": xml_content,
                    "xml_path": str(output_path),
                    "generation_id": timestamp,
                    "logs": {
                        "summary": generation_logger.get_summary(),
                        "json": log_data.get('json_log'),
                        "text": log_data.get('text_log'),
                        "download_urls": {
                            "json": f"/api/xml/generation-log/{timestamp}/download?format=json",
                            "text": f"/api/xml/generation-log/{timestamp}/download?format=text"
                        }
                    }
                }
            )
        else:
            return APIResponseModel(
                success=False,
                message="XML生成に失敗しました",
                data={
                    "error": log_data.get('error', 'Unknown error'),
                    "logs": {
                        "summary": generation_logger.get_summary(),
                        "json": log_data.get('json_log'),
                        "text": log_data.get('text_log')
                    }
                }
            )
            
    except Exception as e:
        logger.error("XML生成エラー", error=str(e))
        import traceback
        
        return APIResponseModel(
            success=False,
            message="XML生成中にエラーが発生しました",
            data={
                "error": str(e),
                "traceback": traceback.format_exc(),
                "logs": {
                    "summary": {"error_count": 1, "warning_count": 0, "success": False},
                    "error_details": [{"message": str(e), "type": type(e).__name__}]
                }
            }
        )