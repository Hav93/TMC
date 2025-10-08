"""
数据模型定义
"""
from datetime import datetime, timezone
import os
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import bcrypt

Base = declarative_base()

def get_local_now():
    """获取本地时区的当前时间 - 使用统一时区处理"""
    try:
        from timezone_utils import get_current_time
        return get_current_time()
    except ImportError:
        # 如果timezone_utils不可用，使用默认逻辑
        try:
            import pytz
            import os
            tz_name = os.environ.get('TZ', 'Asia/Shanghai')  # 默认改为中国时区
            if tz_name == 'UTC':
                return datetime.now(pytz.UTC)
            else:
                try:
                    tz = pytz.timezone(tz_name)
                    return datetime.now(tz)
                except pytz.UnknownTimeZoneError:
                    # 如果时区无效，使用Asia/Shanghai
                    return datetime.now(pytz.timezone('Asia/Shanghai'))
        except ImportError:
            # 如果pytz不可用，使用系统本地时间
            return datetime.now()

class ForwardRule(Base):
    """转发规则模型"""
    __tablename__ = 'forward_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    source_chat_id = Column(String(50), nullable=False, comment='源聊天ID')
    source_chat_name = Column(String(200), comment='源聊天名称')
    target_chat_id = Column(String(50), nullable=False, comment='目标聊天ID')
    target_chat_name = Column(String(200), comment='目标聊天名称')
    
    # 功能开关
    is_active = Column(Boolean, default=True, comment='是否启用')
    enable_keyword_filter = Column(Boolean, default=False, comment='是否启用关键词过滤')
    enable_regex_replace = Column(Boolean, default=False, comment='是否启用正则替换')
    
    # 客户端选择
    client_id = Column(String(50), default='main_user', comment='使用的客户端ID')
    client_type = Column(String(20), default='user', comment='客户端类型: user/bot')
    
    # 消息类型支持
    enable_text = Column(Boolean, default=True, comment='是否转发文本消息')
    enable_media = Column(Boolean, default=True, comment='是否转发媒体文件')
    enable_photo = Column(Boolean, default=True, comment='是否转发图片')
    enable_video = Column(Boolean, default=True, comment='是否转发视频')
    enable_document = Column(Boolean, default=True, comment='是否转发文档')
    enable_audio = Column(Boolean, default=True, comment='是否转发音频')
    enable_voice = Column(Boolean, default=True, comment='是否转发语音')
    enable_sticker = Column(Boolean, default=False, comment='是否转发贴纸')
    enable_animation = Column(Boolean, default=True, comment='是否转发动图')
    enable_webpage = Column(Boolean, default=True, comment='是否转发网页预览')
    
    # 高级设置
    forward_delay = Column(Integer, default=0, comment='转发延迟(秒)')
    max_message_length = Column(Integer, default=4096, comment='最大消息长度')
    enable_link_preview = Column(Boolean, default=True, comment='是否启用链接预览')
    
    # 时间过滤设置
    time_filter_type = Column(String(20), default='after_start', comment='时间过滤类型: after_start(启动后), time_range(时间段), from_time(指定时间开始), today_only(仅当天), all_messages(所有消息)')
    start_time = Column(DateTime, comment='开始时间(用于time_range和from_time类型)')
    end_time = Column(DateTime, comment='结束时间(用于time_range类型)')
    
    # 【新功能】消息去重设置
    enable_deduplication = Column(Boolean, default=False, comment='是否启用消息去重')
    dedup_time_window = Column(Integer, default=3600, comment='去重时间窗口(秒)，默认1小时')
    dedup_check_content = Column(Boolean, default=True, comment='去重时检查消息内容')
    dedup_check_media = Column(Boolean, default=True, comment='去重时检查媒体文件')
    
    # 【新功能】发送者过滤设置
    enable_sender_filter = Column(Boolean, default=False, comment='是否启用发送者过滤')
    sender_filter_mode = Column(String(20), default='whitelist', comment='发送者过滤模式: whitelist(白名单), blacklist(黑名单)')
    sender_whitelist = Column(Text, comment='发送者白名单，JSON数组格式：[{"id":"123","username":"user1"},...]')
    sender_blacklist = Column(Text, comment='发送者黑名单，JSON数组格式：[{"id":"456","username":"user2"},...]')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    # 关系
    keywords = relationship("Keyword", back_populates="rule", cascade="all, delete-orphan")
    replace_rules = relationship("ReplaceRule", back_populates="rule", cascade="all, delete-orphan")
    message_logs = relationship("MessageLog", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ForwardRule(id={self.id}, name='{self.name}')>"

class Keyword(Base):
    """关键词模型"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=False)
    keyword = Column(String(500), nullable=False, comment='关键词')
    is_regex = Column(Boolean, default=False, comment='是否为正则表达式')
    is_exclude = Column(Boolean, default=False, comment='是否为排除关键词')
    case_sensitive = Column(Boolean, default=False, comment='是否区分大小写')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="keywords")
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword='{self.keyword}')>"

class ReplaceRule(Base):
    """替换规则模型"""
    __tablename__ = 'replace_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=False)
    name = Column(String(100), comment='替换规则名称')
    pattern = Column(Text, nullable=False, comment='正则表达式模式')
    replacement = Column(Text, nullable=False, comment='替换内容')
    priority = Column(Integer, default=0, comment='优先级，数字越小优先级越高')
    is_regex = Column(Boolean, default=True, comment='是否为正则表达式')
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_global = Column(Boolean, default=False, comment='是否全局替换')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="replace_rules")
    
    def __repr__(self):
        return f"<ReplaceRule(id={self.id}, name='{self.name}')>"

class MessageLog(Base):
    """消息日志模型"""
    __tablename__ = 'message_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('forward_rules.id'), nullable=True)
    rule_name = Column(String(100), comment='规则名称（用于稳定关联）')
    
    # 源消息信息
    source_chat_id = Column(String(50), nullable=False, comment='源聊天ID')
    source_chat_name = Column(String(200), comment='源聊天名称')
    source_message_id = Column(Integer, nullable=False, comment='源消息ID')
    
    # 目标消息信息
    target_chat_id = Column(String(50), nullable=False, comment='目标聊天ID')
    target_chat_name = Column(String(200), comment='目标聊天名称')
    target_message_id = Column(Integer, comment='目标消息ID')
    
    # 消息内容
    original_text = Column(Text, comment='原始消息文本')
    processed_text = Column(Text, comment='处理后消息文本')
    media_type = Column(String(50), comment='媒体类型')
    
    # 【新功能】消息指纹（用于去重）
    content_hash = Column(String(64), index=True, comment='消息内容哈希值（用于去重）')
    media_hash = Column(String(64), comment='媒体文件哈希值（如果有）')
    sender_id = Column(String(50), comment='发送者ID')
    sender_username = Column(String(100), comment='发送者用户名')
    
    # 状态信息
    status = Column(String(20), default='success', comment='转发状态')
    error_message = Column(Text, comment='错误信息')
    processing_time = Column(Integer, comment='处理时间(毫秒)')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    # 关系
    rule = relationship("ForwardRule", back_populates="message_logs")
    
    def __repr__(self):
        return f"<MessageLog(id={self.id}, status='{self.status}')>"

class UserSession(Base):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, comment='用户ID')
    username = Column(String(100), comment='用户名')
    first_name = Column(String(100), comment='名字')
    last_name = Column(String(100), comment='姓氏')
    phone_number = Column(String(20), comment='手机号码')
    is_admin = Column(Boolean, default=False, comment='是否为管理员')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    last_activity = Column(DateTime, default=get_local_now, comment='最后活动时间')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"

class TelegramClient(Base):
    """Telegram客户端配置模型"""
    __tablename__ = 'telegram_clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), unique=True, nullable=False, comment='客户端ID')
    client_type = Column(String(20), nullable=False, comment='客户端类型: user/bot')
    
    # 机器人客户端配置
    bot_token = Column(String(500), comment='机器人Token')
    admin_user_id = Column(String(50), comment='管理员用户ID')
    
    # 用户客户端配置
    api_id = Column(String(50), comment='Telegram API ID')
    api_hash = Column(String(100), comment='Telegram API Hash')
    phone = Column(String(20), comment='手机号')
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment='是否启用')
    auto_start = Column(Boolean, default=False, comment='是否自动启动')
    last_connected = Column(DateTime, comment='最后连接时间')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    def __repr__(self):
        return f"<TelegramClient(id={self.id}, client_id='{self.client_id}', type='{self.client_type}')>"

class BotSettings(Base):
    """机器人设置模型"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, comment='设置键')
    value = Column(Text, comment='设置值')
    description = Column(String(500), comment='设置描述')
    data_type = Column(String(20), default='string', comment='数据类型')
    is_system = Column(Boolean, default=False, comment='是否为系统设置')
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    def __repr__(self):
        return f"<BotSettings(key='{self.key}', value='{self.value}')>"

# 数据库操作辅助类
class DatabaseHelper:
    """数据库操作辅助类"""
    
    @staticmethod
    def create_default_settings():
        """创建默认设置"""
        default_settings = [
            {
                'key': 'max_forward_delay',
                'value': '5',
                'description': '最大转发延迟(秒)',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'enable_media_forward',
                'value': 'true',
                'description': '是否启用媒体转发',
                'data_type': 'boolean',
                'is_system': True
            },
            {
                'key': 'max_message_length',
                'value': '4096',
                'description': '最大消息长度',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'log_retention_days',
                'value': '30',
                'description': '日志保留天数',
                'data_type': 'integer',
                'is_system': True
            },
            {
                'key': 'enable_debug_mode',
                'value': 'false',
                'description': '是否启用调试模式',
                'data_type': 'boolean',
                'is_system': False
            }
        ]
        
        return default_settings
    
    @staticmethod
    def get_table_names():
        """获取所有表名"""
        return [
            'forward_rules',
            'keywords',
            'replace_rules',
            'message_logs',
            'user_sessions',
            'telegram_clients',
            'bot_settings',
            'users',
            'media_monitor_rules',
            'download_tasks',
            'media_files'
        ]

class User(Base):
    """用户模型 - 用于Web登录认证"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=True, comment='邮箱')
    password_hash = Column(String(128), nullable=False, comment='密码哈希')
    full_name = Column(String(100), comment='全名')
    avatar = Column(String(500), comment='头像URL或Base64')
    
    # 权限和状态
    is_active = Column(Boolean, default=True, comment='是否激活')
    is_admin = Column(Boolean, default=False, comment='是否为管理员')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    last_login = Column(DateTime, comment='最后登录时间')
    
    def set_password(self, password: str):
        """设置密码"""
        # 使用bcrypt加密密码
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# ==================== 媒体文件管理模型 ====================

class MediaMonitorRule(Base):
    """媒体监控规则模型"""
    __tablename__ = 'media_monitor_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    description = Column(Text, comment='规则描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    client_id = Column(String(50), nullable=False, comment='使用的客户端ID')
    
    # 监听源（JSON数组格式）
    source_chats = Column(Text, comment='监听的频道/群组列表，JSON格式：["channel_123", "group_456"]')
    
    # 媒体过滤
    media_types = Column(Text, comment='文件类型过滤，JSON格式：["photo", "video", "audio", "document"]')
    min_size_mb = Column(Integer, default=0, comment='最小文件大小(MB)')
    max_size_mb = Column(Integer, default=2000, comment='最大文件大小(MB)')
    filename_include = Column(Text, comment='文件名包含关键词（逗号分隔）')
    filename_exclude = Column(Text, comment='文件名排除关键词（逗号分隔）')
    file_extensions = Column(Text, comment='允许的文件扩展名，JSON格式：[".mp4", ".mkv"]')
    
    # 发送者过滤
    enable_sender_filter = Column(Boolean, default=False, comment='是否启用发送者过滤')
    sender_filter_mode = Column(String(20), default='whitelist', comment='过滤模式：whitelist/blacklist')
    sender_whitelist = Column(Text, comment='发送者白名单（简单文本格式：@user1, @user2, 123456）')
    sender_blacklist = Column(Text, comment='发送者黑名单（简单文本格式）')
    
    # 下载设置
    temp_folder = Column(String(255), default='/app/media/downloads', comment='临时下载文件夹')
    concurrent_downloads = Column(Integer, default=3, comment='并发下载数量')
    retry_on_failure = Column(Boolean, default=True, comment='失败时是否重试')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    
    # 元数据提取
    extract_metadata = Column(Boolean, default=True, comment='是否提取元数据')
    metadata_mode = Column(String(20), default='lightweight', comment='元数据提取模式：disabled/lightweight/full')
    metadata_timeout = Column(Integer, default=10, comment='元数据提取超时（秒）')
    async_metadata_extraction = Column(Boolean, default=True, comment='是否异步提取元数据')
    
    # 归档配置
    organize_enabled = Column(Boolean, default=False, comment='是否启用文件归档')
    organize_target_type = Column(String(20), default='local', comment='归档目标：local/clouddrive_mount/clouddrive_api')
    organize_local_path = Column(String(255), comment='本地归档路径')
    organize_clouddrive_mount = Column(String(255), comment='CloudDrive挂载路径')
    organize_mode = Column(String(20), default='copy', comment='归档方式：copy/move')
    keep_temp_file = Column(Boolean, default=False, comment='归档后是否保留临时文件')
    
    # CloudDrive API配置
    clouddrive_enabled = Column(Boolean, default=False, comment='是否启用CloudDrive API上传')
    clouddrive_url = Column(String(255), comment='CloudDrive服务地址')
    clouddrive_username = Column(String(100), comment='CloudDrive用户名')
    clouddrive_password = Column(String(255), comment='CloudDrive密码（加密存储）')
    clouddrive_remote_path = Column(String(255), comment='CloudDrive远程路径')
    
    # 文件夹结构
    folder_structure = Column(String(50), default='date', comment='文件夹组织方式：flat/date/type/source/sender/custom')
    custom_folder_template = Column(String(255), comment='自定义文件夹模板：{year}/{month}/{type}')
    rename_files = Column(Boolean, default=False, comment='是否重命名文件')
    filename_template = Column(String(255), comment='文件名模板：{date}_{sender}_{original_name}')
    
    # 清理设置
    auto_cleanup_enabled = Column(Boolean, default=True, comment='是否启用自动清理')
    auto_cleanup_days = Column(Integer, default=7, comment='自动清理天数')
    cleanup_only_organized = Column(Boolean, default=True, comment='是否只清理已归档文件')
    
    # 存储容量限制
    max_storage_gb = Column(Integer, default=100, comment='最大存储容量(GB)')
    
    # 统计数据
    total_downloaded = Column(Integer, default=0, comment='累计下载数量')
    total_size_mb = Column(Integer, default=0, comment='累计下载大小(MB)')
    last_download_at = Column(DateTime, comment='最后下载时间')
    failed_downloads = Column(Integer, default=0, comment='失败下载数量')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    # 关系
    download_tasks = relationship("DownloadTask", back_populates="monitor_rule", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="monitor_rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MediaMonitorRule(id={self.id}, name='{self.name}', active={self.is_active})>"


class DownloadTask(Base):
    """下载任务模型"""
    __tablename__ = 'download_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_rule_id = Column(Integer, ForeignKey('media_monitor_rules.id'), nullable=False, comment='关联的监控规则ID')
    message_id = Column(Integer, comment='消息ID')
    chat_id = Column(String(50), comment='聊天ID')
    
    # 文件信息
    file_name = Column(String(255), comment='文件名')
    file_type = Column(String(50), comment='文件类型：photo/video/audio/document')
    file_size_mb = Column(Integer, comment='文件大小(MB)')
    
    # 任务状态
    status = Column(String(20), default='pending', comment='任务状态：pending/downloading/success/failed/retrying/paused')
    priority = Column(Integer, default=0, comment='优先级：-10到10')
    
    # 下载进度
    downloaded_bytes = Column(Integer, default=0, comment='已下载字节数')
    total_bytes = Column(Integer, comment='总字节数')
    progress_percent = Column(Integer, default=0, comment='进度百分比')
    download_speed_mbps = Column(Integer, comment='下载速度(MB/s)')
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment='重试次数')
    max_retries = Column(Integer, default=3, comment='最大重试次数')
    last_error = Column(Text, comment='最后一次错误信息')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    started_at = Column(DateTime, comment='开始下载时间')
    completed_at = Column(DateTime, comment='完成时间')
    failed_at = Column(DateTime, comment='失败时间')
    
    # 关系
    monitor_rule = relationship("MediaMonitorRule", back_populates="download_tasks")
    media_file = relationship("MediaFile", back_populates="download_task", uselist=False)
    
    def __repr__(self):
        return f"<DownloadTask(id={self.id}, file='{self.file_name}', status='{self.status}')>"


class MediaFile(Base):
    """媒体文件模型"""
    __tablename__ = 'media_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_rule_id = Column(Integer, ForeignKey('media_monitor_rules.id'), nullable=False, comment='关联的监控规则ID')
    download_task_id = Column(Integer, ForeignKey('download_tasks.id'), comment='关联的下载任务ID')
    message_id = Column(Integer, comment='消息ID')
    
    # 文件路径
    temp_path = Column(String(500), comment='临时文件路径')
    final_path = Column(String(500), comment='最终归档路径')
    clouddrive_path = Column(String(500), comment='CloudDrive远程路径')
    file_hash = Column(String(64), unique=True, comment='文件哈希(SHA-256)，用于去重')
    
    # 基础信息
    file_name = Column(String(255), comment='文件名')
    file_type = Column(String(50), comment='文件类型：image/video/audio/document')
    file_size_mb = Column(Integer, comment='文件大小(MB)')
    extension = Column(String(10), comment='文件扩展名')
    original_name = Column(String(255), comment='原始文件名')
    
    # 元数据（JSON存储）
    metadata = Column(Text, comment='完整元数据JSON')
    
    # 快捷字段（从metadata提取，方便查询）
    width = Column(Integer, comment='宽度（图片/视频）')
    height = Column(Integer, comment='高度（图片/视频）')
    duration_seconds = Column(Integer, comment='时长（视频/音频）')
    resolution = Column(String(20), comment='分辨率')
    codec = Column(String(50), comment='编码格式')
    bitrate_kbps = Column(Integer, comment='比特率(kbps)')
    
    # 来源信息
    source_chat = Column(String(100), comment='来源频道/群组')
    sender_id = Column(String(50), comment='发送者ID')
    sender_username = Column(String(100), comment='发送者用户名')
    
    # 状态
    is_organized = Column(Boolean, default=False, comment='是否已归档')
    is_uploaded_to_cloud = Column(Boolean, default=False, comment='是否已上传到云端')
    is_starred = Column(Boolean, default=False, comment='是否收藏')
    
    # 时间戳
    downloaded_at = Column(DateTime, default=get_local_now, comment='下载时间')
    organized_at = Column(DateTime, comment='归档时间')
    uploaded_at = Column(DateTime, comment='上传时间')
    
    # 关系
    monitor_rule = relationship("MediaMonitorRule", back_populates="media_files")
    download_task = relationship("DownloadTask", back_populates="media_file")
    
    def __repr__(self):
        return f"<MediaFile(id={self.id}, name='{self.file_name}', type='{self.file_type}')>"
