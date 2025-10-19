"""
CloudDrive2 上传器（集成进度和断点续传）

将 CloudDrive2 客户端与现有的进度管理、断点续传工具集成
"""
import os
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from log_manager import get_logger
from services.clouddrive2_client import CloudDrive2Client, CloudDrive2Config, create_clouddrive2_client
from services.upload_progress_manager import get_progress_manager, UploadStatus
from services.upload_resume_manager import get_resume_manager
from services.quick_upload_service import QuickUploadService

logger = get_logger(__name__)


class CloudDrive2Uploader:
    """
    CloudDrive2 上传器
    
    功能：
    1. 通过 CloudDrive2 上传文件到 115 网盘
    2. 集成进度管理（实时显示上传进度）
    3. 集成断点续传（支持恢复中断的上传）
    4. 集成秒传检测（节省带宽）
    """
    
    def __init__(
        self,
        clouddrive2_host: str = "localhost",
        clouddrive2_port: int = 19798,
        mount_point: str = "/115"
    ):
        """
        初始化上传器
        
        Args:
            clouddrive2_host: CloudDrive2 服务地址
            clouddrive2_port: CloudDrive2 服务端口
            mount_point: 115 网盘挂载点路径
        """
        self.clouddrive2_host = clouddrive2_host
        self.clouddrive2_port = clouddrive2_port
        self.mount_point = mount_point
        
        # 初始化管理器
        self.progress_mgr = get_progress_manager()
        self.resume_mgr = get_resume_manager()
        self.quick_service = QuickUploadService()
        
        self.client: Optional[CloudDrive2Client] = None
    
    async def upload_file(
        self,
        file_path: str,
        target_dir: str = "",
        enable_quick_upload: bool = True,
        enable_resume: bool = True
    ) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_path: 本地文件路径
            target_dir: 目标目录（相对于挂载点）
            enable_quick_upload: 是否启用秒传检测
            enable_resume: 是否启用断点续传
        
        Returns:
            上传结果字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': f'文件不存在: {file_path}'
                }
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            logger.info(f"📤 准备上传: {file_name} ({file_size} bytes)")
            logger.info(f"   目标目录: {target_dir or '/'}")
            logger.info(f"   秒传检测: {'开启' if enable_quick_upload else '关闭'}")
            logger.info(f"   断点续传: {'开启' if enable_resume else '关闭'}")
            
            # 创建进度跟踪
            progress = self.progress_mgr.create_progress(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                target_dir_id=target_dir
            )
            
            try:
                # 步骤1: 秒传检测
                if enable_quick_upload:
                    progress.status = UploadStatus.CHECKING
                    self.progress_mgr.update_progress(progress)
                    
                    logger.info("🔍 检查秒传...")
                    quick_result = self.quick_service.calculate_sha1(file_path)
                    
                    if quick_result:
                        logger.info(f"✅ SHA1: {quick_result}")
                        # TODO: 调用115秒传API检查
                        # 如果秒传成功，直接返回
                
                # 步骤2: 检查断点续传
                session = None
                if enable_resume:
                    session = await self.resume_mgr.get_session(file_path, target_dir)
                    if session:
                        logger.info(f"📋 发现未完成的上传会话: {session.session_id}")
                        logger.info(f"   进度: {session.get_progress():.2f}%")
                
                # 步骤3: 连接 CloudDrive2
                logger.info("🔌 连接 CloudDrive2...")
                self.client = create_clouddrive2_client(
                    host=self.clouddrive2_host,
                    port=self.clouddrive2_port
                )
                
                connected = await self.client.connect()
                if not connected:
                    return {
                        'success': False,
                        'message': 'CloudDrive2 连接失败'
                    }
                
                # 步骤4: 检查挂载点
                logger.info(f"🗂️ 检查挂载点: {self.mount_point}")
                mount_status = await self.client.check_mount_status(self.mount_point)
                
                if not mount_status.get('available'):
                    return {
                        'success': False,
                        'message': f"挂载点不可用: {mount_status.get('message', '未知错误')}"
                    }
                
                logger.info("✅ 挂载点可用")
                
                # 步骤5: 执行上传
                progress.status = UploadStatus.UPLOADING
                self.progress_mgr.update_progress(progress)
                
                # 构建远程路径
                remote_path = os.path.join(target_dir, file_name)
                
                # 进度回调
                def progress_callback(uploaded: int, total: int):
                    progress.uploaded_bytes = uploaded
                    progress.percentage = (uploaded / total * 100) if total > 0 else 0
                    self.progress_mgr.update_progress(progress)
                
                result = await self.client.upload_file(
                    local_path=file_path,
                    remote_path=remote_path,
                    mount_point=self.mount_point,
                    progress_callback=progress_callback
                )
                
                # 步骤6: 更新状态
                if result['success']:
                    progress.status = UploadStatus.SUCCESS
                    progress.uploaded_bytes = file_size
                    progress.percentage = 100
                    
                    # 清理断点续传会话
                    if session:
                        await self.resume_mgr.delete_session(session.session_id)
                    
                    logger.info(f"✅ 上传成功: {file_name}")
                else:
                    progress.status = UploadStatus.FAILED
                    logger.error(f"❌ 上传失败: {result.get('message')}")
                
                self.progress_mgr.update_progress(progress)
                
                return result
            
            finally:
                # 断开连接
                if self.client:
                    await self.client.disconnect()
        
        except Exception as e:
            logger.error(f"❌ 上传异常: {e}", exc_info=True)
            
            # 更新进度状态
            if hasattr(self, 'progress_mgr'):
                try:
                    progress.status = UploadStatus.FAILED
                    self.progress_mgr.update_progress(progress)
                except:
                    pass
            
            return {
                'success': False,
                'message': str(e)
            }
    
    async def batch_upload(
        self,
        file_paths: list,
        target_dir: str = "",
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        批量上传文件
        
        Args:
            file_paths: 文件路径列表
            target_dir: 目标目录
            max_concurrent: 最大并发数
        
        Returns:
            批量上传结果
        """
        logger.info(f"📦 批量上传: {len(file_paths)} 个文件")
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def upload_with_limit(path):
            async with semaphore:
                return await self.upload_file(path, target_dir)
        
        tasks = [upload_with_limit(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed_count = len(results) - success_count
        
        logger.info(f"📊 批量上传完成: 成功 {success_count}, 失败 {failed_count}")
        
        return {
            'success': failed_count == 0,
            'total': len(file_paths),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }


# 全局上传器实例
_uploader: Optional[CloudDrive2Uploader] = None


def get_clouddrive2_uploader(
    host: str = None,
    port: int = None,
    mount_point: str = None
) -> CloudDrive2Uploader:
    """
    获取全局 CloudDrive2 上传器实例
    
    Args:
        host: CloudDrive2 服务地址
        port: CloudDrive2 服务端口
        mount_point: 挂载点路径
    """
    global _uploader
    
    if _uploader is None:
        _uploader = CloudDrive2Uploader(
            clouddrive2_host=host or os.getenv('CLOUDDRIVE2_HOST', 'localhost'),
            clouddrive2_port=port or int(os.getenv('CLOUDDRIVE2_PORT', '19798')),
            mount_point=mount_point or os.getenv('CLOUDDRIVE2_MOUNT_POINT', '/115')
        )
    
    return _uploader

