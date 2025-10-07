#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本号管理模块

统一从根目录的 VERSION 文件读取版本号
"""

import os
from pathlib import Path

def get_version() -> str:
    """
    从 VERSION 文件读取版本号
    
    Returns:
        str: 版本号，如果读取失败则返回默认值
    """
    # 尝试从多个可能的路径读取 VERSION 文件
    possible_paths = [
        Path(__file__).parent.parent.parent / 'VERSION',  # 项目根目录
        Path(__file__).parent.parent / 'VERSION',          # app 目录
        Path('/app/VERSION'),                               # Docker 容器内
        Path('VERSION'),                                    # 当前目录
    ]
    
    for version_file in possible_paths:
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return version
            except Exception as e:
                print(f"Warning: Failed to read VERSION file at {version_file}: {e}")
                continue
    
    # 如果所有路径都失败，返回默认版本
    return '1.1.0'

# 导出版本号
__version__ = get_version()
VERSION = __version__

# 兼容导出
def get_app_version() -> str:
    """获取应用版本号（兼容旧代码）"""
    return __version__

if __name__ == '__main__':
    print(f"TMC Version: {VERSION}")

