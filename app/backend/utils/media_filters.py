"""
媒体文件过滤器
用于媒体监控规则的消息过滤
"""
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from log_manager import get_logger

logger = get_logger('media_filters')


class MediaFilter:
    """媒体文件过滤器"""
    
    @staticmethod
    def check_file_type(message, allowed_types: List[str]) -> bool:
        """
        检查文件类型是否允许
        
        Args:
            message: Telegram 消息对象
            allowed_types: 允许的类型列表 ['photo', 'video', 'audio', 'document']
            
        Returns:
            是否允许
        """
        if not allowed_types:
            return True
        
        if message.photo and 'photo' in allowed_types:
            return True
        if message.video and 'video' in allowed_types:
            return True
        if message.audio and 'audio' in allowed_types:
            return True
        if message.voice and 'audio' in allowed_types:
            return True
        if message.document and 'document' in allowed_types:
            return True
        
        return False
    
    @staticmethod
    def check_file_size(message, min_size_mb: int, max_size_mb: int) -> bool:
        """
        检查文件大小是否在范围内
        
        Args:
            message: Telegram 消息对象
            min_size_mb: 最小文件大小(MB)
            max_size_mb: 最大文件大小(MB)
            
        Returns:
            是否在范围内
        """
        file_size = MediaFilter.get_file_size(message)
        
        if file_size is None:
            return True
        
        file_size_mb = file_size / (1024 * 1024)
        
        if min_size_mb and file_size_mb < min_size_mb:
            return False
        
        if max_size_mb and file_size_mb > max_size_mb:
            return False
        
        return True
    
    @staticmethod
    def check_filename(
        message,
        include_keywords: Optional[str],
        exclude_keywords: Optional[str]
    ) -> bool:
        """
        检查文件名是否匹配关键词
        
        Args:
            message: Telegram 消息对象
            include_keywords: 包含关键词（逗号分隔）
            exclude_keywords: 排除关键词（逗号分隔）
            
        Returns:
            是否匹配
        """
        filename = MediaFilter.get_filename(message)
        
        if not filename:
            return True
        
        filename_lower = filename.lower()
        
        # 检查包含关键词
        if include_keywords:
            keywords = [k.strip().lower() for k in include_keywords.split(',') if k.strip()]
            if keywords and not any(kw in filename_lower for kw in keywords):
                return False
        
        # 检查排除关键词
        if exclude_keywords:
            keywords = [k.strip().lower() for k in exclude_keywords.split(',') if k.strip()]
            if keywords and any(kw in filename_lower for kw in keywords):
                return False
        
        return True
    
    @staticmethod
    def check_file_extension(message, allowed_extensions: List[str]) -> bool:
        """
        检查文件扩展名是否允许
        
        Args:
            message: Telegram 消息对象
            allowed_extensions: 允许的扩展名列表 ['.mp4', '.mkv', ...]
            
        Returns:
            是否允许
        """
        if not allowed_extensions:
            return True
        
        filename = MediaFilter.get_filename(message)
        
        if not filename:
            return True
        
        file_ext = Path(filename).suffix.lower()
        
        return file_ext in [ext.lower() for ext in allowed_extensions]
    
    @staticmethod
    def get_file_type(message) -> Optional[str]:
        """
        获取文件类型
        
        Returns:
            'photo', 'video', 'audio', 'document' 或 None
        """
        if message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.audio or message.voice:
            return 'audio'
        elif message.document:
            return 'document'
        return None
    
    @staticmethod
    def get_file_size(message) -> Optional[int]:
        """
        获取文件大小（字节）
        
        Returns:
            文件大小或 None
        """
        if message.photo:
            # 照片：获取最大尺寸的照片
            sizes = message.photo.sizes if hasattr(message.photo, 'sizes') else [message.photo]
            return max(sizes, key=lambda s: s.size if hasattr(s, 'size') else 0).size if sizes else None
        elif message.video:
            return message.video.size if hasattr(message.video, 'size') else None
        elif message.audio:
            return message.audio.size if hasattr(message.audio, 'size') else None
        elif message.voice:
            return message.voice.size if hasattr(message.voice, 'size') else None
        elif message.document:
            return message.document.size if hasattr(message.document, 'size') else None
        return None
    
    @staticmethod
    def get_filename(message) -> Optional[str]:
        """
        获取文件名
        
        Returns:
            文件名或 None
        """
        if message.document:
            # 文档类型直接有文件名
            if hasattr(message.document, 'attributes'):
                for attr in message.document.attributes:
                    if hasattr(attr, 'file_name'):
                        return attr.file_name
        elif message.video:
            # 视频可能有文件名属性
            if hasattr(message.video, 'attributes'):
                for attr in message.video.attributes:
                    if hasattr(attr, 'file_name'):
                        return attr.file_name
        elif message.audio:
            # 音频可能有文件名或标题
            if hasattr(message.audio, 'attributes'):
                for attr in message.audio.attributes:
                    if hasattr(attr, 'file_name'):
                        return attr.file_name
            # 尝试从标题和艺术家构建文件名
            if hasattr(message.audio, 'title') and message.audio.title:
                return f"{message.audio.title}.mp3"
        elif message.photo:
            # 照片通常没有文件名，生成一个
            return f"photo_{message.id}.jpg"
        
        return None
    
    @staticmethod
    def get_media_info(message) -> Dict[str, Any]:
        """
        获取媒体文件的完整信息
        
        Returns:
            包含类型、大小、文件名等信息的字典
        """
        return {
            'type': MediaFilter.get_file_type(message),
            'size': MediaFilter.get_file_size(message),
            'size_mb': round(MediaFilter.get_file_size(message) / (1024 * 1024), 2) if MediaFilter.get_file_size(message) else 0,
            'filename': MediaFilter.get_filename(message),
            'extension': Path(MediaFilter.get_filename(message)).suffix if MediaFilter.get_filename(message) else None,
            'message_id': message.id,
            'date': message.date
        }


