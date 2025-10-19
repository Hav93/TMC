"""
数据库迁移管理器（Alembic 封装）

在应用启动阶段被 main.py 调用，用于在需要时自动执行
`alembic upgrade head` 并在 SQLite 下进行安全备份。
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from log_manager import get_logger
from config import Config

logger = get_logger(__name__)


def _find_alembic_root(start: Optional[Path] = None) -> Optional[Path]:
    """从给定目录向上查找包含 alembic.ini 的根目录。

    默认从当前文件的上两级目录开始搜索（容器内一般为 /app）。
    """
    start_dir = start or Path(__file__).resolve().parent.parent
    for parent in [start_dir] + list(start_dir.parents):
        if (parent / "alembic.ini").exists() and (parent / "alembic").exists():
            return parent
    return None


def _backup_sqlite_db(db_url: str) -> None:
    if not db_url.startswith("sqlite:///"):
        return
    db_file = db_url.replace("sqlite:///", "")
    db_path = Path(db_file)
    if not db_path.exists():
        return
    backup_dir = db_path.parent
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_backup_{ts}{db_path.suffix}"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ 已备份 SQLite 数据库: {backup_path}")
    except Exception as e:
        logger.warning(f"⚠️ 备份 SQLite 数据库失败: {e}")


def check_and_migrate(auto_migrate: bool = True, backup_first: bool = True) -> bool:
    """检查并执行 Alembic 迁移。

    返回 True 表示执行成功（或无需迁移），False 表示执行失败但允许继续启动。
    """
    try:
        alembic_root = _find_alembic_root()
        if not alembic_root:
            logger.warning("⚠️ 未找到 alembic.ini，跳过数据库迁移")
            return True

        # SQLite 先做备份
        if backup_first:
            _backup_sqlite_db(Config.DATABASE_URL)

        env = os.environ.copy()
        # 传递数据库 URL 给 Alembic（workflow/容器里依赖该变量）
        env["DATABASE_URL"] = Config.DATABASE_URL

        logger.info("📦 执行 Alembic 迁移: upgrade head")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(alembic_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            logger.info("✅ Alembic 迁移完成")
            return True
        else:
            logger.error(f"❌ Alembic 迁移失败: \n{result.stdout}")
            return False
    except FileNotFoundError:
        # 容器/环境未安装 alembic 命令
        logger.warning("⚠️ 未安装 alembic 命令，跳过迁移")
        return True
    except Exception as e:
        logger.error(f"❌ 执行数据库迁移异常: {e}")
        return False


