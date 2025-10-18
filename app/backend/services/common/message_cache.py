"""
消息缓存管理器

功能：
1. 缓存消息处理结果，避免重复计算
2. 缓存链接提取结果
3. 缓存关键词匹配结果
4. 自动过期管理
5. 内存限制控制
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import hashlib
from collections import OrderedDict
from log_manager import get_logger
from timezone_utils import get_user_now

logger = get_logger("message_cache", "enhanced_bot.log")


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def is_expired(self, ttl: int) -> bool:
        """检查是否过期"""
        return (get_user_now() - self.created_at).total_seconds() > ttl
    
    def access(self):
        """记录访问"""
        self.last_accessed = get_user_now()
        self.access_count += 1


class MessageCacheManager:
    """
    消息缓存管理器
    
    特性：
    1. LRU缓存策略
    2. TTL自动过期
    3. 内存限制
    4. 统计信息
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,  # 默认1小时
        cleanup_interval: int = 300  # 5分钟清理一次
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        
        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_size': 0
        }
        
        # 启动清理任务
        self._cleanup_task = None
        self._is_running = False
    
    async def start(self):
        """启动缓存管理器"""
        if self._is_running:
            return
        
        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"✅ 消息缓存管理器已启动 (max_size={self.max_size}, ttl={self.default_ttl}s)")
    
    async def stop(self):
        """停止缓存管理器"""
        self._is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("✅ 消息缓存管理器已停止")
    
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.stats['misses'] += 1
                return default
            
            # 检查是否过期
            if entry.is_expired(self.default_ttl):
                del self._cache[key]
                self.stats['expirations'] += 1
                self.stats['misses'] += 1
                return default
            
            # 记录访问并移到末尾（LRU）
            entry.access()
            self._cache.move_to_end(key)
            self.stats['hits'] += 1
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        async with self._lock:
            # 如果已存在，更新
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.created_at = get_user_now()
                entry.last_accessed = get_user_now()
                self._cache.move_to_end(key)
                return
            
            # 检查容量限制
            if len(self._cache) >= self.max_size:
                # 移除最旧的条目（LRU）
                oldest_key, _ = self._cache.popitem(last=False)
                self.stats['evictions'] += 1
                logger.debug(f"缓存已满，移除最旧条目: {oldest_key}")
            
            # 添加新条目
            entry = CacheEntry(key=key, value=value)
            self._cache[key] = entry
            self.stats['total_size'] = len(self._cache)
    
    async def delete(self, key: str):
        """删除缓存值"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.stats['total_size'] = len(self._cache)
    
    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            self.stats['total_size'] = 0
            logger.info("缓存已清空")
    
    async def _cleanup_loop(self):
        """定期清理过期缓存"""
        while self._is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理缓存失败: {e}", exc_info=True)
    
    async def _cleanup_expired(self):
        """清理过期缓存"""
        async with self._lock:
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.is_expired(self.default_ttl):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self.stats['expirations'] += 1
            
            self.stats['total_size'] = len(self._cache)
            
            if expired_keys:
                logger.info(f"清理过期缓存: {len(expired_keys)} 条")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_size': self.stats['total_size'],
            'max_size': self.max_size,
            'usage_percent': (self.stats['total_size'] / self.max_size * 100) if self.max_size > 0 else 0,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'evictions': self.stats['evictions'],
            'expirations': self.stats['expirations']
        }
    
    # ===== 便捷方法：消息相关缓存 =====
    
    @staticmethod
    def _make_message_key(chat_id: int, message_id: int, suffix: str = "") -> str:
        """生成消息缓存键"""
        return f"msg:{chat_id}:{message_id}:{suffix}"
    
    async def cache_extracted_links(self, chat_id: int, message_id: int, links: Dict[str, List[str]]):
        """缓存提取的链接"""
        key = self._make_message_key(chat_id, message_id, "links")
        await self.set(key, links)
    
    async def get_extracted_links(self, chat_id: int, message_id: int) -> Optional[Dict[str, List[str]]]:
        """获取缓存的链接"""
        key = self._make_message_key(chat_id, message_id, "links")
        return await self.get(key)
    
    async def cache_matched_keywords(self, chat_id: int, message_id: int, keywords_hash: str, matched: List[str]):
        """缓存匹配的关键词"""
        key = self._make_message_key(chat_id, message_id, f"keywords:{keywords_hash}")
        await self.set(key, matched)
    
    async def get_matched_keywords(self, chat_id: int, message_id: int, keywords_hash: str) -> Optional[List[str]]:
        """获取缓存的关键词匹配结果"""
        key = self._make_message_key(chat_id, message_id, f"keywords:{keywords_hash}")
        return await self.get(key)
    
    async def cache_rule_match(self, chat_id: int, message_id: int, rule_id: int, matched: bool):
        """缓存规则匹配结果"""
        key = self._make_message_key(chat_id, message_id, f"rule:{rule_id}")
        await self.set(key, matched)
    
    async def get_rule_match(self, chat_id: int, message_id: int, rule_id: int) -> Optional[bool]:
        """获取缓存的规则匹配结果"""
        key = self._make_message_key(chat_id, message_id, f"rule:{rule_id}")
        return await self.get(key)
    
    @staticmethod
    def hash_keywords(keywords: List[str]) -> str:
        """计算关键词列表的哈希值"""
        keywords_str = "|".join(sorted(keywords))
        return hashlib.md5(keywords_str.encode()).hexdigest()[:8]


# 全局缓存管理器实例
_cache_manager: Optional[MessageCacheManager] = None


def get_message_cache() -> MessageCacheManager:
    """获取全局缓存管理器实例"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MessageCacheManager()
        logger.info("✅ 创建全局消息缓存管理器")
    return _cache_manager


async def init_message_cache():
    """初始化消息缓存管理器"""
    cache = get_message_cache()
    await cache.start()
    return cache

