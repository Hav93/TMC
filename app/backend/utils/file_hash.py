"""
文件哈希计算工具
基于 fake115uploader 的哈希实现
"""
import hashlib
from pathlib import Path
from typing import Tuple


def calculate_sha1(file_path: str) -> Tuple[str, str]:
    """
    计算文件的SHA1哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        (block_hash, total_hash) - 前128KB的SHA1和整个文件的SHA1
    """
    with open(file_path, 'rb') as f:
        # 1. 计算前128KB的SHA1 (block_hash)
        block_size = 128 * 1024  # 128KB
        block_data = f.read(block_size)
        block_hash = hashlib.sha1(block_data).hexdigest().upper()
        
        # 2. 计算整个文件的SHA1 (total_hash)
        f.seek(0)
        sha1_hasher = hashlib.sha1()
        
        # 分块读取以处理大文件
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha1_hasher.update(chunk)
        
        total_hash = sha1_hasher.hexdigest().upper()
        
    return block_hash, total_hash


def calculate_range_sha1(file_path: str, start: int, end: int) -> str:
    """
    计算文件指定范围的SHA1哈希值（用于二次验证）
    
    Args:
        file_path: 文件路径
        start: 起始字节位置
        end: 结束字节位置（包含）
        
    Returns:
        指定范围的SHA1值（大写）
    """
    with open(file_path, 'rb') as f:
        f.seek(start)
        data = f.read(end - start + 1)
        return hashlib.sha1(data).hexdigest().upper()


def calculate_file_md5(file_path: str) -> str:
    """
    计算文件的MD5哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件的MD5值（小写）
    """
    md5_hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            md5_hasher.update(chunk)
    return md5_hasher.hexdigest()


def calculate_content_md5(data: bytes) -> str:
    """
    计算内容的MD5并返回Base64编码（用于OSS上传）
    
    Args:
        data: 文件内容
        
    Returns:
        Base64编码的MD5值
    """
    import base64
    md5_hash = hashlib.md5(data).digest()
    return base64.b64encode(md5_hash).decode('utf-8')

