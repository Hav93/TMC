#!/usr/bin/env python3
"""
数据库重置工具

⚠️ 警告：此脚本会删除所有数据！
使用前请确保已备份重要数据。

使用场景：
1. 开发测试环境快速重置
2. 数据库损坏无法修复
3. 迁移失败需要从头开始

使用方法：
    python scripts/maintenance/reset_database.py --confirm

选项：
    --confirm: 确认删除数据（必需）
    --backup: 删除前先备份
    --keep-config: 保留配置数据（用户、设置等）
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
import shutil

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database(db_path: Path) -> Path:
    """备份数据库"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_before_reset_{timestamp}.db"
    
    if not db_path.exists():
        logger.warning(f"数据库文件不存在: {db_path}")
        return None
    
    try:
        shutil.copy2(db_path, backup_path)
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ 数据库已备份到: {backup_path}")
        logger.info(f"   大小: {size_mb:.2f} MB")
        return backup_path
    except Exception as e:
        logger.error(f"❌ 备份失败: {e}")
        return None


def reset_database(db_path: Path, keep_config: bool = False):
    """
    重置数据库
    
    Args:
        db_path: 数据库路径
        keep_config: 是否保留配置数据
    """
    try:
        if not db_path.exists():
            logger.info("数据库文件不存在，无需重置")
            return True
        
        if keep_config:
            logger.info("🔄 重置数据库（保留配置）...")
            # 导入数据库模型
            import sqlite3
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 保留的表：用户、配置、Bot设置
            keep_tables = ['users', 'media_settings', 'bot_settings', 'telegram_clients']
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]
            
            # 删除不需要保留的表
            for table in all_tables:
                if table not in keep_tables and not table.startswith('alembic'):
                    logger.info(f"   清空表: {table}")
                    cursor.execute(f"DELETE FROM {table}")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 数据库已重置（配置已保留）")
            
        else:
            logger.info("🔄 完全重置数据库...")
            db_path.unlink()
            logger.info("✅ 数据库文件已删除")
            
            # 同时删除alembic版本表（如果存在）
            alembic_versions = db_path.parent / "alembic_version"
            if alembic_versions.exists():
                alembic_versions.unlink()
                logger.info("✅ Alembic版本记录已清除")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 重置失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库重置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完全重置（删除所有数据）
  python scripts/maintenance/reset_database.py --confirm --backup
  
  # 重置但保留配置
  python scripts/maintenance/reset_database.py --confirm --keep-config
  
  # Docker环境
  docker exec tmc-local python scripts/maintenance/reset_database.py --confirm
        """
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='确认删除数据（必需）'
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        help='删除前先备份'
    )
    
    parser.add_argument(
        '--keep-config',
        action='store_true',
        help='保留配置数据（用户、设置等）'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default='/app/data/bot.db',
        help='数据库文件路径（默认: /app/data/bot.db）'
    )
    
    args = parser.parse_args()
    
    # 检查确认标志
    if not args.confirm:
        logger.error("❌ 必须使用 --confirm 参数确认删除")
        logger.info("   这是为了防止误删除数据")
        sys.exit(1)
    
    db_path = Path(args.db_path)
    
    # 显示警告
    logger.warning("⚠️" * 20)
    logger.warning("⚠️  数据库重置警告  ⚠️")
    logger.warning("⚠️" * 20)
    logger.warning("")
    logger.warning(f"   数据库路径: {db_path}")
    
    if args.keep_config:
        logger.warning("   操作: 清空数据表（保留配置）")
    else:
        logger.warning("   操作: 完全删除数据库文件")
    
    logger.warning("")
    logger.warning("   此操作将导致数据丢失！")
    logger.warning("")
    
    # 再次确认（生产环境）
    try:
        response = input("请输入 'YES' 确认继续: ")
        if response != "YES":
            logger.info("操作已取消")
            sys.exit(0)
    except (EOFError, KeyboardInterrupt):
        # Docker环境或脚本模式，跳过交互确认
        logger.info("非交互模式，直接执行")
    
    # 备份
    if args.backup:
        logger.info("📦 备份数据库...")
        backup_path = backup_database(db_path)
        if not backup_path:
            logger.warning("⚠️ 备份失败，但将继续重置")
    
    # 执行重置
    success = reset_database(db_path, keep_config=args.keep_config)
    
    if success:
        logger.info("✅ 数据库重置完成")
        logger.info("")
        logger.info("📝 后续步骤:")
        logger.info("   1. 重启应用: docker restart tmc-local")
        logger.info("   2. 应用将自动创建新数据库并运行迁移")
        logger.info("   3. 重新配置必要的设置")
        sys.exit(0)
    else:
        logger.error("❌ 数据库重置失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

