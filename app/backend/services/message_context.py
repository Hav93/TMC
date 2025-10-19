"""
消息处理上下文

提供安全的消息处理上下文，封装客户端操作，处理事件循环问题
"""
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
import asyncio

@dataclass
class MessageContext:
    """
    消息处理上下文
    
    作用：
    1. 封装消息和客户端管理器
    2. 提供安全的客户端操作方法
    3. 处理事件循环问题
    4. 缓存处理结果，避免重复计算
    5. 集成全局缓存和过滤引擎
    """
    
    message: Any  # Telethon Message 对象
    client_manager: Any  # TelegramClientManager 实例
    chat_id: int
    is_edited: bool = False
    
    # 本地缓存（用于单次处理）
    _extracted_links: Optional[Dict[str, List[str]]] = field(default=None, repr=False)
    _matched_keywords: Optional[Dict] = field(default_factory=dict, repr=False)
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        """
        安全地发送消息
        
        自动处理：
        - 事件循环切换
        - 连接状态检查
        - 超时控制
        """
        return await self.client_manager._safe_send_message(
            chat_id, text, **kwargs
        )
    
    async def download_media(self, file_path: str):
        """安全地下载媒体"""
        return await self.client_manager._safe_download_media(
            self.message, file_path
        )
    
    def is_connected(self) -> bool:
        """检查客户端连接状态"""
        return self.client_manager.connected
    
    async def get_extracted_links(self) -> Dict[str, List[str]]:
        """获取提取的链接（带全局缓存）"""
        # 优先使用本地缓存
        if self._extracted_links is not None:
            return self._extracted_links
        
        # 尝试从全局缓存获取
        try:
            from services.common.message_cache import get_message_cache
            cache = get_message_cache()
            
            message_id = self.message.id if self.message else 0
            cached_links = await cache.get_extracted_links(self.chat_id, message_id)
            
            if cached_links is not None:
                self._extracted_links = cached_links
                return cached_links
        except Exception:
            pass  # 缓存失败不影响功能
        
        # 提取链接
        from services.resource_monitor_service import LinkExtractor
        self._extracted_links = LinkExtractor.extract_all(
            self.message.text or ""
        )
        
        # 保存到全局缓存
        try:
            from services.common.message_cache import get_message_cache
            cache = get_message_cache()
            message_id = self.message.id if self.message else 0
            await cache.cache_extracted_links(self.chat_id, message_id, self._extracted_links)
        except Exception:
            pass
        
        return self._extracted_links
    
    async def get_matched_keywords(self, keywords: List[str]) -> List[str]:
        """获取匹配的关键词（带全局缓存和共享过滤引擎）"""
        cache_key = tuple(sorted(keywords))
        
        # 优先使用本地缓存
        if cache_key in self._matched_keywords:
            return self._matched_keywords[cache_key]
        
        # 尝试从全局缓存获取
        try:
            from services.common.message_cache import get_message_cache, MessageCacheManager
            cache = get_message_cache()
            
            message_id = self.message.id if self.message else 0
            keywords_hash = MessageCacheManager.hash_keywords(keywords)
            cached_matched = await cache.get_matched_keywords(
                self.chat_id, message_id, keywords_hash
            )
            
            if cached_matched is not None:
                self._matched_keywords[cache_key] = cached_matched
                return cached_matched
        except Exception:
            pass
        
        # 使用共享过滤引擎匹配
        try:
            from services.common.filter_engine import get_filter_engine
            filter_engine = get_filter_engine()
            
            message_text = self.message.text or ""
            matched = filter_engine.match_keywords(message_text, keywords)
        except Exception:
            # 回退到简单匹配
            matched = []
            message_text = (self.message.text or "").lower()
            for keyword in keywords:
                if keyword.lower() in message_text:
                    matched.append(keyword)
        
        # 保存到缓存
        self._matched_keywords[cache_key] = matched
        
        try:
            from services.common.message_cache import get_message_cache, MessageCacheManager
            cache = get_message_cache()
            message_id = self.message.id if self.message else 0
            keywords_hash = MessageCacheManager.hash_keywords(keywords)
            await cache.cache_matched_keywords(
                self.chat_id, message_id, keywords_hash, matched
            )
        except Exception:
            pass
        
        return matched
    
    def __repr__(self):
        return f"<MessageContext(chat_id={self.chat_id}, message_id={self.message.id if self.message else None})>"

