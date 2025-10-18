"""
上传进度WebSocket推送

实时推送上传进度到前端
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
import json
from services.upload_progress_manager import get_progress_manager, UploadProgress

router = APIRouter(prefix="/ws", tags=["websocket"])


class UploadWebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._broadcast_task: asyncio.Task = None
        
    async def connect(self, websocket: WebSocket):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # 如果是第一个连接，启动广播任务
        if len(self.active_connections) == 1 and not self._broadcast_task:
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        self.active_connections.discard(websocket)
        
        # 如果没有连接了，停止广播任务
        if len(self.active_connections) == 0 and self._broadcast_task:
            self._broadcast_task.cancel()
            self._broadcast_task = None
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def _broadcast_loop(self):
        """定期广播上传进度"""
        try:
            while True:
                # 每500ms广播一次进度
                await asyncio.sleep(0.5)
                
                # 获取所有上传任务的进度
                progress_mgr = get_progress_manager()
                progresses = await progress_mgr.list_progresses()
                
                if progresses:
                    message = {
                        "type": "upload_progress",
                        "data": {
                            "uploads": [
                                progress.to_dict()
                                for progress in progresses.values()
                            ]
                        }
                    }
                    await self.broadcast(message)
        except asyncio.CancelledError:
            pass


# 全局WebSocket管理器
ws_manager = UploadWebSocketManager()


@router.websocket("/upload/progress")
async def upload_progress_websocket(websocket: WebSocket):
    """
    上传进度WebSocket端点
    
    前端连接: ws://localhost:8000/ws/upload/progress
    
    消息格式:
    {
        "type": "upload_progress",
        "data": {
            "uploads": [
                {
                    "file_name": "video.mp4",
                    "status": "uploading",
                    "percentage": 45.5,
                    "speed_mbps": 2.5,
                    ...
                }
            ]
        }
    }
    """
    await ws_manager.connect(websocket)
    
    try:
        # 保持连接，处理客户端消息
        while True:
            # 接收客户端消息（用于心跳或控制）
            data = await websocket.receive_text()
            
            # 处理控制消息
            try:
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': message.get('timestamp')
                    })
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket异常: {e}")
        ws_manager.disconnect(websocket)

