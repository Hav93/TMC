#!/usr/bin/env python3
"""
Telegram客户端管理器 - 解决事件循环冲突的核心模块
"""
import asyncio
import threading
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone, timedelta
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, ChatAdminRequiredError, UserPrivacyRestrictedError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from config import Config
from database import get_db
from models import ForwardRule, MessageLog, get_local_now
from filters import KeywordFilter, RegexReplacer
from proxy_utils import get_proxy_manager
from log_manager import get_logger
from services.message_context import MessageContext
from services.message_dispatcher import get_message_dispatcher
from services.resource_monitor_service import ResourceMonitorProcessor

logger = logging.getLogger(__name__)


class LoginErrorHandler:
    """统一处理 Telegram 登录错误"""
    
    @staticmethod
    def handle_error(error: Exception) -> Dict[str, Any]:
        """
        统一处理 Telegram 错误，返回友好的错误信息
        
        Args:
            error: Telegram 异常
            
        Returns:
            包含 success, message, error_type 的字典
        """
        try:
            from telethon.errors import (
                SessionPasswordNeededError,
                PhoneCodeInvalidError,
                PhoneCodeExpiredError,
                FloodWaitError,
                PhoneNumberInvalidError,
                PhoneNumberBannedError,
                PhoneNumberUnoccupiedError
            )
            
            if isinstance(error, SessionPasswordNeededError):
                return {
                    "success": True,  # 需要密码不算失败
                    "message": "需要输入二步验证密码",
                    "step": "waiting_password",
                    "error_type": "need_password"
                }
            elif isinstance(error, PhoneCodeInvalidError):
                return {
                    "success": False,
                    "message": "验证码错误，请检查后重新输入",
                    "error_type": "invalid_code"
                }
            elif isinstance(error, PhoneCodeExpiredError):
                return {
                    "success": False,
                    "message": "验证码已过期，请重新发送",
                    "error_type": "code_expired",
                    "should_resend": True
                }
            elif isinstance(error, FloodWaitError):
                wait_seconds = getattr(error, 'seconds', 60)
                wait_minutes = wait_seconds // 60
                if wait_minutes > 0:
                    time_text = f"{wait_minutes} 分钟"
                else:
                    time_text = f"{wait_seconds} 秒"
                return {
                    "success": False,
                    "message": f"操作过于频繁，请等待 {time_text} 后重试",
                    "error_type": "flood_wait",
                    "wait_seconds": wait_seconds
                }
            elif isinstance(error, PhoneNumberInvalidError):
                return {
                    "success": False,
                    "message": "手机号码格式错误，请使用国际格式（如：+8613800138000）",
                    "error_type": "invalid_phone"
                }
            elif isinstance(error, PhoneNumberBannedError):
                return {
                    "success": False,
                    "message": "该手机号码已被 Telegram 封禁，无法使用",
                    "error_type": "phone_banned"
                }
            elif isinstance(error, PhoneNumberUnoccupiedError):
                return {
                    "success": False,
                    "message": "该手机号码未注册 Telegram，请先注册",
                    "error_type": "phone_unregistered"
                }
            else:
                # 未知错误，返回原始错误信息
                error_msg = str(error)
                # 尝试从错误信息中提取有用信息
                if "timeout" in error_msg.lower():
                    return {
                        "success": False,
                        "message": "连接超时，请检查网络或代理设置",
                        "error_type": "timeout"
                    }
                elif "connection" in error_msg.lower():
                    return {
                        "success": False,
                        "message": "网络连接失败，请检查网络或代理设置",
                        "error_type": "connection_error"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"登录失败: {error_msg}",
                        "error_type": "unknown"
                    }
        except Exception as e:
            # 处理错误的过程中出错，返回最基本的错误信息
            return {
                "success": False,
                "message": f"发生未知错误: {str(error)}",
                "error_type": "unknown"
            }


def get_configured_timezone():
    """获取配置的时区对象"""
    try:
        import pytz
        import os
        tz_name = os.environ.get('TZ', 'Asia/Shanghai')
        
        if tz_name == 'UTC':
            return pytz.UTC
        else:
            try:
                return pytz.timezone(tz_name)
            except pytz.UnknownTimeZoneError:
                logger.warning(f"未知时区 {tz_name}，使用 Asia/Shanghai")
                return pytz.timezone('Asia/Shanghai')
    except ImportError:
        logger.warning("pytz 不可用，使用 UTC 时区")
        return timezone.utc

def get_current_time():
    """获取当前配置时区的时间"""
    try:
        import pytz
        import os
        tz_name = os.environ.get('TZ', 'Asia/Shanghai')
        
        if tz_name == 'UTC':
            return datetime.now(pytz.UTC)
        else:
            try:
                tz = pytz.timezone(tz_name)
                return datetime.now(tz)
            except pytz.UnknownTimeZoneError:
                logger.warning(f"未知时区 {tz_name}，使用 Asia/Shanghai")
                tz = pytz.timezone('Asia/Shanghai')
                return datetime.now(tz)
    except ImportError:
        logger.warning("pytz 不可用，使用系统本地时间")
        return datetime.now()

