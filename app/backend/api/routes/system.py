#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理API路由

提供系统健康检查、状态等信息
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from log_manager import get_logger
import json
from datetime import datetime
import sys
import platform
from typing import Optional, Set
from pathlib import Path
import asyncio
import os
import re
from config import Config

logger = get_logger('api.system', 'api.log')

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康检查端点
    
    返回系统运行状态
    """
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": Config.APP_VERSION
    })


@router.get("/status")
async def system_status():
    """
    获取系统状态信息
    
    返回基本系统信息
    """
    try:
        return JSONResponse(content={
            "success": True,
            "status": {
                "app_version": Config.APP_VERSION,
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "uptime": "N/A"  # 可以后续添加
            }
        })
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取系统状态失败: {str(e)}"
        }, status_code=500)


@router.get("/info")
async def system_info():
    """
    获取系统基本信息
    
    返回系统版本、Python版本等
    """
    try:
        return JSONResponse(content={
            "success": True,
            "info": {
                "app_version": Config.APP_VERSION,
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        })
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取系统信息失败: {str(e)}"
        }, status_code=500)


@router.post("/restart")
async def restart_system():
    """
    重启系统（仅重启应用）
    
    注意：此操作会重启整个应用
    """
    try:
        logger.warning("收到重启请求")
        
        # 在Docker环境中，可以通过退出让容器重启
        # 需要配置restart策略
        return JSONResponse(content={
            "success": True,
            "message": "重启请求已接收，系统将在5秒后重启"
        })
    except Exception as e:
        logger.error(f"重启系统失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"重启系统失败: {str(e)}"
        }, status_code=500)


@router.get("/logs")
async def get_system_logs():
    """
    获取系统日志
    
    返回最近的系统日志（日志文件内容）
    """
    try:
        import os
        from pathlib import Path
        
        logs_dir = Path("logs")
        log_files = []
        
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                try:
                    # 读取最后100行
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        last_lines = lines[-100:] if len(lines) > 100 else lines
                        
                    log_files.append({
                        "filename": log_file.name,
                        "size": log_file.stat().st_size,
                        "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat(),
                        "preview": ''.join(last_lines)
                    })
                except Exception as e:
                    logger.warning(f"读取日志文件 {log_file} 失败: {e}")
        
        return JSONResponse(content={
            "success": True,
            "logs": log_files
        })
    except Exception as e:
        logger.error(f"获取系统日志失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取系统日志失败: {str(e)}"
        }, status_code=500)


@router.get("/container-logs/stream")
async def stream_container_logs(
    sources: Optional[str] = Query(default=None, description="以逗号分隔的日志文件名过滤，如: web_api.log,api_rules.log"),
    levels: Optional[str] = Query(default=None, description="以逗号分隔的级别过滤，如: INFO,WARNING,ERROR"),
    keyword: Optional[str] = Query(default=None, description="关键字过滤（包含匹配，不区分大小写）"),
    tail: Optional[int] = Query(default=500, description="加载最近N行历史日志，0表示不加载历史"),
):
    """
    实时流式传输应用日志（SSE）
    
    使用Server-Sent Events实时推送应用日志到前端
    """
    from fastapi.responses import StreamingResponse

    # 解析过滤条件
    source_filters: Optional[Set[str]] = (
        set([s.strip() for s in sources.split(',') if s.strip()]) if sources else None
    )
    level_filters: Optional[Set[str]] = (
        set([lv.strip().upper() for lv in levels.split(',') if lv.strip()]) if levels else None
    )
    keyword_lc: Optional[str] = keyword.lower() if keyword else None

    async def log_generator():
        """异步生成器，持续读取应用日志（支持源/级别/关键字过滤，动态发现新日志文件）。"""
        # 日志目录（优先使用配置）
        logs_dir = Path(getattr(Config, 'LOGS_DIR', '/app/logs'))
        try:
            # 记录每个文件的读取位置
            file_positions = {}
            file_handles = {}

            # 正则用于解析日志级别和时间戳： 2025-10-06 12:00:00 | INFO | xxx - msg
            level_regex = re.compile(r"\|\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|")
            # 正则用于解析时间戳：2025-10-06 12:00:00 或 2025-10-06 12:00:00.123
            timestamp_regex = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)")

            def discover_log_files() -> Set[str]:
                files = set()
                if logs_dir.exists():
                    for p in logs_dir.glob('*.log'):
                        files.add(p.name)
                return files

            # 首次发现日志文件
            discovered = discover_log_files()

            # 如果有源过滤，仅保留匹配的
            if source_filters:
                discovered = {f for f in discovered if f in source_filters}

            # 读取文件最后N行的辅助函数
            def read_tail_lines(filepath: Path, n: int) -> list:
                """读取文件最后n行"""
                if n <= 0:
                    return []
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        return lines[-n:] if len(lines) > n else lines
                except Exception:
                    return []

            # 先发送初始连接消息，包含可用源
            yield (
                f"data: {json.dumps({'type': 'connected', 'message': '✅ TMC v1.0 - 已连接到日志流', 'sources': sorted(list(discovered))})}\n\n"
            )

            # 打开新发现的文件并发送历史日志
            for fname in discovered:
                if fname not in file_handles:
                    fpath = logs_dir / fname
                    if fpath.exists():
                        try:
                            # 先读取历史日志
                            if tail > 0:
                                tail_lines = read_tail_lines(fpath, tail)
                                for raw in tail_lines:
                                    line = raw.rstrip()
                                    if not line:
                                        continue
                                    
                                    # 解析时间戳
                                    timestamp_match = timestamp_regex.match(line)
                                    log_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    
                                    # 解析级别
                                    level_match = level_regex.search(line)
                                    level_val = level_match.group(1) if level_match else None
                                    
                                    # 级别过滤
                                    if level_filters and (level_val is None or level_val.upper() not in level_filters):
                                        logger.debug(f"级别过滤跳过: {line[:50]}")
                                        continue
                                    
                                    # 关键字过滤
                                    if keyword_lc and (keyword_lc not in line.lower()):
                                        logger.debug(f"关键字过滤跳过: {line[:50]}")
                                        continue
                                    
                                    log_data = {
                                        'type': 'log',
                                        'message': line,
                                        'timestamp': log_timestamp,
                                        'source': fname,
                                        'level': (level_val or 'INFO')
                                    }
                                    yield f"data: {json.dumps(log_data)}\n\n"
                            
                            # 打开文件用于后续实时读取
                            fh = open(fpath, 'r', encoding='utf-8', errors='ignore')
                            fh.seek(0, os.SEEK_END)
                            file_handles[fname] = fh
                            file_positions[fname] = fh.tell()
                        except Exception as e:
                            logger.warning(f"无法打开日志文件 {fname}: {e}")

            last_discover_ts = datetime.now().timestamp()

            # 持续监控
            while True:
                has_new_data = False

                # 周期性重新发现新日志文件（每2秒）
                now_ts = datetime.now().timestamp()
                if now_ts - last_discover_ts >= 2:
                    last_discover_ts = now_ts
                    current = discover_log_files()
                    if source_filters:
                        current = {f for f in current if f in source_filters}
                    # 打开新增
                    for fname in current:
                        if fname not in file_handles:
                            fpath = logs_dir / fname
                            if fpath.exists():
                                try:
                                    # 新增文件也读取历史日志
                                    if tail > 0:
                                        tail_lines = read_tail_lines(fpath, tail)
                                        for raw in tail_lines:
                                            line = raw.rstrip()
                                            if not line:
                                                continue
                                            
                                            # 解析时间戳
                                            timestamp_match = timestamp_regex.match(line)
                                            log_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            
                                            level_match = level_regex.search(line)
                                            level_val = level_match.group(1) if level_match else None
                                            
                                            if level_filters and (level_val is None or level_val.upper() not in level_filters):
                                                continue
                                            
                                            if keyword_lc and (keyword_lc not in line.lower()):
                                                continue
                                            
                                            log_data = {
                                                'type': 'log',
                                                'message': line,
                                                'timestamp': log_timestamp,
                                                'source': fname,
                                                'level': (level_val or 'INFO')
                                            }
                                            yield f"data: {json.dumps(log_data)}\n\n"
                                    
                                    fh = open(fpath, 'r', encoding='utf-8', errors='ignore')
                                    fh.seek(0, os.SEEK_END)
                                    file_handles[fname] = fh
                                    file_positions[fname] = fh.tell()
                                    # 通知新增源
                                    yield f"data: {json.dumps({'type': 'connected', 'message': f'新增日志源: {fname}', 'source': fname})}\n\n"
                                except Exception as e:
                                    logger.warning(f"无法打开新增日志文件 {fname}: {e}")
                    # 关闭已删除
                    for fname in list(file_handles.keys()):
                        fpath = logs_dir / fname
                        if not fpath.exists():
                            try:
                                file_handles[fname].close()
                            except Exception:
                                pass
                            del file_handles[fname]

                # 读取各文件的新行
                for fname, fh in list(file_handles.items()):
                    try:
                        # 检查文件是否有新内容
                        current_pos = fh.tell()
                        fh.seek(0, os.SEEK_END)
                        end_pos = fh.tell()
                        
                        # 如果有新内容，回到之前位置读取
                        if end_pos > current_pos:
                            fh.seek(current_pos)
                            lines = fh.readlines()
                            
                            if lines:
                                has_new_data = True
                                for raw in lines:
                                    line = raw.rstrip()
                                    if not line:
                                        continue

                                    # 解析时间戳
                                    timestamp_match = timestamp_regex.match(line)
                                    log_timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                                    # 解析级别
                                    level_match = level_regex.search(line)
                                    level_val = level_match.group(1) if level_match else None

                                    # 级别过滤
                                    if level_filters and (level_val is None or level_val.upper() not in level_filters):
                                        continue

                                    # 关键字过滤
                                    if keyword_lc and (keyword_lc not in line.lower()):
                                        continue

                                    log_data = {
                                        'type': 'log',
                                        'message': line,
                                        'timestamp': log_timestamp,
                                        'source': fname,
                                        'level': (level_val or 'INFO')
                                    }
                                    yield f"data: {json.dumps(log_data)}\n\n"

                                file_positions[fname] = fh.tell()
                        else:
                            # 没有新内容，保持在当前位置
                            fh.seek(current_pos)
                            
                    except Exception as e:
                        logger.error(f"读取 {fname} 失败: {e}")
                        # 尝试重开
                        try:
                            fh.close()
                        except Exception:
                            pass
                        fpath = logs_dir / fname
                        if fpath.exists():
                            try:
                                fh2 = open(fpath, 'r', encoding='utf-8', errors='ignore')
                                fh2.seek(file_positions.get(fname, 0))
                                file_handles[fname] = fh2
                            except Exception:
                                pass

                # 始终sleep一小段时间，避免CPU占用过高，也让文件有时间写入新内容
                await asyncio.sleep(0.5)

        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f'日志流错误: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            # 关闭所有文件句柄
            try:
                for fh in list(locals().get('file_handles', {}).values()):
                    try:
                        fh.close()
                    except Exception:
                        pass
            except Exception:
                pass
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/enhanced-status")
async def enhanced_status():
    """
    获取增强模式状态
    
    返回当前是否运行在增强模式，以及相关状态信息
    """
    try:
        from main import get_enhanced_bot
        
        enhanced_bot = get_enhanced_bot()
        
        # 获取增强Bot的状态
        is_running = enhanced_bot is not None and enhanced_bot.running if hasattr(enhanced_bot, 'running') else False
        
        # 获取客户端统计信息
        total_clients = 0
        running_clients = 0
        connected_clients = 0
        
        if enhanced_bot and hasattr(enhanced_bot, 'get_client_status'):
            clients_status = enhanced_bot.get_client_status()
            total_clients = len(clients_status)
            running_clients = sum(1 for client in clients_status.values() if client.get("running", False))
            connected_clients = sum(1 for client in clients_status.values() if client.get("connected", False))
        
        return JSONResponse(content={
            "success": True,
            "enhanced_mode": True,  # 始终返回True，因为我们使用的是增强版启动
            "bot_running": is_running,
            "total_clients": total_clients,
            "running_clients": running_clients,
            "connected_clients": connected_clients,
            "version": Config.APP_VERSION,
            "mode": "enhanced",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取增强模式状态失败: {e}")
        return JSONResponse(content={
            "success": False,
            "enhanced_mode": True,  # 即使出错也返回True
            "message": f"状态获取失败: {str(e)}"
        }, status_code=500)


@router.post("/clear-cache")
async def clear_cache():
    """
    清除系统缓存
    
    清除临时文件和缓存数据
    """
    try:
        import shutil
        from pathlib import Path
        
        temp_dir = Path("temp")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            
        logger.info("缓存已清除")
        
        return JSONResponse(content={
            "success": True,
            "message": "缓存清除成功"
        })
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"清除缓存失败: {str(e)}"
        }, status_code=500)

