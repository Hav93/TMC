"""
115上传断点续传管理器

参考fake115uploader的断点续传设计
"""
import json
import os
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from pathlib import Path


class UploadSession:
    """上传会话"""
    
    def __init__(
        self,
        session_id: str,
        file_path: str,
        file_size: int,
        file_sha1: str,
        target_dir_id: str,
        total_parts: int = 0
    ):
        self.session_id = session_id
        self.file_path = file_path
        self.file_size = file_size
        self.file_sha1 = file_sha1
        self.target_dir_id = target_dir_id
        self.total_parts = total_parts
        self.uploaded_parts: List[int] = []  # 已上传的分片编号
        self.upload_id: str = ""  # OSS multipart upload ID
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            'session_id': self.session_id,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_sha1': self.file_sha1,
            'target_dir_id': self.target_dir_id,
            'total_parts': self.total_parts,
            'uploaded_parts': self.uploaded_parts,
            'upload_id': self.upload_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UploadSession':
        """从字典反序列化"""
        session = cls(
            session_id=data['session_id'],
            file_path=data['file_path'],
            file_size=data['file_size'],
            file_sha1=data['file_sha1'],
            target_dir_id=data['target_dir_id'],
            total_parts=data.get('total_parts', 0)
        )
        session.uploaded_parts = data.get('uploaded_parts', [])
        session.upload_id = data.get('upload_id', '')
        if 'created_at' in data:
            session.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            session.updated_at = datetime.fromisoformat(data['updated_at'])
        return session
    
    def get_progress(self) -> float:
        """获取上传进度（0-100）"""
        if self.total_parts == 0:
            return 0.0
        return (len(self.uploaded_parts) / self.total_parts) * 100
    
    def is_complete(self) -> bool:
        """是否已完成"""
        return self.total_parts > 0 and len(self.uploaded_parts) == self.total_parts
    
    def get_pending_parts(self) -> List[int]:
        """获取待上传的分片列表"""
        if self.total_parts == 0:
            return []
        all_parts = set(range(1, self.total_parts + 1))
        uploaded = set(self.uploaded_parts)
        return sorted(list(all_parts - uploaded))


class UploadResumeManager:
    """
    上传断点续传管理器
    
    功能：
    1. 保存上传会话到本地文件
    2. 恢复未完成的上传
    3. 跟踪分片上传进度
    4. 清理过期会话
    """
    
    def __init__(self, storage_dir: str = "./data/upload_sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{session_id}.json"
    
    def _generate_session_id(self, file_path: str, target_dir_id: str) -> str:
        """
        生成会话ID（基于文件路径和目标目录）
        
        相同文件上传到相同目录 = 相同session_id = 可以断点续传
        """
        content = f"{file_path}:{target_dir_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def create_session(
        self,
        file_path: str,
        file_size: int,
        file_sha1: str,
        target_dir_id: str,
        total_parts: int = 0
    ) -> UploadSession:
        """创建新的上传会话"""
        session_id = self._generate_session_id(file_path, target_dir_id)
        
        session = UploadSession(
            session_id=session_id,
            file_path=file_path,
            file_size=file_size,
            file_sha1=file_sha1,
            target_dir_id=target_dir_id,
            total_parts=total_parts
        )
        
        await self.save_session(session)
        return session
    
    async def get_session(
        self,
        file_path: str,
        target_dir_id: str
    ) -> Optional[UploadSession]:
        """获取现有会话（用于断点续传）"""
        session_id = self._generate_session_id(file_path, target_dir_id)
        session_file = self._get_session_file(session_id)
        
        if not session_file.exists():
            return None
        
        try:
            async with self._lock:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UploadSession.from_dict(data)
        except Exception as e:
            print(f"读取会话失败: {e}")
            return None
    
    async def save_session(self, session: UploadSession):
        """保存会话"""
        session.updated_at = datetime.now()
        session_file = self._get_session_file(session.session_id)
        
        async with self._lock:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
    
    async def update_progress(
        self,
        session: UploadSession,
        part_number: int
    ):
        """更新上传进度"""
        if part_number not in session.uploaded_parts:
            session.uploaded_parts.append(part_number)
            session.uploaded_parts.sort()
        await self.save_session(session)
    
    async def delete_session(self, session_id: str):
        """删除会话"""
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            async with self._lock:
                session_file.unlink()
    
    async def list_sessions(self) -> List[UploadSession]:
        """列出所有会话"""
        sessions = []
        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append(UploadSession.from_dict(data))
            except Exception:
                continue
        return sessions
    
    async def clean_expired_sessions(self, days: int = 7):
        """清理过期会话（超过N天未更新）"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        sessions = await self.list_sessions()
        
        for session in sessions:
            if session.updated_at < cutoff:
                await self.delete_session(session.session_id)


# 全局管理器实例
_resume_manager: Optional[UploadResumeManager] = None


def get_resume_manager() -> UploadResumeManager:
    """获取全局断点续传管理器"""
    global _resume_manager
    if _resume_manager is None:
        _resume_manager = UploadResumeManager()
    return _resume_manager

