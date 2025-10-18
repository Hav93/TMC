"""
fake115uploader 命令行包装器

使用 fake115uploader 二进制实现 115 网盘上传功能
"""
import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from log_manager import get_logger

logger = get_logger(__name__)


class Fake115UploaderWrapper:
    """
    fake115uploader 包装器
    
    提供Python接口调用fake115uploader二进制
    """
    
    def __init__(self, cookie: str, config_dir: Optional[str] = None):
        """
        初始化
        
        Args:
            cookie: 115 Cookie
            config_dir: 配置文件目录（默认使用临时目录）
        """
        self.cookie = cookie
        self.config_dir = config_dir or tempfile.mkdtemp(prefix='fake115_')
        self.config_file = os.path.join(self.config_dir, 'fake115uploader.json')
        self.binary_path = self._find_binary()
        
        # 创建配置文件
        self._create_config()
    
    def _find_binary(self) -> Optional[str]:
        """查找fake115uploader二进制文件"""
        # 优先查找PATH中的
        binary = shutil.which('fake115uploader')
        if binary:
            logger.info(f"✅ 找到fake115uploader: {binary}")
            return binary
        
        # 查找常见位置
        possible_paths = [
            '/usr/local/bin/fake115uploader',
            '/usr/bin/fake115uploader',
            os.path.expanduser('~/go/bin/fake115uploader'),
            './fake115uploader',
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"✅ 找到fake115uploader: {path}")
                return path
        
        logger.warning("⚠️ 未找到fake115uploader二进制文件")
        logger.warning("请运行: go install github.com/orzogc/fake115uploader@latest")
        return None
    
    def _create_config(self):
        """创建配置文件"""
        config = {
            "cookies": self.cookie,
            "cid": "0",  # 默认根目录
            "partsNum": 0,  # 自动分片
            "resultDir": "",
            "httpRetry": 3,
            "httpProxy": "",
            "ossProxy": ""
        }
        
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 创建配置文件: {self.config_file}")
    
    async def upload_file(
        self,
        file_path: str,
        target_cid: str = "0",
        mode: str = "multipart",
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_path: 本地文件路径
            target_cid: 目标目录CID
            mode: 上传模式
                - "fast": 仅秒传
                - "upload": 秒传+普通上传（<5GB）
                - "multipart": 秒传+断点续传（推荐，支持大文件）
            progress_callback: 进度回调函数
        
        Returns:
            {
                'success': bool,
                'message': str,
                'file_id': str (optional),
                'quick_upload': bool
            }
        """
        if not self.binary_path:
            return {
                'success': False,
                'message': 'fake115uploader二进制未安装'
            }
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f'文件不存在: {file_path}'
            }
        
        # 构建命令
        mode_flag = {
            'fast': '-f',
            'upload': '-u',
            'multipart': '-m'
        }.get(mode, '-m')
        
        cmd = [
            self.binary_path,
            '-l', self.config_file,
            '-c', target_cid,
            mode_flag,
            file_path
        ]
        
        logger.info(f"📤 执行上传命令: {' '.join(cmd)}")
        
        try:
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_text = stdout.decode('utf-8', errors='ignore')
            stderr_text = stderr.decode('utf-8', errors='ignore')
            
            logger.info(f"📥 上传输出:\n{stdout_text}")
            
            if stderr_text:
                logger.warning(f"⚠️ 错误输出:\n{stderr_text}")
            
            # 解析输出
            if process.returncode == 0:
                # 上传成功
                is_quick = '秒传成功' in stdout_text or 'quick' in stdout_text.lower()
                
                return {
                    'success': True,
                    'message': '文件上传成功',
                    'quick_upload': is_quick,
                    'output': stdout_text
                }
            else:
                # 上传失败
                return {
                    'success': False,
                    'message': f'上传失败 (exit code: {process.returncode})',
                    'error': stderr_text or stdout_text
                }
        
        except Exception as e:
            logger.error(f"❌ 上传异常: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def cleanup(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.config_dir):
                import shutil
                shutil.rmtree(self.config_dir)
                logger.info(f"🗑️ 清理配置目录: {self.config_dir}")
        except Exception as e:
            logger.warning(f"⚠️ 清理失败: {e}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()


async def upload_with_fake115uploader(
    cookie: str,
    file_path: str,
    target_cid: str = "0",
    mode: str = "multipart"
) -> Dict[str, Any]:
    """
    便捷函数：使用fake115uploader上传文件
    
    Args:
        cookie: 115 Cookie
        file_path: 文件路径
        target_cid: 目标目录CID
        mode: 上传模式
    
    Returns:
        上传结果字典
    """
    uploader = Fake115UploaderWrapper(cookie)
    try:
        result = await uploader.upload_file(file_path, target_cid, mode)
        return result
    finally:
        uploader.cleanup()

