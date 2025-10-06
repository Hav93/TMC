"""
FastAPI依赖注入
提供公共的依赖项，如数据库会话、bot实例等
"""
from typing import Generator, Optional
from sqlalchemy.orm import Session
from database import SessionLocal
from enhanced_bot import EnhancedTelegramBot

# 全局bot实例引用（由main.py设置）
_bot_instance: Optional[EnhancedTelegramBot] = None


def set_bot_instance(bot: EnhancedTelegramBot):
    """设置全局bot实例"""
    global _bot_instance
    _bot_instance = bot


def get_enhanced_bot() -> Optional[EnhancedTelegramBot]:
    """获取EnhancedBot实例"""
    # 尝试从main模块获取
    try:
        from main import get_enhanced_bot as get_bot_from_main
        return get_bot_from_main()
    except ImportError:
        return _bot_instance


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    使用依赖注入，确保每个请求都有独立的数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user():
    """
    获取当前用户（未来可以实现认证）
    目前返回None，表示未实现认证
    """
    # TODO: 实现用户认证
    return None