class SenderFilter:
    """发送者过滤器（复用现有的发送者过滤逻辑）"""
    
    @staticmethod
    def parse_sender_list(sender_list_text: Optional[str]) -> List[Dict[str, Optional[str]]]:
        """
        解析发送者列表（支持简单文本格式）
        
        格式：@username1, @username2, 123456, @username3
        
        Returns:
            [{"id": "123456", "username": None}, {"id": None, "username": "username1"}, ...]
        """
        if not sender_list_text:
            return []
        
        sender_list_text = sender_list_text.strip()
        
        # 尝试解析为JSON（兼容旧版）
        if sender_list_text.startswith('[') or sender_list_text.startswith('{'):
            try:
                return json.loads(sender_list_text)
            except json.JSONDecodeError:
                pass
        
        # 解析为简单文本格式
        result = []
        items = [item.strip() for item in sender_list_text.split(',') if item.strip()]
        
        for item in items:
            # 去除 @ 符号
            item = item.lstrip('@')
            
            if not item:
                continue
            
            # 判断是用户名还是ID
            if item.isdigit():
                # 纯数字，当作ID
                result.append({"id": item, "username": None})
            else:
                # 包含字母，当作用户名
                result.append({"id": None, "username": item})
        
        return result
    
    @staticmethod
    def is_sender_allowed(
        sender_id: str,
        sender_username: Optional[str],
        filter_mode: str,
        whitelist: Optional[str],
        blacklist: Optional[str]
    ) -> bool:
        """
        检查发送者是否允许
        
        Args:
            sender_id: 发送者ID
            sender_username: 发送者用户名
            filter_mode: 过滤模式 ('whitelist' 或 'blacklist')
            whitelist: 白名单文本
            blacklist: 黑名单文本
            
        Returns:
            是否允许
        """
        if filter_mode == 'whitelist':
            # 白名单模式：只允许名单中的发送者
            if not whitelist:
                return True
            
            allowed_senders = SenderFilter.parse_sender_list(whitelist)
            return SenderFilter._is_in_sender_list(sender_id, sender_username, allowed_senders)
        
        elif filter_mode == 'blacklist':
            # 黑名单模式：阻止名单中的发送者
            if not blacklist:
                return True
            
            blocked_senders = SenderFilter.parse_sender_list(blacklist)
            return not SenderFilter._is_in_sender_list(sender_id, sender_username, blocked_senders)
        
        return True
    
    @staticmethod
    def _is_in_sender_list(
        sender_id: str,
        sender_username: Optional[str],
        sender_list: List[Dict[str, Optional[str]]]
    ) -> bool:
        """检查发送者是否在列表中"""
        for item in sender_list:
            # 匹配ID
            if item.get('id') and str(item['id']) == str(sender_id):
                return True
            
            # 匹配用户名
            if item.get('username') and sender_username:
                if item['username'].lower() == sender_username.lower():
                    return True
        
        return False
    
    @staticmethod
    def get_sender_info(message) -> Dict[str, Any]:
        """
        获取发送者信息
        
        Returns:
            包含 id 和 username 的字典
        """
        sender = message.sender
        
        if sender:
            return {
                'id': str(sender.id) if hasattr(sender, 'id') else None,
                'username': sender.username if hasattr(sender, 'username') else None,
                'first_name': sender.first_name if hasattr(sender, 'first_name') else None,
                'last_name': sender.last_name if hasattr(sender, 'last_name') else None
            }
        
        return {
            'id': None,
            'username': None,
            'first_name': None,
            'last_name': None
        }


# 测试函数
def test_sender_filter():
    """测试发送者过滤器"""
    # 测试简单文本格式解析
    test_cases = [
        "@alice, @bob, 123456, @charlie",
        "alice, 123456, 789012",
        "@user1, @user2",
        "111, 222, 333"
    ]
    
    for test_text in test_cases:
        result = SenderFilter.parse_sender_list(test_text)
        print(f"输入: {test_text}")
        print(f"解析结果: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    # 测试白名单
    whitelist = "@alice, 123456"
    print(f"白名单: {whitelist}")
    print(f"alice 是否允许: {SenderFilter.is_sender_allowed('999', 'alice', 'whitelist', whitelist, None)}")
    print(f"123456 是否允许: {SenderFilter.is_sender_allowed('123456', None, 'whitelist', whitelist, None)}")
    print(f"bob 是否允许: {SenderFilter.is_sender_allowed('888', 'bob', 'whitelist', whitelist, None)}")
    
    # 测试黑名单
    blacklist = "@spammer, 999999"
    print(f"\n黑名单: {blacklist}")
    print(f"alice 是否允许: {SenderFilter.is_sender_allowed('111', 'alice', 'blacklist', None, blacklist)}")
    print(f"spammer 是否允许: {SenderFilter.is_sender_allowed('222', 'spammer', 'blacklist', None, blacklist)}")
    print(f"999999 是否允许: {SenderFilter.is_sender_allowed('999999', None, 'blacklist', None, blacklist)}")


if __name__ == '__main__':
    test_sender_filter()

