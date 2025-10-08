"""
消息去重工具类
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select
from database import get_db
from models import MessageLog, get_local_now

class MessageDeduplicator:
    """消息去重器"""
    
    @staticmethod
    def calculate_content_hash(text: str) -> str:
        """
        计算消息内容的哈希值
        
        Args:
            text: 消息文本
            
        Returns:
            str: SHA256 哈希值
        """
        if not text:
            return ""
        # 标准化文本：去除首尾空格，统一换行符
        normalized_text = text.strip().replace('\r\n', '\n')
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def calculate_media_hash(media_id: str, media_type: str) -> str:
        """
        计算媒体文件的哈希值
        
        Args:
            media_id: 媒体文件ID
            media_type: 媒体类型
            
        Returns:
            str: SHA256 哈希值
        """
        if not media_id:
            return ""
        # 使用媒体ID和类型计算哈希
        content = f"{media_type}:{media_id}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    async def is_duplicate(
        rule_id: int,
        content_hash: str,
        media_hash: Optional[str],
        time_window: int,
        check_content: bool = True,
        check_media: bool = True
    ) -> bool:
        """
        检查消息是否重复
        
        Args:
            rule_id: 规则ID
            content_hash: 内容哈希
            media_hash: 媒体哈希
            time_window: 时间窗口（秒）
            check_content: 是否检查内容
            check_media: 是否检查媒体
            
        Returns:
            bool: 是否重复
        """
        try:
            async for db in get_db():
                # 计算时间窗口的起始时间
                window_start = get_local_now() - timedelta(seconds=time_window)
                
                # 构建查询条件
                query = select(MessageLog).where(
                    MessageLog.rule_id == rule_id,
                    MessageLog.created_at >= window_start,
                    MessageLog.status == 'success'  # 只检查成功转发的消息
                )
                
                # 根据配置添加哈希检查条件
                if check_content and content_hash:
                    query = query.where(MessageLog.content_hash == content_hash)
                
                if check_media and media_hash:
                    query = query.where(MessageLog.media_hash == media_hash)
                
                # 如果内容和媒体都不检查，则不算重复
                if not check_content and not check_media:
                    return False
                
                # 执行查询
                result = await db.execute(query.limit(1))
                duplicate = result.scalar_one_or_none()
                
                return duplicate is not None
                
        except Exception as e:
            # 出错时不阻止转发，记录日志
            print(f"检查消息重复失败: {e}")
            return False


class SenderFilter:
    """发送者过滤器"""
    
    @staticmethod
    def parse_sender_list(sender_list_json: Optional[str]) -> list:
        """
        解析发送者列表JSON
        
        Args:
            sender_list_json: JSON字符串
            
        Returns:
            list: 发送者列表 [{"id": "123", "username": "user1"}, ...]
        """
        if not sender_list_json:
            return []
        
        try:
            return json.loads(sender_list_json)
        except json.JSONDecodeError:
            return []
    
    @staticmethod
    def is_sender_allowed(
        sender_id: str,
        sender_username: Optional[str],
        filter_mode: str,
        whitelist_json: Optional[str],
        blacklist_json: Optional[str]
    ) -> bool:
        """
        检查发送者是否允许转发
        
        Args:
            sender_id: 发送者ID
            sender_username: 发送者用户名
            filter_mode: 过滤模式 ('whitelist' 或 'blacklist')
            whitelist_json: 白名单JSON
            blacklist_json: 黑名单JSON
            
        Returns:
            bool: 是否允许
        """
        if filter_mode == 'whitelist':
            # 白名单模式：只允许白名单中的发送者
            whitelist = SenderFilter.parse_sender_list(whitelist_json)
            if not whitelist:
                # 白名单为空，不允许任何人
                return False
            
            # 检查发送者是否在白名单中
            for sender in whitelist:
                if str(sender.get('id')) == str(sender_id):
                    return True
                if sender_username and sender.get('username') == sender_username:
                    return True
            
            return False
            
        elif filter_mode == 'blacklist':
            # 黑名单模式：阻止黑名单中的发送者
            blacklist = SenderFilter.parse_sender_list(blacklist_json)
            if not blacklist:
                # 黑名单为空，允许所有人
                return True
            
            # 检查发送者是否在黑名单中
            for sender in blacklist:
                if str(sender.get('id')) == str(sender_id):
                    return False
                if sender_username and sender.get('username') == sender_username:
                    return False
            
            return True
        
        # 未知模式，默认允许
        return True
    
    @staticmethod
    def get_sender_info(message: Any) -> Dict[str, Any]:
        """
        从Telethon消息对象提取发送者信息
        
        Args:
            message: Telethon消息对象
            
        Returns:
            dict: {"id": "123", "username": "user1", "first_name": "John"}
        """
        try:
            sender = message.sender
            if not sender:
                return {
                    "id": str(message.sender_id) if message.sender_id else None,
                    "username": None,
                    "first_name": None
                }
            
            return {
                "id": str(sender.id),
                "username": getattr(sender, 'username', None),
                "first_name": getattr(sender, 'first_name', None),
                "last_name": getattr(sender, 'last_name', None)
            }
        except Exception as e:
            print(f"提取发送者信息失败: {e}")
            return {"id": None, "username": None, "first_name": None}