def ensure_timezone(dt):
    """确保datetime对象有时区信息"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是配置的时区
        configured_tz = get_configured_timezone()
        return configured_tz.localize(dt)
    
    return dt

class TelegramClientManager:
    """
    Telegram客户端管理器
    
    核心修复:
    1. 每个客户端运行在独立线程中
    2. 使用装饰器事件处理避免add_event_handler
    3. 直接使用run_until_disconnected，不包装在任务中
    4. 异步任务隔离，避免阻塞事件监听
    """
    
    def __init__(self, client_id: str, client_type: str = "user"):
        self.client_id = client_id
        self.client_type = client_type  # "user" or "bot"
        self.client: Optional[TelegramClient] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        self.connected = False
        self.user_info = None
        
        # 客户端配置
        # 机器人客户端配置
        self.bot_token: Optional[str] = None
        self.admin_user_id: Optional[str] = None
        
        # 用户客户端配置
        self.api_id: Optional[str] = None
        self.api_hash: Optional[str] = None
        self.phone: Optional[str] = None
        
        # 注意：bot 客户端也可以有独立的 api_id 和 api_hash
        # 如果 bot 客户端没有配置，则使用全局配置
        
        # 消息处理
        self.keyword_filter = KeywordFilter()
        self.regex_replacer = RegexReplacer()
        self.monitored_chats = set()
        
        # 状态回调
        self.status_callbacks: List[Callable] = []
        
        # 错误信息（供 API 使用）
        self.last_error: Optional[str] = None
        
        # 登录流程状态
        self.login_session = None
        self.login_state = "idle"  # idle, waiting_code, waiting_password, completed
        self.last_code_sent_time = None  # 上次发送验证码的时间
        self.code_cooldown_seconds = 60   # 验证码发送冷却时间（秒）
        
        # 日志队列 - 用于备份失败的日志记录（在运行时初始化）
        self.failed_log_queue = None
        self.log_retry_task = None
        
        # 日志 - 使用统一的日志管理器，消息转发日志会写入 enhanced_bot.log
        self.logger = get_logger(f"client.{client_id}", "enhanced_bot.log")
    
    def add_status_callback(self, callback: Callable):
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
    
    async def _reset_login_state(self):
        """
        重置登录状态
        
        在登录失败或取消登录时调用，确保状态完全清理
        """
        self.login_state = "idle"
        self.login_session = None
        
        # 断开登录客户端连接（但不删除 client 对象，可能被其他地方使用）
        if self.client and self.client.is_connected() and not self.connected:
            # 只有在未完成登录的情况下才断开
            try:
                await self.client.disconnect()
                self.logger.info("🔌 登录客户端已断开连接")
            except Exception as e:
                self.logger.warning(f"断开登录客户端失败: {e}")
    
    def _notify_status_change(self, status: str, data: Dict[str, Any] = None):
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                callback(self.client_id, status, data or {})
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
    
    def start(self) -> bool:
        """启动客户端（在独立线程中）"""
        if self.running:
            self.logger.warning("客户端已在运行中")
            return True
        
        try:
            self.thread = threading.Thread(
                target=self._run_client_thread,
                name=f"TelegramClient-{self.client_id}",
                daemon=True
            )
            self.thread.start()
            
            # 等待启动完成
            max_wait = 30  # 30秒超时
            start_time = time.time()
            while not self.running and (time.time() - start_time) < max_wait:
                time.sleep(0.1)
            
            if self.running:
                self.logger.info(f"✅ 客户端 {self.client_id} 启动成功")
                return True
            else:
                self.logger.error(f"❌ 客户端 {self.client_id} 启动超时")
                return False
                
        except Exception as e:
            self.logger.error(f"启动客户端失败: {e}")
            return False
    
    def stop(self):
        """停止客户端"""
        if not self.running:
            return
        
        self.running = False
        
        if self.loop and self.client:
            # 在客户端的事件循环中执行断开连接
            try:
                # 创建一个异步函数来断开连接
                async def disconnect_client():
                    if self.client.is_connected():
                        await self.client.disconnect()
                
                future = asyncio.run_coroutine_threadsafe(
                    disconnect_client(), 
                    self.loop
                )
                future.result(timeout=5)  # 等待最多5秒
            except Exception as e:
                self.logger.warning(f"停止客户端时出错: {e}")
        
        if self.thread:
            self.thread.join(timeout=10)
        
        self.logger.info(f"✅ 客户端 {self.client_id} 已停止")
    
    def _run_client_thread(self):
        """在独立线程中运行客户端"""
        try:
            # 创建独立的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 运行客户端
            self.loop.run_until_complete(self._run_client())
            
        except Exception as e:
            self.logger.error(f"客户端线程运行失败: {e}")
            self._notify_status_change("error", {"error": str(e)})
        finally:
            if self.loop:
                self.loop.close()
            self.running = False
            self.connected = False
    
    async def _run_client(self):
        """运行客户端主逻辑"""
        try:
            # 初始化日志队列（在事件循环中）
            self.failed_log_queue = asyncio.Queue(maxsize=1000)
            
            # 创建客户端
            await self._create_client()
            
            if not self.client:
                raise Exception("客户端创建失败")
            
            # 启动客户端
            try:
                if self.client_type == "bot":
                    bot_token = self.bot_token or Config.BOT_TOKEN
                    await self.client.start(bot_token=bot_token)
                else:
                    # 【优化】用户客户端启动逻辑：
                    # - 如果已有 session 且已授权，可以正常启动
                    # - 如果没有 session 或未授权，阻止命令行登录，引导使用 Web 界面
                    self.logger.info(f"📞 正在连接到 Telegram 服务器...")
                    
                    # 先连接（不登录）
                    await self.client.connect()
                    
                    # 检查是否已授权
                    if not await self.client.is_user_authorized():
                        self.logger.error("❌ 用户客户端未登录，请通过 Web 界面完成登录")
                        await self.client.disconnect()
                        raise Exception("用户客户端需要通过 Web 界面登录，不能在命令行环境中启动")
                    
                    # 已授权，正常启动（不会触发命令行输入）
                    self.logger.info(f"✅ 用户客户端已授权，使用现有 session 启动")
            except Exception as start_error:
                error_msg = str(start_error)
                if "database is locked" in error_msg:
                    self.logger.warning(f"⚠️ Session 文件被锁定，尝试自动修复...")
                    
                    # 尝试自动修复：清理锁定的 session 文件
                    try:
                        import sqlite3
                        import time
                        import gc
                        session_path = Path(Config.SESSIONS_DIR) / f"{self.client_type}_{self.client_id}.session"
                        
                        if session_path.exists():
                            self.logger.info("   ├─ 📂 Session文件存在，开始清理锁定...")
                            
                            # 第1步：断开当前连接（如果有）
                            if hasattr(self, 'client') and self.client:
                                try:
                                    await self.client.disconnect()
                                    self.client = None
                                    self.logger.info("   ├─ 🔌 已断开旧连接")
                                except Exception as e:
                                    self.logger.debug(f"   ├─ 断开连接异常: {e}")
                            
                            # 等待连接完全释放
                            await asyncio.sleep(0.5)
                            gc.collect()  # 强制垃圾回收
                            
                            # 第2步：强制删除 WAL 和 SHM 文件
                            wal_file = session_path.with_suffix('.session-wal')
                            shm_file = session_path.with_suffix('.session-shm')
                            
                            for file, name in [(wal_file, 'WAL'), (shm_file, 'SHM')]:
                                if file.exists():
                                    try:
                                        file.unlink()
                                        self.logger.info(f"   ├─ 🗑️ 删除 {name} 文件")
                                    except Exception as e:
                                        self.logger.warning(f"   ├─ ⚠️ 删除{name}失败: {e}")
                            
                            # 第3步：尝试打开数据库并清除WAL模式
                            try:
                                conn = sqlite3.connect(str(session_path), timeout=10.0, check_same_thread=False)
                                conn.execute("PRAGMA journal_mode=DELETE")
                                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                                conn.commit()
                                conn.close()
                                self.logger.info("   ├─ ✅ Session 文件锁定已清除")
                            except Exception as db_error:
                                self.logger.warning(f"   ├─ ⚠️ 无法清除数据库锁: {db_error}")
                                # 如果还是锁定，尝试最后一招：复制session文件
                                try:
                                    import shutil
                                    backup_path = session_path.with_suffix('.session.backup')
                                    temp_path = session_path.with_suffix('.session.tmp')
                                    
                                    # 复制到临时文件
                                    shutil.copy2(session_path, temp_path)
                                    # 删除原文件
                                    session_path.unlink()
                                    # 重命名回来
                                    temp_path.rename(session_path)
                                    self.logger.info("   ├─ ✅ 使用复制方式清除锁定")
                                except Exception as copy_error:
                                    self.logger.error(f"   ├─ ❌ 复制方式也失败: {copy_error}")
                            
                            # 等待文件系统同步
                            await asyncio.sleep(1.0)
                            
                            # 第4步：重新创建客户端
                            self.logger.info("   ├─ 🔄 重新创建客户端...")
                            await self._create_client()
                            
                            # 第5步：重试启动
                            self.logger.info("   └─ 🔄 重试启动客户端...")
                            await self.client.start()
                            self.logger.info("   └─ ✅ 客户端启动成功（锁定已修复）")
                    except Exception as fix_error:
                        fix_error_msg = str(fix_error)
                        self.logger.error(f"❌ 自动修复失败: {fix_error}")
                        
                        # 如果还是锁定错误，说明无法自动修复
                        if "database is locked" in fix_error_msg:
                            self.logger.error("💡 Session 文件持续被锁定，建议手动解决:")
                            self.logger.error("   1. 停止所有使用此 session 的进程")
                            self.logger.error("   2. 重启 Docker 容器")
                            self.logger.error("   3. 如果问题持续，删除 session 文件并重新登录")
                            # 不抛出异常，让客户端保持"已停止"状态，用户可以手动重试
                            return
                        else:
                            raise Exception(f"Session 文件被锁定且无法自动修复: {error_msg}")
                elif "Server closed the connection" in error_msg or "0 bytes read" in error_msg:
                    self.logger.error(f"❌ Telegram 服务器连接失败: {error_msg}")
                    self.logger.error("💡 可能的解决方案:")
                    self.logger.error("   1. 检查网络连接是否正常")
                    self.logger.error("   2. 检查系统设置中的代理配置是否正确（如果需要代理）")
                    self.logger.error("   3. 尝试删除 session 文件后重新登录")
                    self.logger.error("   4. 稍后再试，可能是 Telegram 服务器暂时不可用")
                    raise Exception(f"Telegram 服务器连接失败，请检查网络和代理设置: {error_msg}")
                else:
                    raise
            
            # 获取用户信息
            self.user_info = await self.client.get_me()
            self.connected = True
            self.running = True
            
            self.logger.info(f"✅ {self.client_type} 客户端已连接: {getattr(self.user_info, 'username', '') or getattr(self.user_info, 'first_name', 'Unknown')}")
            self._notify_status_change("connected", {
                "user_info": {
                    "id": self.user_info.id,
                    "username": getattr(self.user_info, 'username', ''),
                    "first_name": getattr(self.user_info, 'first_name', ''),
                    "phone": getattr(self.user_info, 'phone', '')
                }
            })
            
            # 保存客户端配置到数据库（包含连接时间）
            await self._save_client_config()
            
            # 注册事件处理器（使用装饰器方式）
            self._register_event_handlers()
            
            # 注册消息处理器（资源监控等）
            await self._register_message_processors()
            
            # 更新监听聊天列表
            await self._update_monitored_chats()
            
            # 关键修复：直接使用run_until_disconnected，不包装在任务中
            self.logger.info(f"🎯 开始监听消息...")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"客户端运行失败: {error_msg}")
            
            # 保存错误信息供 API 使用
            self.last_error = error_msg
            
            self._notify_status_change("error", {"error": error_msg})
            raise
        finally:
            self.running = False
            self.connected = False
            self._notify_status_change("disconnected", {})
    
    async def _update_last_connected(self):
        """更新数据库中的最后连接时间"""
        try:
            from models import TelegramClient
            from database import get_db
            from sqlalchemy import select
            from datetime import datetime
            
            async for db in get_db():
                result = await db.execute(
                    select(TelegramClient).where(TelegramClient.client_id == self.client_id)
                )
                db_client = result.scalar_one_or_none()
                
                if db_client:
                    db_client.last_connected = datetime.now()
                    await db.commit()
                    self.logger.debug(f"✅ 已更新客户端 {self.client_id} 的最后连接时间")
                break
        except Exception as e:
            self.logger.warning(f"更新最后连接时间失败（不影响运行）: {e}")
    
    async def _save_client_config(self):
        """保存或更新客户端配置到数据库"""
        try:
            from models import TelegramClient
            from database import get_db
            from sqlalchemy import select
            from datetime import datetime
            
            async for db in get_db():
                result = await db.execute(
                    select(TelegramClient).where(TelegramClient.client_id == self.client_id)
                )
                db_client = result.scalar_one_or_none()
                
                if db_client:
                    # 更新现有记录
                    if self.client_type == 'user':
                        if self.api_id:
                            db_client.api_id = str(self.api_id)
                        if self.api_hash:
                            db_client.api_hash = self.api_hash
                        if self.phone:
                            db_client.phone = self.phone
                    elif self.client_type == 'bot':
                        if self.bot_token:
                            db_client.bot_token = self.bot_token
                        if self.admin_user_id:
                            db_client.admin_user_id = self.admin_user_id
                    
                    db_client.last_connected = datetime.now()
                    await db.commit()
                    self.logger.info(f"✅ 已更新客户端 {self.client_id} 的配置到数据库")
                else:
                    # 创建新记录
                    new_client = TelegramClient(
                        client_id=self.client_id,
                        client_type=self.client_type,
                        api_id=str(self.api_id) if self.api_id and self.client_type == 'user' else None,
                        api_hash=self.api_hash if self.api_hash and self.client_type == 'user' else None,
                        phone=self.phone if self.phone and self.client_type == 'user' else None,
                        bot_token=self.bot_token if self.bot_token and self.client_type == 'bot' else None,
                        admin_user_id=self.admin_user_id if self.admin_user_id and self.client_type == 'bot' else None,
                        last_connected=datetime.now(),
                        auto_start=False
                    )
                    db.add(new_client)
                    await db.commit()
                    self.logger.info(f"✅ 已保存客户端 {self.client_id} 的配置到数据库")
                break
        except Exception as e:
            self.logger.warning(f"保存客户端配置失败（不影响运行）: {e}")
    
    async def _create_client(self):
        """创建Telegram客户端"""
        try:
            # 获取代理配置
            proxy_manager = get_proxy_manager()
            proxy_config = proxy_manager.get_telethon_proxy()
            
            # 会话文件路径
            session_name = f"{Config.SESSIONS_DIR}/{self.client_type}_{self.client_id}"
            session_file = f"{session_name}.session"
            
            # 检查session文件是否存在
            import os
            session_exists = os.path.exists(session_file)
            
            # 预防性清理：删除可能存在的 WAL 和 SHM 锁定文件
            if session_exists:
                wal_file = f"{session_file}-wal"
                shm_file = f"{session_file}-shm"
                
                if os.path.exists(wal_file):
                    try:
                        os.remove(wal_file)
                        self.logger.debug(f"🗑️ 清理旧 WAL 文件")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 无法删除 WAL 文件: {e}")
                
                if os.path.exists(shm_file):
                    try:
                        os.remove(shm_file)
                        self.logger.debug(f"🗑️ 清理旧 SHM 文件")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 无法删除 SHM 文件: {e}")
            
            self.logger.info(f"🔍 客户端 {self.client_id} 配置检查:")
            self.logger.info(f"   - Session路径: {session_file}")
            self.logger.info(f"   - Session存在: {session_exists}")
            self.logger.info(f"   - 客户端API ID: {self.api_id}")
            self.logger.info(f"   - 客户端API Hash: {'***' if self.api_hash else None}")
            self.logger.info(f"   - 全局API ID: {Config.API_ID}")
            self.logger.info(f"   - 全局API Hash: {'***' if Config.API_HASH else None}")
            
            # 根据客户端类型使用不同的配置
            if self.client_type == "bot":
                # 机器人客户端使用bot_token
                bot_token = self.bot_token or Config.BOT_TOKEN
                if not bot_token:
                    raise ValueError(f"机器人客户端 {self.client_id} 缺少Bot Token")
                
                # Bot 客户端的 API 配置：优先使用客户端配置，否则使用全局配置
                api_id = int(self.api_id) if self.api_id else None
                api_hash = self.api_hash or None
                
                # 如果没有客户端特定配置，使用全局配置
                if not api_id or not api_hash:
                    if session_exists:
                        # Session文件存在，使用全局配置
                        api_id = Config.API_ID
                        api_hash = Config.API_HASH
                        self.logger.info(f"💡 Bot客户端 {self.client_id} 使用session文件和全局API配置")
                    else:
                        # 新Bot客户端，必须有全局配置
                        api_id = Config.API_ID
                        api_hash = Config.API_HASH
                        if not api_id or not api_hash:
                            raise ValueError(f"Bot客户端 {self.client_id} 缺少API ID或API Hash（客户端配置和全局配置都为空）")
                        self.logger.info(f"💡 Bot客户端 {self.client_id} 使用全局API配置")
                else:
                    self.logger.info(f"✅ Bot客户端 {self.client_id} 使用客户端专属API配置")
                
                self.client = TelegramClient(
                    session_name,
                    api_id,
                    api_hash,
                    proxy=proxy_config,
                    connection_retries=5,
                    retry_delay=2,
                    timeout=30,
                    auto_reconnect=True
                )
            else:
                # 用户客户端：优先使用客户端配置，如果session存在则可以使用全局配置
                api_id = int(self.api_id) if self.api_id else None
                api_hash = self.api_hash or None
                
                # 如果没有客户端特定配置，检查是否有session文件
                if not api_id or not api_hash:
                    if session_exists:
                        # Session文件存在，使用全局配置
                        api_id = Config.API_ID
                        api_hash = Config.API_HASH
                        self.logger.info(f"💡 客户端 {self.client_id} 使用session文件和全局API配置")
                    else:
                        raise ValueError(f"用户客户端 {self.client_id} 缺少API ID或API Hash，且没有session文件（路径：{session_file}）")
                
                if not api_id or not api_hash:
                    raise ValueError(f"用户客户端 {self.client_id} 缺少API ID或API Hash（全局配置也为空）")
                
                self.client = TelegramClient(
                    session_name,
                    api_id,
                    api_hash,
                    proxy=proxy_config,
                    connection_retries=5,
                    retry_delay=2,
                    timeout=30,
                    auto_reconnect=True
                )
            
            if session_exists:
                self.logger.info(f"📱 {self.client_type} 客户端已创建（使用现有session）")
            else:
                self.logger.info(f"📱 {self.client_type} 客户端已创建（新session）")
            
        except Exception as e:
            self.logger.error(f"创建客户端失败: {e}")
            raise
    
    def _register_event_handlers(self):
        """注册事件处理器（使用装饰器方式）"""
        if not self.client:
            return
        
        # 核心修复：使用装饰器事件处理替代add_event_handler
        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            """处理新消息事件"""
            try:
                # 异步任务隔离：在独立任务中处理，避免阻塞事件监听
                asyncio.create_task(self._process_message(event))
            except Exception as e:
                self.logger.error(f"消息处理任务创建失败: {e}")
        
        @self.client.on(events.MessageEdited())
        async def handle_message_edited(event):
            """处理消息编辑事件"""
            try:
                asyncio.create_task(self._process_message(event, is_edited=True))
            except Exception as e:
                self.logger.error(f"消息编辑处理任务创建失败: {e}")
        
        self.logger.info("✅ 事件处理器已注册（装饰器方式）")
    
    async def _register_message_processors(self):
        """注册消息处理器（资源监控等）"""
        try:
            # 获取消息分发器
            dispatcher = get_message_dispatcher()
            
            # 注册资源监控处理器（不需要传入数据库会话）
            resource_processor = ResourceMonitorProcessor()
            dispatcher.register(resource_processor)
            self.logger.info("✅ 资源监控处理器已注册")
        except Exception as e:
            self.logger.error(f"注册消息处理器失败: {e}", exc_info=True)
    
    async def _safe_send_message(self, chat_id: int, text: str, **kwargs):
        """
        安全地发送消息（跨事件循环调用）
        
        用于 MessageContext 调用，自动处理事件循环切换
        """
        if not self.client or not self.loop:
            raise Exception("客户端未连接")
        
        async def _send():
            return await self.client.send_message(chat_id, text, **kwargs)
        
        # 使用 run_coroutine_threadsafe 在客户端事件循环中执行
        future = asyncio.run_coroutine_threadsafe(_send(), self.loop)
        return future.result(timeout=30)  # 30秒超时
    
    async def _safe_download_media(self, message, file_path: str):
        """
        安全地下载媒体（跨事件循环调用）
        
        用于 MessageContext 调用，自动处理事件循环切换
        """
        if not self.client or not self.loop:
            raise Exception("客户端未连接")
        
        async def _download():
            return await self.client.download_media(message, file=file_path)
        
        # 使用 run_coroutine_threadsafe 在客户端事件循环中执行
        future = asyncio.run_coroutine_threadsafe(_download(), self.loop)
        return future.result(timeout=300)  # 5分钟超时
    
    async def _process_message(self, event, is_edited: bool = False):
        """处理消息（在独立任务中运行）- 优化版"""
        start_time = time.time()
        try:
            message = event.message
            
            # 性能优化：提前检查消息有效性
            if not message or not hasattr(message, 'peer_id'):
                return
            
            # 过滤服务消息（如置顶、加入群组等系统消息）
            from telethon.tl.types import MessageService
            if isinstance(message, MessageService):
                self.logger.debug(f"⏭️ 跳过服务消息: {message.id} (类型: {type(message.action).__name__})")
                return
                
            # 修复聊天ID转换问题 - 更准确的转换逻辑
            from telethon.tl.types import PeerChannel, PeerChat, PeerUser
            
            if isinstance(message.peer_id, PeerChannel):
                # 超级群组/频道：转换为 -100xxxxxxxxx 格式
                raw_chat_id = message.peer_id.channel_id
                chat_id = -1000000000000 - raw_chat_id
            elif isinstance(message.peer_id, PeerChat):
                # 普通群组：转换为负数
                raw_chat_id = message.peer_id.chat_id
                chat_id = -raw_chat_id
            else:
                # 私聊用户：保持正数
                raw_chat_id = message.peer_id.user_id
                chat_id = raw_chat_id
            
            # 先检查是否需要监听此聊天，只有监听的才记录INFO级别日志
            if chat_id not in self.monitored_chats:
                # 不在监听列表，使用DEBUG级别
                self.logger.debug(f"收到消息但不在监听列表: 原始ID={raw_chat_id}, 转换ID={chat_id}, 消息ID={message.id}")
                return
            
            # 在监听列表中，记录INFO级别日志
            self.logger.info(f"📨 收到监控消息: 聊天ID={chat_id}, 消息ID={message.id}")
            self.logger.debug(f"处理监听消息: 聊天ID={chat_id}, 消息ID={message.id}")
            
            # 1. 处理转发规则
            rules = await self._get_applicable_rules(chat_id)
            
            if rules:
                # 并发处理多个规则（如果有多个）
                if len(rules) > 1:
                    tasks = []
                    for rule in rules:
                        task = asyncio.create_task(self._process_rule_safe(rule, message, event))
                        tasks.append(task)
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # 单个规则直接处理
                    await self._process_rule_safe(rules[0], message, event)
            else:
                self.logger.debug(f"聊天ID {chat_id} 没有适用的转发规则")
            
            # 2. 统一处理资源监控和媒体监控（带优先级）
            await self._process_monitors_with_priority(chat_id, message, is_edited)
                
            # 性能监控
            processing_time = (time.time() - start_time) * 1000
            if processing_time > 1000:  # 超过1秒记录警告
                self.logger.warning(f"消息处理耗时: {processing_time:.2f}ms")
                    
        except Exception as e:
            self.logger.error(f"消息处理失败: {e}")
    
    async def _process_monitors_with_priority(self, chat_id: int, message, is_edited: bool = False):
        """
        统一处理资源监控和媒体监控，按优先级执行
        
        优先级逻辑：
        1. 先检查是否有资源监控规则，如果有且消息包含链接 → 只处理资源监控
        2. 如果没有链接或没有资源监控规则 → 检查媒体监控规则
        """
        try:
            from models import ResourceMonitorRule, MediaMonitorRule
            from sqlalchemy import select
            from services.message_dispatcher import get_message_dispatcher
            from services.message_context import MessageContext
            import re
            
            # 1. 先检查是否有资源监控规则监听此频道
            has_resource_monitor = False
            has_links = False
            
            async for db in get_db():
                # 检查资源监控规则
                resource_rules_result = await db.execute(
                    select(ResourceMonitorRule).where(
                        ResourceMonitorRule.is_active == True
                    )
                )
                resource_rules = resource_rules_result.scalars().all()
                
                # 检查是否有规则监听此频道
                import json
                for rule in resource_rules:
                    source_chats = json.loads(rule.source_chats) if rule.source_chats else []
                    if str(chat_id) in source_chats:
                        has_resource_monitor = True
                        
                        # 检查消息是否包含链接
                        if hasattr(message, 'text') and message.text:
                            # 检测各类资源链接
                            magnet_pattern = r'magnet:\?xt=urn:btih:[a-zA-Z0-9]+'
                            pan115_pattern = r'https?://(?:115\.com|115cdn\.com)/s/[a-zA-Z0-9]+(?:\?password=[a-zA-Z0-9]+)?'
                            ed2k_pattern = r'ed2k://\|file\|[^|]+\|[0-9]+\|[a-fA-F0-9]+\|'
                            
                            if (re.search(magnet_pattern, message.text) or 
                                re.search(pan115_pattern, message.text) or 
                                re.search(ed2k_pattern, message.text)):
                                has_links = True
                                break
                        break
                
                # 2. 根据优先级决定处理方式
                if has_resource_monitor and has_links:
                    # 优先级1: 有资源监控规则且消息包含链接 → 只处理资源监控
                    self.logger.info(f"📋 检测到资源链接，分发给资源监控处理")
                    context = MessageContext(
                        message=message,
                        client_manager=self,
                        chat_id=chat_id,
                        is_edited=is_edited
                    )
                    dispatcher = get_message_dispatcher()
                    await dispatcher.dispatch(context)
                    # 不再处理媒体监控
                    return
                
                # 优先级2: 没有链接或没有资源监控 → 检查媒体监控
                self.logger.debug(f"📋 未检测到资源链接，检查媒体监控")
                
                # 查找适用的媒体监控规则
                media_rules_result = await db.execute(
                    select(MediaMonitorRule).where(
                        MediaMonitorRule.is_active == True,
                        MediaMonitorRule.client_id == self.client_id
                    )
                )
                media_rules = media_rules_result.scalars().all()
                
                for rule in media_rules:
                    source_chats = json.loads(rule.source_chats) if rule.source_chats else []
                    
                    if str(chat_id) in source_chats:
                        # 检查消息是否包含媒体
                        has_media = (
                            hasattr(message, 'media') and message.media is not None and
                            not (hasattr(message.media, '__class__') and 
                                 message.media.__class__.__name__ == 'MessageMediaWebPage')
                        )
                        
                        if not has_media:
                            self.logger.debug(f"⏭️ 跳过媒体监控规则 {rule.name}：消息不包含媒体")
                            continue
                        
                        self.logger.info(f"📹 触发媒体监控规则: {rule.name} (ID: {rule.id})")
                        
                        # 处理媒体消息
                        from services.media_monitor_service import get_media_monitor_service
                        media_monitor = get_media_monitor_service()
                        await media_monitor.process_message(self.client, message, rule.id, client_wrapper=self)
                
                break
                
        except Exception as e:
            self.logger.error(f"监控处理失败: {e}", exc_info=True)
    
    async def _process_media_monitor(self, chat_id: int, message):
        """处理媒体监控（已弃用，保留用于兼容）"""
        try:
            # 获取媒体监控服务
            from services.media_monitor_service import get_media_monitor_service
            media_monitor = get_media_monitor_service()
            
            # 检查是否有适用的媒体监控规则
            from models import MediaMonitorRule
            from sqlalchemy import select
            
            async for db in get_db():
                # 查找适用的媒体监控规则
                result = await db.execute(
                    select(MediaMonitorRule).where(
                        MediaMonitorRule.is_active == True,
                        MediaMonitorRule.client_id == self.client_id
                    )
                )
                rules = result.scalars().all()
                
                for rule in rules:
                    # 解析 source_chats（JSON 字符串）
                    import json
                    source_chats = json.loads(rule.source_chats) if rule.source_chats else []
                    
                    # 检查消息是否来自监控的聊天
                    if str(chat_id) in source_chats:
                        # 提前检查消息是否包含媒体，避免不必要的处理
                        has_media = (
                            hasattr(message, 'media') and message.media is not None and
                            not (hasattr(message.media, '__class__') and 
                                 message.media.__class__.__name__ == 'MessageMediaWebPage')
                        )
                        
                        if not has_media:
                            self.logger.debug(f"⏭️ 跳过媒体监控规则 {rule.name}：消息不包含媒体")
                            continue
                        
                        self.logger.info(f"📹 触发媒体监控规则: {rule.name} (ID: {rule.id})")
                        # 处理媒体消息（传递客户端包装器self，以便访问事件循环）
                        await media_monitor.process_message(self.client, message, rule.id, client_wrapper=self)
                
                break
                
        except Exception as e:
            self.logger.error(f"媒体监控处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _get_applicable_rules(self, chat_id: int) -> List[ForwardRule]:
        """获取适用的转发规则"""
        try:
            async for db in get_db():
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload
                
                stmt = select(ForwardRule).options(
                    selectinload(ForwardRule.keywords),
                    selectinload(ForwardRule.replace_rules)
                ).where(
                    ForwardRule.source_chat_id == chat_id,
                    ForwardRule.is_active == True
                )
                
                result = await db.execute(stmt)
                rules = result.scalars().all()
                return list(rules)
                
        except Exception as e:
            self.logger.error(f"获取转发规则失败: {e}")
            return []
    
    async def _process_rule_safe(self, rule: ForwardRule, message, event):
        """安全的规则处理包装器"""
        try:
            await self._process_rule(rule, message, event)
        except Exception as e:
            self.logger.error(f"处理规则 {rule.id}({rule.name}) 失败: {e}")
            # 记录错误日志
            try:
                await self._log_message(rule.id, message, "failed", str(e), rule.name)
            except Exception as log_error:
                self.logger.error(f"记录错误日志失败: {log_error}")
    
    async def _process_rule(self, rule: ForwardRule, message, event):
        """处理单个转发规则"""
        try:
            # 消息类型检查
            if not self._check_message_type(rule, message):
                return
            
            # 时间过滤检查
            if not self._check_time_filter(rule, message):
                return
            
            # 【新功能】发送者过滤检查
            if getattr(rule, 'enable_sender_filter', False):
                from utils.message_deduplicator import SenderFilter
                sender_info = SenderFilter.get_sender_info(message)
                is_allowed = SenderFilter.is_sender_allowed(
                    sender_info['id'],
                    sender_info['username'],
                    getattr(rule, 'sender_filter_mode', 'whitelist'),
                    getattr(rule, 'sender_whitelist', None),
                    getattr(rule, 'sender_blacklist', None)
                )
                if not is_allowed:
                    self.logger.info(f"⏭️ 发送者 {sender_info['username'] or sender_info['id']} 被过滤器阻止")
                    return
            
            # 获取消息文本（对于媒体消息使用caption）
            message_text = message.text or message.message or ""
            
            # 【新功能】消息去重检查
            if getattr(rule, 'enable_deduplication', False):
                from utils.message_deduplicator import MessageDeduplicator
                
                # 计算消息指纹
                content_hash = MessageDeduplicator.calculate_content_hash(message_text)
                media_hash = None
                if message.media and hasattr(message.media, 'id'):
                    media_type = type(message.media).__name__
                    media_hash = MessageDeduplicator.calculate_media_hash(
                        str(message.media.id), media_type
                    )
                
                # 检查是否重复
                is_duplicate = await MessageDeduplicator.is_duplicate(
                    rule.id,
                    content_hash,
                    media_hash,
                    getattr(rule, 'dedup_time_window', 3600),
                    getattr(rule, 'dedup_check_content', True),
                    getattr(rule, 'dedup_check_media', True)
                )
                
                if is_duplicate:
                    self.logger.info(f"⏭️ 消息重复，跳过转发（规则: {rule.name}）")
                    return
            
            # 关键词过滤
            if rule.enable_keyword_filter and rule.keywords:
                if not self.keyword_filter.should_forward(message_text, rule.keywords):
                    return
            
            # 文本替换
            text_to_forward = message_text
            if rule.enable_regex_replace and rule.replace_rules:
                text_to_forward = self.regex_replacer.apply_replacements(text_to_forward, rule.replace_rules)
            
            # 长度限制
            if rule.max_message_length and len(text_to_forward) > rule.max_message_length:
                text_to_forward = text_to_forward[:rule.max_message_length] + "..."
            
            # 转发延迟
            if rule.forward_delay > 0:
                await asyncio.sleep(rule.forward_delay)
            
            # 执行转发
            await self._forward_message(rule, message, text_to_forward)
            
            # 记录日志（使用重试机制，包含新的指纹字段）
            await self._log_message_with_retry(rule.id, message, "success", None, rule.name, rule.target_chat_id)
            
        except Exception as e:
            self.logger.error(f"规则处理失败: {e}")
            await self._log_message_with_retry(rule.id, message, "failed", str(e), rule.name)
    
    def _check_message_type(self, rule: ForwardRule, message) -> bool:
        """检查消息类型是否符合规则"""
        try:
            from telethon.tl.types import (
                MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage,
                MessageMediaGeo, MessageMediaVenue, MessageMediaContact,
                MessageMediaGame, MessageMediaInvoice, MessageMediaGeoLive,
                MessageMediaPoll, MessageMediaDice, MessageMediaStory
            )
            
            # 检查是否为纯文本消息（无媒体）
            if not message.media:
                # 纯文本消息检查
                if message.text and not getattr(rule, 'enable_text', True):
                    self.logger.debug(f"📝 文本消息被规则禁用: {rule.name}")
                    return False
                return True
            
            # 有媒体的消息 - 检查具体媒体类型
            media = message.media
            
            # 图片
            if isinstance(media, MessageMediaPhoto):
                enable_photo = getattr(rule, 'enable_photo', True)
                self.logger.info(f"🖼️ 检测到图片消息 - 规则 '{rule.name}' enable_photo={enable_photo}")
                if not enable_photo:
                    self.logger.debug(f"🖼️ 图片消息被规则禁用: {rule.name}")
                    return False
                self.logger.info(f"✅ 图片消息通过类型检查")
                return True
            
            # 文档（包括视频、音频、文档等）
            if isinstance(media, MessageMediaDocument):
                document = media.document
                if hasattr(document, 'mime_type') and document.mime_type:
                    mime_type = document.mime_type.lower()
                    
                    # 视频
                    if mime_type.startswith('video/'):
                        if not getattr(rule, 'enable_video', True):
                            self.logger.debug(f"🎥 视频消息被规则禁用: {rule.name}")
                            return False
                        return True
                    
                    # 音频
                    if mime_type.startswith('audio/'):
                        if not getattr(rule, 'enable_audio', True):
                            self.logger.debug(f"🎵 音频消息被规则禁用: {rule.name}")
                            return False
                        return True
                    
                    # 文档/其他文件
                    if not getattr(rule, 'enable_document', True):
                        self.logger.debug(f"📄 文档消息被规则禁用: {rule.name}")
                        return False
                    return True
                
                # 检查是否为特殊类型（语音、贴纸、动图等）
                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        attr_type = type(attr).__name__
                        
                        # 语音消息
                        if 'Voice' in attr_type:
                            if not getattr(rule, 'enable_voice', True):
                                self.logger.debug(f"🎤 语音消息被规则禁用: {rule.name}")
                                return False
                            return True
                        
                        # 贴纸
                        if 'Sticker' in attr_type:
                            if not getattr(rule, 'enable_sticker', False):  # 默认禁用贴纸
                                self.logger.debug(f"😀 贴纸消息被规则禁用: {rule.name}")
                                return False
                            return True
                        
                        # 动图
                        if 'Animated' in attr_type or 'Video' in attr_type:
                            if not getattr(rule, 'enable_animation', True):
                                self.logger.debug(f"🎞️ 动图消息被规则禁用: {rule.name}")
                                return False
                            return True
            
            # 网页预览
            if isinstance(media, MessageMediaWebPage):
                if not getattr(rule, 'enable_webpage', True):
                    self.logger.debug(f"🌐 网页预览被规则禁用: {rule.name}")
                    return False
                return True
            
            # 其他媒体类型（地理位置、联系人、游戏等）
            # 默认允许，除非有特定的禁用设置
            self.logger.debug(f"🔍 未知媒体类型，默认允许: {type(media).__name__}")
            return True
            
        except Exception as e:
            self.logger.error(f"消息类型检查失败: {e}")
            # 出错时默认允许转发
            return True
    
    def _check_time_filter(self, rule: ForwardRule, message) -> bool:
        """检查时间过滤条件 - 统一在用户时区进行比较"""
        from timezone_utils import get_user_now, telegram_time_to_user_time, database_time_to_user_time
        
        if not hasattr(rule, 'time_filter_type'):
            return True
        
        # 核心：将Telegram消息时间转换为用户时区，后续所有比较都在用户时区进行
        message_time = telegram_time_to_user_time(message.date)
        current_time = get_user_now()
        
        if rule.time_filter_type == "after_start":
            # 启动后的消息都转发（实时消息处理）
            return True
        elif rule.time_filter_type == "today_only":
            # 仅转发当天消息
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            return message_time >= today_start
        elif rule.time_filter_type == "from_time":
            # 从指定时间开始 - 数据库时间转为用户时区
            if hasattr(rule, 'start_time') and rule.start_time:
                start_time = database_time_to_user_time(rule.start_time)
                return message_time >= start_time
            else:
                # 未设置开始时间，默认允许所有实时消息
                self.logger.warning(f"⚠️ 规则 '{rule.name}' 设置为from_time但未配置start_time，默认允许实时消息")
                return True
        elif rule.time_filter_type == "time_range":
            # 指定时间段内 - 数据库时间转为用户时区
            if hasattr(rule, 'start_time') and hasattr(rule, 'end_time'):
                if rule.start_time and rule.end_time:
                    start_time = database_time_to_user_time(rule.start_time)
                    end_time = database_time_to_user_time(rule.end_time)
                    return start_time <= message_time <= end_time
                else:
                    # 时间配置不完整，默认允许所有实时消息
                    self.logger.warning(f"⚠️ 规则 '{rule.name}' 设置为time_range但时间配置不完整，默认允许实时消息")
                    return True
            else:
                # 缺少时间属性，默认允许所有实时消息
                self.logger.warning(f"⚠️ 规则 '{rule.name}' 设置为time_range但缺少时间属性，默认允许实时消息")
                return True
        elif rule.time_filter_type == "all_messages":
            # 转发所有消息（无时间限制）
            return True
        
        return True
    
    async def _forward_message(self, rule: ForwardRule, original_message, text_to_forward: str):
        """转发消息（支持文本和媒体消息）"""
        try:
            target_chat_id = int(rule.target_chat_id)
            
            # 记录消息类型信息
            self.logger.info(f"🔍 准备转发消息 - 消息ID: {original_message.id}, 有媒体: {bool(original_message.media)}, 媒体类型: {type(original_message.media).__name__ if original_message.media else 'None'}")
            
            # 发送消息 - 根据消息是否有媒体决定如何转发
            if original_message.media:
                # 转发媒体消息（包括图片、视频、文档等）；网页预览单独按文本路径处理
                media_type_name = type(original_message.media).__name__
                self.logger.info(f"📤 转发媒体消息: 类型={media_type_name}, 文本长度={len(text_to_forward)}")
                try:
                    from telethon.tl.types import MessageMediaWebPage
                except Exception:
                    MessageMediaWebPage = type('MessageMediaWebPage', (), {})  # 占位，避免导入失败

                if isinstance(original_message.media, MessageMediaWebPage):
                    # 网页预览：按文本重发 + link preview + 复原按钮
                    text = text_to_forward or (original_message.text or original_message.message or "")
                    # 若正文没有 URL，而按钮里有 URL，则注入第一个 URL，保证生成预览
                    if (not text) and getattr(original_message, 'reply_markup', None):
                        try:
                            for row in getattr(original_message.reply_markup, 'rows', []) or []:
                                for btn in getattr(row, 'buttons', []) or []:
                                    if hasattr(btn, 'url') and btn.url:
                                        text = btn.url
                                        raise StopIteration
                        except StopIteration:
                            pass
                    await self.client.send_message(
                        target_chat_id,
                        text or "",
                        link_preview=getattr(rule, 'enable_link_preview', True),
                        buttons=getattr(original_message, 'reply_markup', None),
                        entities=getattr(original_message, 'entities', None),
                    )
                else:
                    # 其他媒体：作为文件发送，caption 放入文本，保留按钮
                    await self.client.send_file(
                        target_chat_id,
                        original_message.media,
                        caption=text_to_forward or "",
                        buttons=getattr(original_message, 'reply_markup', None),
                    )
                self.logger.info("✅ 媒体消息已转发成功")
            else:
                # 转发纯文本消息
                self.logger.info(f"📤 转发文本消息: 长度={len(text_to_forward)}")
                await self.client.send_message(
                    target_chat_id,
                    text_to_forward,
                    link_preview=getattr(rule, 'enable_link_preview', True)
                )
                self.logger.info(f"✅ 文本消息已转发成功")
            
            self.logger.info(f"✅ 消息已转发: {rule.source_chat_id} -> {target_chat_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 转发消息失败: {e}", exc_info=True)
            raise
    
    async def _log_message_with_retry(self, rule_id: int, message, status: str, error_message: str = None, rule_name: str = None, target_chat_id: str = None, max_retries: int = 3):
        """记录消息日志（带重试机制）"""
        for attempt in range(max_retries):
            try:
                await self._log_message(rule_id, message, status, error_message, rule_name, target_chat_id)
                if attempt > 0:
                    self.logger.info(f"✅ 日志记录重试成功（第{attempt + 1}次尝试）")
                return  # 成功则退出
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5  # 递增等待时间：0.5s, 1s, 1.5s
                    self.logger.warning(f"⚠️ 日志记录失败（第{attempt + 1}次尝试），{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"❌ 日志记录最终失败（已重试{max_retries}次）: {e}")
                    # 最后尝试：将失败的日志信息保存到备用队列
                    await self._save_to_log_queue(rule_id, message, status, error_message, rule_name, target_chat_id)
    
    async def _log_message(self, rule_id: int, message, status: str, error_message: str = None, rule_name: str = None, target_chat_id: str = None):
        """记录消息日志"""
        try:
            async for db in get_db():
                # 获取聊天ID
                from telethon.tl.types import PeerChannel, PeerChat, PeerUser
                
                if isinstance(message.peer_id, PeerChannel):
                    source_chat_id = str(-1000000000000 - message.peer_id.channel_id)
                elif isinstance(message.peer_id, PeerChat):
                    source_chat_id = str(-message.peer_id.chat_id)
                else:
                    source_chat_id = str(message.peer_id.user_id)
                
                # 获取规则信息（包括聊天名称）
                source_chat_name = None
                target_chat_name = None
                if not rule_name and rule_id:
                    try:
                        from sqlalchemy import select
                        rule_result = await db.execute(
                            select(ForwardRule.name, ForwardRule.source_chat_name, ForwardRule.target_chat_name, ForwardRule.target_chat_id)
                            .where(ForwardRule.id == rule_id)
                        )
                        rule_record = rule_result.first()
                        if rule_record:
                            rule_name = rule_record[0]
                            source_chat_name = rule_record[1]
                            target_chat_name = rule_record[2]
                            if not target_chat_id:
                                target_chat_id = rule_record[3]
                    except Exception as e:
                        self.logger.warning(f"获取规则信息失败: {e}")
                
                # 【新功能】计算消息指纹
                from utils.message_deduplicator import MessageDeduplicator, SenderFilter
                message_text = message.text or message.message or ""
                content_hash = MessageDeduplicator.calculate_content_hash(message_text)
                media_hash = None
                if message.media and hasattr(message.media, 'id'):
                    media_type = type(message.media).__name__
                    media_hash = MessageDeduplicator.calculate_media_hash(
                        str(message.media.id), media_type
                    )
                
                # 提取发送者信息
                sender_info = SenderFilter.get_sender_info(message)
                
                log_entry = MessageLog(
                    rule_id=rule_id,
                    rule_name=rule_name,
                    source_chat_id=source_chat_id,
                    source_chat_name=source_chat_name,
                    source_message_id=message.id,
                    target_chat_id=target_chat_id or "",
                    target_chat_name=target_chat_name,
                    original_text=message_text[:500] if message_text else "",
                    content_hash=content_hash,
                    media_hash=media_hash,
                    sender_id=sender_info['id'],
                    sender_username=sender_info['username'],
                    status=status,
                    error_message=error_message
                )
                db.add(log_entry)
                await db.commit()
                break
                
        except Exception as e:
            self.logger.error(f"记录消息日志失败: {e}")
            raise  # 重新抛出异常以便重试机制捕获
    
    async def _save_to_log_queue(self, rule_id: int, message, status: str, error_message: str = None, rule_name: str = None, target_chat_id: str = None):
        """将失败的日志保存到备用队列"""
        try:
            # 检查队列是否已初始化
            if self.failed_log_queue is None:
                self.logger.error("❌ 日志队列未初始化，无法保存")
                return
            
            log_data = {
                'rule_id': rule_id,
                'message': message,
                'status': status,
                'error_message': error_message,
                'rule_name': rule_name,
                'target_chat_id': target_chat_id,
                'timestamp': time.time()
            }
            
            if self.failed_log_queue.full():
                # 队列满时，移除最旧的记录
                try:
                    self.failed_log_queue.get_nowait()
                    self.logger.warning("⚠️ 日志队列已满，移除最旧记录")
                except:
                    pass
            
            await self.failed_log_queue.put(log_data)
            self.logger.info(f"📝 日志已保存到备用队列（队列大小: {self.failed_log_queue.qsize()}）")
            
            # 启动重试任务（如果尚未启动）
            if self.log_retry_task is None or self.log_retry_task.done():
                self.log_retry_task = asyncio.create_task(self._process_failed_log_queue())
                
        except Exception as e:
            self.logger.error(f"❌ 保存到日志队列失败: {e}")
    
    async def _process_failed_log_queue(self):
        """处理备用日志队列中的失败日志（后台任务）"""
        self.logger.info("🔄 启动日志队列处理任务")
        
        while not self.failed_log_queue.empty() or self.running:
            try:
                # 等待获取队列中的日志数据
                try:
                    log_data = await asyncio.wait_for(self.failed_log_queue.get(), timeout=30)
                except asyncio.TimeoutError:
                    # 30秒内没有新数据，继续等待
                    if not self.running:
                        break
                    continue
                
                # 检查日志是否过期（超过1小时）
                if time.time() - log_data['timestamp'] > 3600:
                    self.logger.warning(f"⚠️ 日志记录已过期（超过1小时），跳过")
                    continue
                
                # 尝试重新记录日志
                try:
                    await self._log_message(
                        log_data['rule_id'],
                        log_data['message'],
                        log_data['status'],
                        log_data['error_message'],
                        log_data['rule_name'],
                        log_data['target_chat_id']
                    )
                    self.logger.info(f"✅ 队列日志重试成功")
                except Exception as e:
                    # 重试失败，重新放回队列（但添加重试计数）
                    retry_count = log_data.get('retry_count', 0) + 1
                    if retry_count < 5:  # 最多重试5次
                        log_data['retry_count'] = retry_count
                        await asyncio.sleep(retry_count * 10)  # 递增等待时间
                        await self.failed_log_queue.put(log_data)
                        self.logger.warning(f"⚠️ 队列日志重试失败（第{retry_count}次），重新放回队列: {e}")
                    else:
                        self.logger.error(f"❌ 队列日志最终失败（已重试{retry_count}次），放弃: {e}")
                
                # 处理完成，短暂休息
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"❌ 处理日志队列时发生错误: {e}")
                await asyncio.sleep(5)
        
        self.logger.info("🛑 日志队列处理任务已停止")
    
    async def _update_monitored_chats(self):
        """更新监听的聊天列表（包含转发规则、媒体监控规则、资源监控规则）"""
        try:
            async for db in get_db():
                from sqlalchemy import select, distinct
                import json
                
                monitored_set = set()
                
                # 1. 获取所有活跃转发规则的源聊天ID
                stmt = select(distinct(ForwardRule.source_chat_id)).where(
                    ForwardRule.is_active == True
                )
                result = await db.execute(stmt)
                forward_chat_ids = result.scalars().all()
                monitored_set.update(int(chat_id) for chat_id in forward_chat_ids)
                
                # 2. 获取所有活跃媒体监控规则的源聊天ID
                from models import MediaMonitorRule
                stmt = select(MediaMonitorRule).where(
                    MediaMonitorRule.is_active == True,
                    MediaMonitorRule.client_id == self.client_id
                )
                result = await db.execute(stmt)
                media_rules = result.scalars().all()
                
                for rule in media_rules:
                    # 解析 source_chats（可能是JSON字符串或已解析的列表）
                    if rule.source_chats:
                        self.logger.info(f"🔍 规则 {rule.id} 的 source_chats 类型: {type(rule.source_chats)}, 值: {repr(rule.source_chats)}")
                        # 如果是字符串，解析为JSON
                        if isinstance(rule.source_chats, str):
                            try:
                                source_chats = json.loads(rule.source_chats)
                                self.logger.info(f"✅ JSON第一次解析: {repr(source_chats)}, 类型: {type(source_chats)}")
                                
                                # 如果解析结果仍是字符串（双重编码），再解析一次
                                if isinstance(source_chats, str):
                                    source_chats = json.loads(source_chats)
                                    self.logger.info(f"✅ JSON第二次解析: {source_chats}")
                            except json.JSONDecodeError as e:
                                self.logger.error(f"❌ JSON解析失败: {e}")
                                continue
                        else:
                            source_chats = rule.source_chats
                        # 将字符串格式的聊天ID转换为整数
                        monitored_set.update(int(chat_id) for chat_id in source_chats)

                # 3. 获取所有活跃资源监控规则的源聊天ID
                from models import ResourceMonitorRule as _RMRule
                rm_stmt = select(_RMRule).where(_RMRule.is_active == True)
                rm_result = await db.execute(rm_stmt)
                rm_rules = rm_result.scalars().all()
                for rm in rm_rules:
                    if rm.source_chats:
                        try:
                            rm_chats = json.loads(rm.source_chats) if isinstance(rm.source_chats, str) else rm.source_chats
                            if isinstance(rm_chats, str):
                                rm_chats = json.loads(rm_chats)
                        except Exception:
                            continue
                        monitored_set.update(int(chat_id) for chat_id in rm_chats)
                
                self.monitored_chats = monitored_set
                self.logger.info(f"🎯 更新监听聊天列表 (转发: {len(forward_chat_ids)}, 媒体监控: {len(media_rules)}, 资源监控: {len(rm_rules)}): {list(self.monitored_chats)}")
                break
                
        except Exception as e:
            self.logger.error(f"更新监听聊天列表失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def send_verification_code(self) -> Dict[str, Any]:
        """发送验证码"""
        try:
            if self.client_type != 'user':
                return {"success": False, "message": "只有用户客户端支持验证码登录"}
            
            if not self.phone:
                return {"success": False, "message": "手机号未设置"}
            
            # 【优化】检查验证码发送冷却时间
            if self.last_code_sent_time:
                elapsed = time.time() - self.last_code_sent_time
                remaining = self.code_cooldown_seconds - int(elapsed)
                if remaining > 0:
                    return {
                        "success": False,
                        "message": f"发送过于频繁，请等待 {remaining} 秒后重试",
                        "error_type": "rate_limit",
                        "remaining_seconds": remaining
                    }
            
            # 创建客户端
            await self._create_client()
            
            if not self.client:
                return {"success": False, "message": "客户端创建失败"}
            
            # 先连接客户端（不进行完整登录）
            await self.client.connect()
            
            if not self.client.is_connected():
                return {"success": False, "message": "客户端连接失败"}
            
            # 【优化】检查是否已经登录（Session 预加载）
            try:
                if await self.client.is_user_authorized():
                    # 已经登录，获取用户信息
                    me = await self.client.get_me()
                    self.user_info = me
                    self.login_state = "completed"
                    self.connected = True
                    
                    self.logger.info(f"✅ Session 已存在，无需重复登录: {getattr(me, 'username', '') or getattr(me, 'first_name', 'Unknown')}")
                    
                    # 保存客户端配置到数据库
                    await self._save_client_config()
                    
                    # 【新方案】保持连接并自动启动客户端运行
                    # 不断开连接，而是直接启动运行线程，这样用户点击启动时可以直接继承这个连接
                    self.logger.info("🚀 检测到已登录，保持连接并准备启动...")
                    
                    # 启动客户端运行线程（类似 start() 方法的逻辑）
                    try:
                        # 设置运行状态
                        self.running = True
                        self.status = "running"
                        
                        # 启动运行线程
                        self.thread = threading.Thread(
                            target=self._run_client_thread,
                            daemon=True,
                            name=f"telegram_client_{self.client_id}"
                        )
                        self.thread.start()
                        
                        self.logger.info(f"✅ 客户端 {self.client_id} 已自动启动（使用已验证的连接）")
                        
                        return {
                            "success": True,
                            "message": f"用户已登录，客户端已自动启动",
                            "step": "completed",
                            "auto_started": True,  # 标记为自动启动
                            "user_info": {
                                "id": me.id,
                                "username": getattr(me, 'username', ''),
                                "first_name": getattr(me, 'first_name', ''),
                                "phone": getattr(me, 'phone', '')
                            }
                        }
                    except Exception as start_error:
                        self.logger.error(f"自动启动失败: {start_error}")
                        # 启动失败，断开连接
                        if self.client and self.client.is_connected():
                            await self.client.disconnect()
                            self.connected = False
                        
                        return {
                            "success": True,
                            "message": "用户已登录，但自动启动失败，请手动启动",
                            "step": "completed",
                            "user_info": {
                                "id": me.id,
                                "username": getattr(me, 'username', ''),
                                "first_name": getattr(me, 'first_name', ''),
                                "phone": getattr(me, 'phone', '')
                            }
                        }
            except Exception as auth_check_error:
                # 检查失败不影响后续流程，继续发送验证码
                self.logger.warning(f"检查登录状态失败: {auth_check_error}")
            
            # 发送验证码
            result = await self.client.send_code_request(self.phone)
            self.login_session = result
            self.login_state = "waiting_code"
            
            # 【优化】记录发送时间，用于冷却计算
            self.last_code_sent_time = time.time()
            
            self.logger.info(f"✅ 验证码已发送到 {self.phone}")
            return {
                "success": True,
                "message": f"验证码已发送到 {self.phone}",
                "step": "waiting_code",
                "cooldown_seconds": self.code_cooldown_seconds  # 前端可用于倒计时显示
            }
            
        except Exception as e:
            self.logger.error(f"发送验证码失败: {e}")
            # 使用统一的错误处理器
            error_response = LoginErrorHandler.handle_error(e)
            return error_response
    
    async def submit_verification_code(self, code: str) -> Dict[str, Any]:
        """提交验证码"""
        try:
            if self.login_state != "waiting_code":
                return {"success": False, "message": "当前不在等待验证码状态"}
            
            if not self.login_session:
                return {"success": False, "message": "登录会话无效，请重新发送验证码"}
            
            # 【优化】自动重连机制
            if not self.client:
                return {"success": False, "message": "客户端未初始化，请重新发送验证码"}
            
            if not self.client.is_connected():
                self.logger.warning("⚠️ 客户端已断开连接，尝试自动重连...")
                try:
                    await self.client.connect()
                    if not self.client.is_connected():
                        return {
                            "success": False,
                            "message": "客户端重连失败，请重新发送验证码",
                            "should_resend": True
                        }
                    self.logger.info("✅ 客户端自动重连成功")
                except Exception as reconnect_error:
                    self.logger.error(f"❌ 客户端重连失败: {reconnect_error}")
                    return {
                        "success": False,
                        "message": "客户端连接已过期，请重新发送验证码",
                        "should_resend": True
                    }
            
            # 提交验证码
            try:
                # 导入 Telethon 专用异常
                from telethon.errors import SessionPasswordNeededError
                
                result = await self.client.sign_in(phone=self.phone, code=code)
                
                # 登录成功
                self.user_info = result
                self.login_state = "completed"
                # 注意：不设置 self.connected = True，登录流程和启动流程分离
                
                self.logger.info(f"✅ 用户客户端登录成功: {getattr(result, 'username', '') or getattr(result, 'first_name', 'Unknown')}")
                
                # 保存客户端配置到数据库
                await self._save_client_config()
                
                # 【关键修复】登录完成后断开连接，释放 session 文件锁
                # 这样用户点击启动时不会遇到 "database is locked" 错误
                try:
                    if self.client and self.client.is_connected():
                        await self.client.disconnect()
                        self.logger.info("🔌 登录完成，已断开临时连接（session 已保存）")
                except Exception as disc_error:
                    self.logger.warning(f"断开登录连接失败: {disc_error}")
                
                return {
                    "success": True,
                    "message": "登录成功，可以启动客户端了",
                    "step": "completed",
                    "auto_start_ready": True,  # 提示前端可以自动启动
                    "user_info": {
                        "id": result.id,
                        "username": getattr(result, 'username', ''),
                        "first_name": getattr(result, 'first_name', ''),
                        "phone": getattr(result, 'phone', '')
                    }
                }
                
            except SessionPasswordNeededError:
                # 【修复】使用 Telethon 专用异常，更准确
                self.login_state = "waiting_password"
                self.logger.info("🔐 检测到需要二步验证密码")
                return {
                    "success": True,
                    "message": "需要输入二步验证密码",
                    "step": "waiting_password"
                }
            except Exception as e:
                # 其他错误
                self.login_state = "idle"
                raise e
            
        except Exception as e:
            self.logger.error(f"提交验证码失败: {e}")
            # 【优化】使用统一的状态清理方法
            await self._reset_login_state()
            # 使用统一的错误处理器
            error_response = LoginErrorHandler.handle_error(e)
            return error_response
    
    async def submit_password(self, password: str) -> Dict[str, Any]:
        """提交二步验证密码"""
        try:
            if self.login_state != "waiting_password":
                return {"success": False, "message": "当前不在等待密码状态"}
            
            # 【优化】自动重连机制
            if not self.client:
                return {"success": False, "message": "客户端未初始化，请重新发送验证码"}
            
            if not self.client.is_connected():
                self.logger.warning("⚠️ 客户端已断开连接，尝试自动重连...")
                try:
                    await self.client.connect()
                    if not self.client.is_connected():
                        return {
                            "success": False,
                            "message": "客户端重连失败，请重新发送验证码",
                            "should_resend": True
                        }
                    self.logger.info("✅ 客户端自动重连成功")
                except Exception as reconnect_error:
                    self.logger.error(f"❌ 客户端重连失败: {reconnect_error}")
                    return {
                        "success": False,
                        "message": "客户端连接已过期，请重新发送验证码",
                        "should_resend": True
                    }
            
            # 提交密码
            result = await self.client.sign_in(password=password)
            
            # 登录成功
            self.user_info = result
            self.login_state = "completed"
            # 注意：不设置 self.connected = True，登录流程和启动流程分离
            
            self.logger.info(f"✅ 用户客户端二步验证成功: {getattr(result, 'username', '') or getattr(result, 'first_name', 'Unknown')}")
            
            # 保存客户端配置到数据库
            await self._save_client_config()
            
            # 【关键修复】登录完成后断开连接，释放 session 文件锁
            try:
                if self.client and self.client.is_connected():
                    await self.client.disconnect()
                    self.logger.info("🔌 登录完成，已断开临时连接（session 已保存）")
            except Exception as disc_error:
                self.logger.warning(f"断开登录连接失败: {disc_error}")
            
            return {
                "success": True,
                "message": "登录成功，可以启动客户端了",
                "step": "completed",
                "auto_start_ready": True,  # 提示前端可以自动启动
                "user_info": {
                    "id": result.id,
                    "username": getattr(result, 'username', ''),
                    "first_name": getattr(result, 'first_name', ''),
                    "phone": getattr(result, 'phone', '')
                }
            }
            
        except Exception as e:
            self.logger.error(f"二步验证失败: {e}")
            # 【优化】使用统一的状态清理方法
            await self._reset_login_state()
            # 使用统一的错误处理器
            error_response = LoginErrorHandler.handle_error(e)
            # 对于密码错误，特别处理
            if error_response.get("error_type") == "unknown":
                error_msg = str(e).lower()
                if "password" in error_msg or "invalid" in error_msg:
                    error_response["message"] = "密码错误，请检查后重新输入"
                    error_response["error_type"] = "invalid_password"
            return error_response
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        # 安全地序列化用户信息
        user_info_safe = None
        if self.user_info:
            try:
                user_info_safe = {
                    "id": getattr(self.user_info, 'id', None),
                    "username": getattr(self.user_info, 'username', None),
                    "first_name": getattr(self.user_info, 'first_name', None),
                    "last_name": getattr(self.user_info, 'last_name', None),
                    "phone": getattr(self.user_info, 'phone', None),
                    "bot": getattr(self.user_info, 'bot', None)
                }
            except Exception as e:
                self.logger.warning(f"序列化用户信息失败: {e}")
                user_info_safe = {"error": "序列化失败"}
        
        return {
            "client_id": self.client_id,
            "client_type": self.client_type,
            "running": self.running,
            "connected": self.connected,
            "login_state": getattr(self, 'login_state', 'idle'),
            "user_info": user_info_safe,
            "monitored_chats": list(self.monitored_chats),
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
    
    def get_chats_sync(self) -> List[Dict[str, Any]]:
        """同步获取聊天列表（线程安全）"""
        if not self.loop or not self.running or not self.connected:
            return []
        
        try:
            # 使用 run_coroutine_threadsafe 在客户端的事件循环中执行
            future = asyncio.run_coroutine_threadsafe(
                self._get_chats_async(),
                self.loop
            )
            # 等待结果，超时时间10秒
            return future.result(timeout=10)
        except Exception as e:
            self.logger.warning(f"获取聊天列表失败: {e}")
            return []
    
    def get_chat_title_sync(self, chat_id: str) -> str:
        """同步获取特定聊天的标题（线程安全）"""
        if not self.loop or not self.running or not self.connected:
            return f"聊天 {chat_id}"
        
        try:
            # 使用 run_coroutine_threadsafe 在客户端的事件循环中执行
            future = asyncio.run_coroutine_threadsafe(
                self._get_chat_title_async(chat_id),
                self.loop
            )
            # 等待结果，超时时间5秒
            return future.result(timeout=5)
        except Exception as e:
            self.logger.warning(f"获取聊天 {chat_id} 标题失败: {e}")
            return f"聊天 {chat_id}"
    
    async def _get_chat_title_async(self, chat_id: str) -> str:
        """在客户端事件循环中异步获取特定聊天标题"""
        try:
            if not self.client or not self.client.is_connected():
                return f"聊天 {chat_id}"
            
            # 转换聊天ID
            try:
                chat_id_int = int(chat_id)
            except ValueError:
                chat_id_int = chat_id
            
            # 获取聊天实体
            entity = await self.client.get_entity(chat_id_int)
            
            # 提取标题
            if hasattr(entity, 'title') and entity.title:
                title = entity.title
            elif hasattr(entity, 'username') and entity.username:
                title = f"@{entity.username}"
            elif hasattr(entity, 'first_name'):
                first_name = getattr(entity, 'first_name', '')
                last_name = getattr(entity, 'last_name', '')
                title = f"{first_name} {last_name}".strip()
            else:
                title = f"聊天 {chat_id}"
            
            self.logger.info(f"✅ 获取聊天 {chat_id} 标题: {title}")
            return title
            
        except Exception as e:
            self.logger.warning(f"⚠️ 无法获取聊天 {chat_id} 标题: {e}")
            return f"聊天 {chat_id}"
    
    async def _get_chats_async(self) -> List[Dict[str, Any]]:
        """在客户端事件循环中异步获取聊天列表"""
        try:
            if not self.client or not self.client.is_connected():
                return []
            
            # 不限制聊天数量，获取所有聊天
            dialogs = await self.client.get_dialogs()
            chats = []
            
            # 获取客户端用户信息用于显示
            client_display_name = "未知客户端"
            if self.user_info:
                if self.client_type == "bot":
                    client_display_name = f"机器人: {getattr(self.user_info, 'first_name', self.client_id)}"
                else:
                    first_name = getattr(self.user_info, 'first_name', '') or ''
                    last_name = getattr(self.user_info, 'last_name', '') or ''
                    username = getattr(self.user_info, 'username', '') or ''
                    
                    # 构建全名（只包含非空部分）
                    name_parts = [first_name, last_name]
                    full_name = ' '.join(part for part in name_parts if part).strip()
                    
                    if username:
                        client_display_name = f"用户: {full_name} (@{username})".strip()
                    else:
                        client_display_name = f"用户: {full_name}".strip()
                    
                    if not client_display_name.replace("用户: ", "").strip():
                        client_display_name = f"用户: {self.client_id}"
            
            for dialog in dialogs:
                try:
                    # 获取更详细的聊天信息
                    entity = dialog.entity
                    chat_type = "user"
                    if dialog.is_group:
                        chat_type = "group"
                    elif dialog.is_channel:
                        chat_type = "channel"
                    
                    # 获取聊天标题
                    title = dialog.title or dialog.name
                    if not title and hasattr(entity, 'first_name'):
                        # 对于私聊用户，组合姓名
                        first_name = getattr(entity, 'first_name', '')
                        last_name = getattr(entity, 'last_name', '')
                        title = f"{first_name} {last_name}".strip()
                    if not title:
                        title = "未知聊天"
                    
                    chat_data = {
                        "id": str(dialog.id),
                        "title": title,
                        "type": chat_type,
                        "username": getattr(entity, 'username', None),
                        "description": getattr(entity, 'about', None),
                        "members_count": getattr(entity, 'participants_count', 0) if hasattr(entity, 'participants_count') else 0,
                        "client_id": self.client_id,
                        "client_type": self.client_type,
                        "client_display_name": client_display_name,
                        "is_verified": getattr(entity, 'verified', False),
                        "is_scam": getattr(entity, 'scam', False),
                        "is_fake": getattr(entity, 'fake', False),
                        "unread_count": dialog.unread_count,
                        "last_message_date": dialog.date.isoformat() if dialog.date else None
                    }
                    chats.append(chat_data)
                except Exception as e:
                    self.logger.warning(f"处理聊天数据失败: {e}")
                    continue
            
            self.logger.info(f"✅ 客户端 {self.client_id} 获取到 {len(chats)} 个聊天")
            return chats
        except Exception as e:
            self.logger.error(f"获取聊天列表失败: {e}")
            return []
    
    async def refresh_monitored_chats(self):
        """刷新监听聊天列表（外部调用）"""
        if self.loop and self.running:
            asyncio.run_coroutine_threadsafe(
                self._update_monitored_chats(),
                self.loop
            )


class MultiClientManager:
    """
    多客户端管理器
    
    管理多个Telegram客户端实例，避免客户端竞争
    """
    
    def __init__(self):
        self.clients: Dict[str, TelegramClientManager] = {}
        self.logger = get_logger("multi_client_manager", "enhanced_bot.log")
    
    def add_client(self, client_id: str, client_type: str = "user") -> TelegramClientManager:
        """添加客户端"""
        if client_id in self.clients:
            self.logger.warning(f"客户端 {client_id} 已存在")
            return self.clients[client_id]
        
        client = TelegramClientManager(client_id, client_type)
        self.clients[client_id] = client
        
        self.logger.info(f"✅ 添加客户端: {client_id} ({client_type})")
        return client

    def add_client_with_config(self, client_id: str, client_type: str = "user", config_data: dict = None) -> TelegramClientManager:
        """添加带配置的客户端"""
        if client_id in self.clients:
            self.logger.warning(f"客户端 {client_id} 已存在")
            return self.clients[client_id]
        
        client = TelegramClientManager(client_id, client_type)
        
        # 存储客户端特定配置
        if config_data:
            if client_type == 'bot':
                client.bot_token = config_data.get('bot_token')
                client.admin_user_id = config_data.get('admin_user_id')
            elif client_type == 'user':
                client.api_id = config_data.get('api_id')
                client.api_hash = config_data.get('api_hash')
                client.phone = config_data.get('phone')
        
        self.clients[client_id] = client
        
        self.logger.info(f"✅ 添加带配置的客户端: {client_id} ({client_type})")
        return client
    
    def remove_client(self, client_id: str, force_delete_session: bool = False) -> bool:
        """
        移除客户端（包括删除 session 文件）
        
        Args:
            client_id: 客户端ID
            force_delete_session: 是否强制删除 session 文件（即使客户端不在内存中）
        
        Returns:
            bool: 是否成功从内存中移除客户端
        """
        if client_id not in self.clients:
            # 客户端不在内存中
            if force_delete_session:
                # 强制删除 session 文件（用于清理数据库中的客户端）
                self._delete_session_file(client_id)
                self.logger.info(f"💡 客户端 {client_id} 不在内存中，但已删除 session 文件")
            else:
                self.logger.debug(f"💡 客户端 {client_id} 不在内存中")
            return False
        
        client = self.clients[client_id]
        
        # 检查客户端是否正在运行
        if client.running:
            self.logger.warning(f"⚠️ 客户端 {client_id} 正在运行，先停止客户端")
            client.stop()
            # 等待客户端完全停止
            import time
            timeout = 5
            for _ in range(timeout * 10):
                if not client.running:
                    break
                time.sleep(0.1)
            
            if client.running:
                self.logger.error(f"❌ 客户端 {client_id} 停止超时，强制移除")
        
        # 删除 session 文件
        self._delete_session_file(client_id, client.client_type)
        
        del self.clients[client_id]
        
        self.logger.info(f"✅ 移除客户端: {client_id}（包括 session 文件）")
        return True
    
    def _delete_session_file(self, client_id: str, client_type: str = None) -> bool:
        """删除客户端的 session 文件"""
        try:
            import os
            from pathlib import Path
            from config import Config
            
            sessions_dir = Path(Config.SESSIONS_DIR)
            
            # 尝试删除可能的 session 文件
            if client_type:
                # 已知类型，直接删除
                session_file = sessions_dir / f"{client_type}_{client_id}.session"
                if session_file.exists():
                    session_file.unlink()
                    self.logger.info(f"🗑️ 删除 session 文件: {session_file}")
                    return True
            else:
                # 未知类型，尝试两种可能
                for ctype in ['user', 'bot']:
                    session_file = sessions_dir / f"{ctype}_{client_id}.session"
                    if session_file.exists():
                        session_file.unlink()
                        self.logger.info(f"🗑️ 删除 session 文件: {session_file}")
                        return True
            
            self.logger.debug(f"💡 未找到客户端 {client_id} 的 session 文件")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 删除 session 文件失败: {e}")
            return False
    
    def get_client(self, client_id: str) -> Optional[TelegramClientManager]:
        """获取客户端"""
        return self.clients.get(client_id)
    
    def start_client(self, client_id: str) -> bool:
        """启动客户端"""
        client = self.clients.get(client_id)
        if not client:
            return False
        
        return client.start()
    
    def stop_client(self, client_id: str) -> bool:
        """停止客户端"""
        client = self.clients.get(client_id)
        if not client:
            return False
        
        client.stop()
        return True
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有客户端状态"""
        return {
            client_id: client.get_status()
            for client_id, client in self.clients.items()
        }
    
    def stop_all(self):
        """停止所有客户端"""
        for client in self.clients.values():
            client.stop()
        self.clients.clear()
        self.logger.info("✅ 所有客户端已停止")
    
    def process_history_messages(self, rule) -> Dict[str, Any]:
        """处理历史消息 - 在客户端的事件循环中执行"""
        try:
            from services.business_services import HistoryMessageService
            import asyncio
            import threading
            
            # 获取对应的客户端
            client_wrapper = self.clients.get(rule.client_id)
            
            # 如果指定的客户端不存在，尝试使用默认客户端
            if not client_wrapper:
                self.logger.warning(f"客户端 {rule.client_id} 不存在，尝试使用可用的客户端")
                # 寻找第一个可用的客户端
                for client_id, wrapper in self.clients.items():
                    if wrapper and wrapper.connected:
                        client_wrapper = wrapper
                        self.logger.info(f"使用替代客户端: {client_id}")
                        break
            
            if not client_wrapper:
                return {
                    "success": False,
                    "message": f"没有可用的客户端处理规则 {rule.client_id}",
                    "processed": 0,
                    "forwarded": 0,
                    "errors": 0
                }
            
            # 检查客户端连接状态
            if not client_wrapper.connected:
                return {
                    "success": False,
                    "message": f"客户端 {client_wrapper.client_id} 未连接",
                    "processed": 0,
                    "forwarded": 0,
                    "errors": 0
                }
            
            # 在客户端的事件循环中异步处理历史消息
            if client_wrapper.loop and client_wrapper.running:
                try:
                    self.logger.info(f"🚀 [历史消息处理] 在客户端事件循环中处理规则 '{rule.name}' 的历史消息...")
                    
                    # 在客户端的现有事件循环中执行
                    future = asyncio.run_coroutine_threadsafe(
                        self._process_history_messages_async(rule, client_wrapper),
                        client_wrapper.loop
                    )
                    
                    self.logger.info(f"✅ 规则 '{rule.name}' 历史消息处理任务已提交到客户端事件循环")
                    
                except Exception as e:
                    self.logger.error(f"❌ 提交历史消息处理任务失败: {e}")
            else:
                self.logger.error(f"❌ 客户端 {client_wrapper.client_id} 事件循环不可用")
            
            self.logger.info(f"📤 规则 '{rule.name}' 的历史消息处理已提交到客户端事件循环")
            
            return {
                "success": True,
                "message": "历史消息处理已开始",
                "processed": 0,
                "forwarded": 0,
                "errors": 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ 历史消息处理失败: {e}")
            return {
                "success": False,
                "message": f"历史消息处理失败: {str(e)}",
                "processed": 0,
                "forwarded": 0,
                "errors": 1
            }
    
    async def _process_history_messages_async(self, rule, client_wrapper):
        """在客户端事件循环中处理历史消息 - 参考v3.1实现"""
        try:
            self.logger.info(f"🔄 开始在客户端事件循环中处理规则 '{rule.name}' 的历史消息...")
            
            # 根据规则的时间过滤类型确定时间范围
            now = get_current_time()
            
            if rule.time_filter_type == 'after_start':
                # 仅转发启动后的消息 - 不处理历史消息
                self.logger.info(f"📝 规则 '{rule.name}' 设置为仅转发启动后消息，跳过历史消息处理")
                return {
                    "success": True,
                    "message": "规则设置为仅转发启动后消息，不处理历史消息",
                    "processed": 0,
                    "forwarded": 0,
                    "errors": 0
                }
            elif rule.time_filter_type == 'today_only':
                # 仅转发当天消息
                today = now.replace(hour=0, minute=0, second=0, microsecond=0)
                start_time = today
                end_time = now
            elif rule.time_filter_type == 'from_time':
                # 从指定时间开始
                if hasattr(rule, 'start_time') and rule.start_time:
                    start_time = ensure_timezone(rule.start_time)
                    end_time = now
                    self.logger.info(f"📝 规则 '{rule.name}' 从指定时间开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.logger.warning(f"⚠️ 规则 '{rule.name}' 设置为从指定时间开始，但未设置开始时间，改为处理最近24小时")
                    start_time = now - timedelta(hours=24)
                    end_time = now
            elif rule.time_filter_type == 'time_range':
                # 指定时间段内
                if hasattr(rule, 'start_time') and hasattr(rule, 'end_time') and rule.start_time and rule.end_time:
                    start_time = ensure_timezone(rule.start_time)
                    end_time = ensure_timezone(rule.end_time)
                    # 确保end_time不超过当前时间
                    if end_time > now:
                        end_time = now
                    self.logger.info(f"📝 规则 '{rule.name}' 时间段: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.logger.warning(f"⚠️ 规则 '{rule.name}' 设置为指定时间段，但时间配置不完整，改为处理最近24小时")
                    start_time = now - timedelta(hours=24)
                    end_time = now
            elif rule.time_filter_type == 'all_messages':
                # 转发所有消息 - 不限制时间范围，获取所有可访问的历史消息
                start_time = None  # 不设置开始时间限制
                end_time = now
                self.logger.info(f"📝 规则 '{rule.name}' 设置为转发所有消息，将获取所有可访问的历史消息（无时间限制）")
            else:
                # 未知或未配置的时间过滤类型，默认处理最近24小时
                self.logger.warning(f"⚠️ 规则 '{rule.name}' 时间过滤类型未识别或未配置: {getattr(rule, 'time_filter_type', 'None')}，使用默认24小时")
                start_time = now - timedelta(hours=24)
                end_time = now
            
            # 根据时间过滤类型调整消息限制
            if rule.time_filter_type == 'all_messages':
                message_limit = None  # all_messages 模式不限制消息数量
            elif rule.time_filter_type in ['time_range', 'from_time']:
                message_limit = 100000   # 指定时间范围获取大量消息
            else:
                message_limit = 100000   # 其他情况也获取大量消息
            
            time_filter = {
                'start_time': start_time,
                'end_time': end_time,
                'limit': message_limit
            }
            
            if start_time is not None:
                self.logger.info(f"📅 时间过滤范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.logger.info(f"📅 时间过滤范围: 无开始时间限制 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 获取历史消息
            try:
                messages = await self._fetch_history_messages_simple(client_wrapper, rule.source_chat_id, time_filter)
                if not messages:
                    return {
                        "success": True,
                        "message": "没有找到符合条件的历史消息",
                        "processed": 0,
                        "forwarded": 0,
                        "errors": 0
                    }
                
                self.logger.info(f"📨 获取到 {len(messages)} 条历史消息")
                
                # 应用完整的转发规则处理和转发消息
                processed = 0
                forwarded = 0
                errors = 0
                
                for message in messages:
                    try:
                        processed += 1
                        
                        # 应用转发规则（关键词过滤、正则替换等）
                        should_forward = await self._should_forward_message(message, rule, client_wrapper)
                        
                        if should_forward:
                            # 处理消息（应用正则替换等）
                            processed_message = await self._process_message_content(message, rule)
                            
                            # 转发消息
                            success = await self._forward_message_to_target(processed_message, rule, client_wrapper)
                            if success:
                                forwarded += 1
                                self.logger.debug(f"✅ 转发历史消息: {message.id}")
                            else:
                                self.logger.warning(f"⚠️ 转发历史消息失败: {message.id}")
                        else:
                            self.logger.debug(f"⏭️ 跳过历史消息: {message.id}")
                        
                    except Exception as e:
                        errors += 1
                        self.logger.error(f"❌ 处理消息失败: {e}")
                
                # 输出详细的处理统计
                skipped = processed - forwarded - errors
                self.logger.info(f"📊 历史消息处理统计:")
                self.logger.info(f"   📥 总获取: {len(messages)} 条")
                self.logger.info(f"   ✅ 成功转发: {forwarded} 条")
                self.logger.info(f"   ⏭️ 跳过转发: {skipped} 条")
                self.logger.info(f"   ❌ 处理错误: {errors} 条")
                
                return {
                    "success": True,
                    "message": f"✅ 处理完成 - 获取:{len(messages)}, 转发:{forwarded}, 跳过:{skipped}, 错误:{errors}",
                    "total_fetched": len(messages),
                    "processed": processed,
                    "forwarded": forwarded,
                    "skipped": skipped,
                    "errors": errors
                }
                
            except Exception as e:
                self.logger.error(f"❌ 获取或处理历史消息失败: {e}")
                return {
                    "success": False,
                    "message": f"获取历史消息失败: {str(e)}",
                    "processed": 0,
                    "forwarded": 0,
                    "errors": 1
                }
                
        except Exception as e:
            self.logger.error(f"❌ 历史消息处理失败: {e}")
            return {
                "success": False,
                "message": f"处理失败: {str(e)}",
                "processed": 0,
                "forwarded": 0,
                "errors": 1
            }
    
    async def _fetch_history_messages_simple(self, client_wrapper, source_chat_id: str, time_filter: dict):
        """简单获取历史消息 - 避免复杂的事件循环问题"""
        try:
            if not client_wrapper.client or not client_wrapper.client.is_connected():
                raise Exception("客户端未连接")
            
            # 转换聊天ID
            try:
                chat_id = int(source_chat_id)
            except ValueError:
                chat_id = source_chat_id
            
            self.logger.info(f"🔍 获取聊天 {chat_id} 的历史消息...")
            
            # 获取聊天实体
            chat_entity = await client_wrapper.client.get_entity(chat_id)
            
            # 获取消息
            messages = []
            count = 0
            max_messages = time_filter.get('limit', 50)
            
            if max_messages is None:
                self.logger.info(f"📊 消息获取限制: 无限制（获取所有可访问消息）")
                # 为了避免内存问题，设置一个合理的上限
                max_messages = 10000
            else:
                self.logger.info(f"📊 消息获取限制: {max_messages} 条")
            
            async for message in client_wrapper.client.iter_messages(
                entity=chat_entity,
                limit=max_messages,
                offset_date=time_filter.get('end_time')
            ):
                # 应用时间过滤 - 将Telegram消息时间转换为用户时区
                from timezone_utils import telegram_time_to_user_time
                message_time = telegram_time_to_user_time(message.date)
                
                if 'start_time' in time_filter and 'end_time' in time_filter and time_filter['start_time'] is not None:
                    # 如果消息时间早于开始时间，说明已经超出范围，直接停止
                    if message_time < time_filter['start_time']:
                        self.logger.info(f"⏹️ 消息时间 {message_time.strftime('%Y-%m-%d %H:%M:%S')} 早于开始时间 {time_filter['start_time'].strftime('%Y-%m-%d %H:%M:%S')}，停止获取")
                        break
                    
                    # 检查是否在时间范围内
                    if not (time_filter['start_time'] <= message_time <= time_filter['end_time']):
                        continue
                        
                elif 'end_time' in time_filter and time_filter['start_time'] is None:
                    # 只有结束时间限制，没有开始时间限制（all_messages模式）
                    if message_time > time_filter['end_time']:
                        continue
                
                messages.append(message)
                count += 1
                
                if count >= max_messages:
                    break
            
            self.logger.info(f"✅ 成功获取 {len(messages)} 条历史消息")
            return messages
            
        except Exception as e:
            self.logger.error(f"❌ 获取历史消息失败: {e}")
            raise
    
    async def _should_forward_message(self, message, rule, client_wrapper):
        """检查消息是否应该被转发（应用所有过滤规则）"""
        try:
            self.logger.info(f"🔍 [转发检查] 开始检查消息 {message.id} (规则: {rule.name})")
            
            # 检查消息是否已经被转发过
            if await self._is_message_already_forwarded(message, rule):
                self.logger.info(f"⏭️ [转发检查] 消息 {message.id} 已经被转发过，跳过")
                return False
            
            # 检查消息类型过滤
            if not self._check_message_type_filter(message, rule):
                self.logger.info(f"⏭️ [转发检查] 消息 {message.id} 不符合消息类型过滤条件，跳过")
                return False
            
            # 检查关键词过滤
            if rule.enable_keyword_filter and hasattr(rule, 'keywords') and rule.keywords:
                if not self._check_keyword_filter(message, rule):
                    self.logger.info(f"⏭️ [转发检查] 消息 {message.id} 不符合关键词过滤条件，跳过")
                    return False
            
            # 检查时间过滤
            if not self._check_time_filter(message, rule):
                self.logger.info(f"⏭️ [转发检查] 消息 {message.id} 不符合时间过滤条件，跳过")
                return False
            
            self.logger.info(f"✅ [转发检查] 消息 {message.id} 通过所有过滤条件，准备转发")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 检查转发条件失败: {e}")
            return False
    
    def _check_message_type_filter(self, message, rule):
        """检查消息类型过滤 - 使用已有的_check_message_type方法"""
        try:
            # 直接使用TelegramClientManager的_check_message_type方法
            # 这个方法已经正确处理了Telethon的媒体类型检查
            # 我们需要找到对应的客户端包装器来调用
            for client_wrapper in self.clients.values():
                # 使用任一客户端的检查方法即可（规则检查逻辑是通用的）
                return client_wrapper._check_message_type(rule, message)
            
            # 如果没有客户端，返回True（允许转发）
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 消息类型过滤检查失败: {e}")
            return True  # 出错时默认通过
    
    def _check_keyword_filter(self, message, rule):
        """检查关键词过滤"""
        try:
            if not message.text:
                return True  # 非文本消息跳过关键词检查
            
            # 这里可以添加关键词过滤逻辑
            # 暂时返回True，表示通过过滤
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 关键词过滤检查失败: {e}")
            return True
    
    def _check_time_filter(self, message, rule):
        """检查时间过滤 - 统一在用户时区进行比较"""
        try:
            from timezone_utils import get_user_now, telegram_time_to_user_time, database_time_to_user_time
            
            # 如果规则没有时间过滤设置，则通过
            if not hasattr(rule, 'time_filter_type'):
                return True
            
            # 核心：将Telegram消息时间转换为用户时区，后续所有比较都在用户时区进行
            message_time = telegram_time_to_user_time(message.date)
            current_time = get_user_now()
            
            if rule.time_filter_type == "after_start":
                # 启动后的消息 - 历史消息处理中通常不会命中这个分支
                # 因为在历史消息处理开始时就会被过滤掉
                return True
            elif rule.time_filter_type == "today_only":
                # 仅转发当天消息 - 用户时区的今天开始时间
                today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                result = message_time >= today_start
                self.logger.debug(f"🕐 时间过滤检查: 消息时间={message_time}, 今天开始={today_start}, 结果={result}")
                return result
            elif rule.time_filter_type == "from_time":
                # 从指定时间开始 - 数据库时间转为用户时区
                if hasattr(rule, 'start_time') and rule.start_time:
                    start_time = database_time_to_user_time(rule.start_time)
                    result = message_time >= start_time
                    self.logger.debug(f"🕐 from_time过滤: 消息时间={message_time}, 开始时间={start_time}, 结果={result}")
                    return result
            elif rule.time_filter_type == "time_range":
                # 指定时间段内 - 数据库时间转为用户时区
                if hasattr(rule, 'start_time') and hasattr(rule, 'end_time'):
                    if rule.start_time and rule.end_time:
                        start_time = database_time_to_user_time(rule.start_time)
                        end_time = database_time_to_user_time(rule.end_time)
                        result = start_time <= message_time <= end_time
                        self.logger.debug(f"🕐 time_range过滤: 消息时间={message_time}, 时间段={start_time}~{end_time}, 结果={result}")
                        return result
            elif rule.time_filter_type == "all_messages":
                # 转发所有消息（无时间限制）
                return True
            
            # 默认通过
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 时间过滤检查失败: {e}")
            return True
    
    async def _process_message_content(self, message, rule):
        """处理消息内容（应用正则替换等）"""
        try:
            # 这里可以添加正则替换等处理逻辑
            # 暂时直接返回原消息
            return message
            
        except Exception as e:
            self.logger.error(f"❌ 消息内容处理失败: {e}")
            return message
    
    async def _is_message_already_forwarded(self, message, rule):
        """检查消息是否已经被转发过"""
        try:
            from database import get_db
            from models import MessageLog
            from sqlalchemy import select, and_, or_
            
            async for db in get_db():
                # 查询消息日志表，检查是否已存在相同的源消息ID和规则名称的记录
                # 优先使用规则名称进行查询，这样更稳定，不受规则ID变化影响
                stmt = select(MessageLog).where(
                    and_(
                        MessageLog.source_message_id == str(message.id),
                        MessageLog.source_chat_id == str(rule.source_chat_id),
                        MessageLog.rule_name == rule.name,  # 主要使用规则名称
                        MessageLog.status == 'success'  # 只检查成功转发的消息
                    )
                )
                result = await db.execute(stmt)
                existing_log = result.scalar_one_or_none()
                
                # 如果基于规则名称没找到，再尝试基于rule_id查询（兼容旧数据）
                if not existing_log:
                    stmt_fallback = select(MessageLog).where(
                        and_(
                            MessageLog.source_message_id == str(message.id),
                            MessageLog.source_chat_id == str(rule.source_chat_id),
                            MessageLog.rule_id == rule.id,  # 兼容旧数据
                            MessageLog.rule_name.is_(None),  # 只查询没有rule_name的旧记录
                            MessageLog.status == 'success'
                        )
                    )
                    result_fallback = await db.execute(stmt_fallback)
                    existing_log = result_fallback.scalar_one_or_none()
                
                # 添加详细的调试日志
                is_already_forwarded = existing_log is not None
                self.logger.info(f"🔍 消息转发状态检查: 消息ID={message.id}, 规则名称='{rule.name}', 源聊天={rule.source_chat_id}")
                self.logger.info(f"🔍 主查询条件: source_message_id='{message.id}', source_chat_id='{rule.source_chat_id}', rule_name='{rule.name}', status='success'")
                self.logger.info(f"🔍 查询结果: {'已转发' if is_already_forwarded else '未转发'} (日志ID: {existing_log.id if existing_log else 'None'})")
                
                if is_already_forwarded:
                    self.logger.info(f"🔍 找到的日志记录: ID={existing_log.id}, 创建时间={existing_log.created_at}, 状态={existing_log.status}")
                
                return is_already_forwarded
                
        except Exception as e:
            self.logger.error(f"❌ 检查消息转发状态失败: {e}")
            return False  # 出错时默认允许转发

    async def _forward_message_to_target(self, message, rule, client_wrapper):
        """转发消息到目标聊天（支持文本和媒体消息）"""
        try:
            # 获取消息文本（对于媒体消息，可能是caption）
            message_text = message.text or message.message or ""
            
            # 使用客户端包装器的转发方法（已支持媒体消息）
            await client_wrapper._forward_message(rule, message, message_text)
            
            # 使用客户端包装器的日志记录方法
            await client_wrapper._log_message(rule.id, message, 'success', None, rule.name, rule.target_chat_id)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 转发消息失败: {e}")
            # 记录失败日志
            try:
                await client_wrapper._log_message(rule.id, message, 'failed', str(e), rule.name)
            except Exception as log_error:
                self.logger.error(f"❌ 记录转发日志失败: {log_error}")
            return False
    


    def update_chat_names_sync(self, rules):
        """同步方式更新聊天名称 - 简化版本"""
        self.logger.info("🔄 开始获取聊天名称（同步方式）...")
        
        if not self.clients:
            self.logger.warning("⚠️ 没有可用的客户端")
            return []
        
        # 获取第一个可用的客户端
        client_manager = next(iter(self.clients.values()))
        if not client_manager or not client_manager.client:
            self.logger.warning("⚠️ 客户端不可用")
            return []
            
        if not client_manager.connected:
            self.logger.warning("⚠️ 客户端未连接")
            return []
        
        updated_rules = []
        
        for rule in rules:
            updated_fields = {}
            
            # 由于聊天名称获取需要在正确的事件循环中执行，
            # 我们在这里只返回占位符信息，真正的获取将在其他地方进行
            if rule.source_chat_id and (not rule.source_chat_name or rule.source_chat_name.startswith('聊天 ')):
                updated_fields['source_chat_name'] = f"聊天 {rule.source_chat_id}"
            
            if rule.target_chat_id and (not rule.target_chat_name or rule.target_chat_name.startswith('聊天 ')):
                updated_fields['target_chat_name'] = f"聊天 {rule.target_chat_id}"
            
            if updated_fields:
                updated_rules.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "updates": updated_fields
                })
                self.logger.info(f"🔄 准备更新规则 {rule.name}: {updated_fields}")
        
        self.logger.info(f"✅ 获取聊天名称完成: 准备更新 {len(updated_rules)} 个规则")
        return updated_rules

# 全局多客户端管理器实例
multi_client_manager = MultiClientManager()
