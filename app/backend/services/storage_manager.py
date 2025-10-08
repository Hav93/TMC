"""
存储空间管理和自动清理服务
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger

logger = get_logger('storage_manager')
from database import get_db
from models import MediaFile, MediaMonitorRule


class StorageManager:
    """存储空间管理器"""
    
    def __init__(self):
        self.cleanup_task = None
        self.is_running = False
    
    async def start(self, check_interval: int = 3600):
        """
        启动存储管理服务
        
        Args:
            check_interval: 检查间隔（秒），默认1小时
        """
        if self.is_running:
            logger.warning("存储管理服务已在运行")
            return
        
        self.is_running = True
        logger.info("💾 启动存储空间管理服务")
        
        # 启动定时清理任务
        self.cleanup_task = asyncio.create_task(self._cleanup_loop(check_interval))
    
    async def stop(self):
        """停止存储管理服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("🛑 停止存储空间管理服务")
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self, interval: int):
        """定时清理循环"""
        logger.info(f"🔄 存储清理循环已启动（间隔: {interval}秒）")
        
        while self.is_running:
            try:
                # 等待间隔时间
                await asyncio.sleep(interval)
                
                if not self.is_running:
                    break
                
                # 执行自动清理
                logger.info("🧹 开始自动存储清理...")
                
                async for db in get_db():
                    # 获取所有启用自动清理的规则
                    result = await db.execute(
                        select(MediaMonitorRule).where(
                            and_(
                                MediaMonitorRule.is_active == True,
                                MediaMonitorRule.auto_cleanup_enabled == True
                            )
                        )
                    )
                    rules = result.scalars().all()
                    
                    for rule in rules:
                        await self._cleanup_for_rule(db, rule)
                    
                    break
                
                logger.info("✅ 自动存储清理完成")
                
            except asyncio.CancelledError:
                logger.info("清理循环被取消")
                break
            except Exception as e:
                logger.error(f"自动清理失败: {e}")
                import traceback
                traceback.print_exc()
    
    async def _cleanup_for_rule(self, db: AsyncSession, rule: MediaMonitorRule):
        """
        为单个规则执行清理
        
        Args:
            db: 数据库会话
            rule: 监控规则
        """
        try:
            logger.info(f"🧹 清理规则: {rule.name} (ID: {rule.id})")
            
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=rule.auto_cleanup_days or 7)
            
            # 查询需要清理的文件
            query = select(MediaFile).where(
                and_(
                    MediaFile.monitor_rule_id == rule.id,
                    MediaFile.downloaded_at < cutoff_date
                )
            )
            
            # 如果只清理已归档的文件
            if rule.cleanup_only_organized:
                query = query.where(MediaFile.is_organized == True)
            
            result = await db.execute(query)
            files_to_cleanup = result.scalars().all()
            
            if not files_to_cleanup:
                logger.info(f"  无需清理的文件")
                return
            
            cleaned_count = 0
            cleaned_size_mb = 0
            
            for file in files_to_cleanup:
                try:
                    # 删除临时文件
                    if file.temp_path and os.path.exists(file.temp_path):
                        file_size = os.path.getsize(file.temp_path)
                        os.remove(file.temp_path)
                        cleaned_size_mb += file_size / (1024 * 1024)
                        cleaned_count += 1
                        logger.debug(f"  🗑️ 删除临时文件: {file.temp_path}")
                    
                    # 如果文件已上传到云端，也可以删除归档文件
                    if file.is_uploaded_to_cloud and file.final_path and os.path.exists(file.final_path):
                        file_size = os.path.getsize(file.final_path)
                        os.remove(file.final_path)
                        cleaned_size_mb += file_size / (1024 * 1024)
                        logger.debug(f"  ☁️ 删除已上传文件: {file.final_path}")
                    
                    # 更新数据库记录（保留记录但清空路径）
                    if file.temp_path and not os.path.exists(file.temp_path):
                        file.temp_path = None
                    if file.final_path and not os.path.exists(file.final_path):
                        file.final_path = None
                    
                except Exception as e:
                    logger.warning(f"  清理文件失败: {file.file_name}, {e}")
            
            await db.commit()
            
            logger.info(f"  ✅ 清理完成: {cleaned_count} 个文件, {cleaned_size_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"规则清理失败: {rule.name}, {e}")
            import traceback
            traceback.print_exc()
    
    async def manual_cleanup(
        self,
        rule_id: int,
        days: int,
        only_organized: bool = True,
        delete_db_records: bool = False
    ) -> Dict[str, Any]:
        """
        手动清理
        
        Args:
            rule_id: 规则ID
            days: 保留天数
            only_organized: 是否只清理已归档文件
            delete_db_records: 是否删除数据库记录
            
        Returns:
            清理结果
        """
        try:
            async for db in get_db():
                # 获取规则
                result = await db.execute(
                    select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                )
                rule = result.scalar_one_or_none()
                
                if not rule:
                    return {
                        'success': False,
                        'message': '规则不存在'
                    }
                
                # 计算截止日期
                cutoff_date = datetime.now() - timedelta(days=days)
                
                # 查询需要清理的文件
                query = select(MediaFile).where(
                    and_(
                        MediaFile.monitor_rule_id == rule_id,
                        MediaFile.downloaded_at < cutoff_date
                    )
                )
                
                if only_organized:
                    query = query.where(MediaFile.is_organized == True)
                
                result = await db.execute(query)
                files_to_cleanup = result.scalars().all()
                
                cleaned_files = []
                cleaned_count = 0
                cleaned_size_mb = 0
                
                for file in files_to_cleanup:
                    try:
                        file_info = {
                            'name': file.file_name,
                            'size_mb': file.file_size_mb,
                            'paths_deleted': []
                        }
                        
                        # 删除临时文件
                        if file.temp_path and os.path.exists(file.temp_path):
                            os.remove(file.temp_path)
                            file_info['paths_deleted'].append(file.temp_path)
                            cleaned_size_mb += file.file_size_mb or 0
                            cleaned_count += 1
                        
                        # 删除归档文件（如果已上传到云端）
                        if file.is_uploaded_to_cloud and file.final_path and os.path.exists(file.final_path):
                            os.remove(file.final_path)
                            file_info['paths_deleted'].append(file.final_path)
                        
                        cleaned_files.append(file_info)
                        
                        # 如果要删除数据库记录
                        if delete_db_records:
                            await db.delete(file)
                        else:
                            # 只清空路径
                            file.temp_path = None
                            if file.is_uploaded_to_cloud:
                                file.final_path = None
                        
                    except Exception as e:
                        logger.warning(f"清理文件失败: {file.file_name}, {e}")
                
                await db.commit()
                
                logger.info(f"🧹 手动清理完成: {rule.name}, {cleaned_count} 个文件, {cleaned_size_mb:.2f} MB")
                
                return {
                    'success': True,
                    'message': '清理成功',
                    'cleaned_count': cleaned_count,
                    'cleaned_size_mb': round(cleaned_size_mb, 2),
                    'files': cleaned_files
                }
                
        except Exception as e:
            logger.error(f"手动清理失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'清理失败: {str(e)}'
            }
    
    async def get_storage_usage(self, rule_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取存储使用情况
        
        Args:
            rule_id: 规则ID（可选，不指定则返回所有）
            
        Returns:
            存储使用情况
        """
        try:
            async for db in get_db():
                if rule_id:
                    # 单个规则的使用情况
                    result = await db.execute(
                        select(MediaMonitorRule).where(MediaMonitorRule.id == rule_id)
                    )
                    rule = result.scalar_one_or_none()
                    
                    if not rule:
                        return {
                            'success': False,
                            'message': '规则不存在'
                        }
                    
                    temp_size, organized_size = await self._calculate_folder_sizes(rule)
                    
                    return {
                        'success': True,
                        'rule_id': rule_id,
                        'rule_name': rule.name,
                        'temp_size_gb': round(temp_size / (1024**3), 2),
                        'organized_size_gb': round(organized_size / (1024**3), 2),
                        'total_size_gb': round((temp_size + organized_size) / (1024**3), 2),
                        'max_size_gb': rule.max_storage_gb,
                        'usage_percent': round((temp_size + organized_size) / (rule.max_storage_gb * 1024**3) * 100, 2) if rule.max_storage_gb else 0,
                        'total_downloaded': rule.total_downloaded or 0,
                        'total_size_mb': rule.total_size_mb or 0
                    }
                
                else:
                    # 所有规则的使用情况
                    result = await db.execute(select(MediaMonitorRule))
                    rules = result.scalars().all()
                    
                    total_temp = 0
                    total_organized = 0
                    rules_usage = []
                    
                    for rule in rules:
                        temp_size, organized_size = await self._calculate_folder_sizes(rule)
                        total_temp += temp_size
                        total_organized += organized_size
                        
                        rules_usage.append({
                            'rule_id': rule.id,
                            'rule_name': rule.name,
                            'temp_size_gb': round(temp_size / (1024**3), 2),
                            'organized_size_gb': round(organized_size / (1024**3), 2),
                            'total_size_gb': round((temp_size + organized_size) / (1024**3), 2)
                        })
                    
                    return {
                        'success': True,
                        'total_temp_size_gb': round(total_temp / (1024**3), 2),
                        'total_organized_size_gb': round(total_organized / (1024**3), 2),
                        'total_size_gb': round((total_temp + total_organized) / (1024**3), 2),
                        'rules': rules_usage
                    }
                
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {e}")
            return {
                'success': False,
                'message': f'获取失败: {str(e)}'
            }
    
    async def _calculate_folder_sizes(self, rule: MediaMonitorRule) -> tuple:
        """
        计算文件夹大小
        
        Returns:
            (临时文件夹大小, 归档文件夹大小) 单位：字节
        """
        temp_size = 0
        organized_size = 0
        
        try:
            # 计算临时文件夹大小
            temp_folder = Path(rule.temp_folder or '/app/media/downloads')
            if temp_folder.exists():
                temp_size = sum(f.stat().st_size for f in temp_folder.rglob('*') if f.is_file())
            
            # 计算归档文件夹大小
            if rule.organize_enabled:
                if rule.organize_target_type == 'local' and rule.organize_local_path:
                    organized_folder = Path(rule.organize_local_path)
                    if organized_folder.exists():
                        organized_size = sum(f.stat().st_size for f in organized_folder.rglob('*') if f.is_file())
                
                elif rule.organize_target_type == 'clouddrive_mount' and rule.organize_clouddrive_mount:
                    mount_folder = Path(rule.organize_clouddrive_mount)
                    if mount_folder.exists():
                        organized_size = sum(f.stat().st_size for f in mount_folder.rglob('*') if f.is_file())
        
        except Exception as e:
            logger.warning(f"计算文件夹大小失败: {e}")
        
        return temp_size, organized_size
    
    async def check_and_cleanup_if_needed(self, rule_id: int) -> Dict[str, Any]:
        """
        检查存储使用情况，如果超过阈值则自动清理
        
        Args:
            rule_id: 规则ID
            
        Returns:
            检查和清理结果
        """
        try:
            usage = await self.get_storage_usage(rule_id)
            
            if not usage.get('success'):
                return usage
            
            usage_percent = usage.get('usage_percent', 0)
            max_size_gb = usage.get('max_size_gb', 100)
            
            # 如果使用率超过 90%，触发清理
            if usage_percent >= 90:
                logger.warning(f"⚠️ 存储使用率过高: {usage_percent:.1f}%，开始自动清理...")
                
                # 先清理已归档的临时文件（保留3天内的）
                cleanup_result = await self.manual_cleanup(
                    rule_id=rule_id,
                    days=3,
                    only_organized=True,
                    delete_db_records=False
                )
                
                # 重新检查使用率
                new_usage = await self.get_storage_usage(rule_id)
                new_usage_percent = new_usage.get('usage_percent', 0)
                
                if new_usage_percent >= 95:
                    # 还是不够，暂停下载队列
                    logger.error(f"🚨 存储空间严重不足: {new_usage_percent:.1f}%，建议暂停下载或增加存储配额")
                    
                    return {
                        'success': True,
                        'action': 'critical',
                        'message': '存储空间严重不足，建议暂停下载',
                        'usage_percent': new_usage_percent,
                        'cleaned': cleanup_result
                    }
                
                return {
                    'success': True,
                    'action': 'cleaned',
                    'message': '已自动清理存储空间',
                    'usage_percent': new_usage_percent,
                    'cleaned': cleanup_result
                }
            
            return {
                'success': True,
                'action': 'none',
                'message': '存储空间充足',
                'usage_percent': usage_percent
            }
            
        except Exception as e:
            logger.error(f"存储检查失败: {e}")
            return {
                'success': False,
                'message': f'检查失败: {str(e)}'
            }


# 全局存储管理器实例
_storage_manager = None


def get_storage_manager() -> StorageManager:
    """获取存储管理器单例"""
    global _storage_manager
    
    if _storage_manager is None:
        _storage_manager = StorageManager()
    
    return _storage_manager

