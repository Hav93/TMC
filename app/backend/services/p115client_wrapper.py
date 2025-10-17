"""
p115client 库包装器
使用官方 p115client 库获取115网盘信息
文档: https://libraries.io/pypi/p115client
"""
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from log_manager import get_logger

logger = get_logger('p115client_wrapper')

# 检查p115client是否可用
P115CLIENT_AVAILABLE = False
P115Client = None
check_response = None

try:
    # 尝试导入p115client
    from p115client import P115Client as _P115Client, check_response as _check_response
    P115Client = _P115Client
    check_response = _check_response
    P115CLIENT_AVAILABLE = True
    logger.info("✅ p115client库已加载")
except ImportError as e:
    logger.warning(f"⚠️ p115client库导入失败: {e}")
    logger.info("💡 将使用Web API备用方案")
except Exception as e:
    logger.error(f"❌ p115client库加载异常: {e}")
    logger.info("💡 将使用Web API备用方案")


class P115ClientWrapper:
    """p115client库的异步包装器"""
    
    def __init__(self, cookies: str):
        """
        初始化p115client客户端
        
        Args:
            cookies: 115网盘cookies字符串
        """
        if not P115CLIENT_AVAILABLE:
            raise ImportError("p115client库未安装")
        
        self.cookies = cookies
        self.client: Optional[P115Client] = None
        self._initialized = False
    
    def _init_client(self):
        """初始化P115Client（同步方法）"""
        if not self._initialized:
            try:
                # P115Client初始化可能需要在同步上下文中执行
                self.client = P115Client(self.cookies)
                self._initialized = True
                logger.info("✅ P115Client初始化成功")
            except Exception as e:
                logger.error(f"❌ P115Client初始化失败: {e}")
                raise
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        异步获取用户信息
        
        Returns:
            {
                'success': bool,
                'user_info': {
                    'user_id': str,
                    'user_name': str,
                    'email': str,
                    'mobile': str,
                    'is_vip': bool,
                    'vip_level': int,
                    'vip_name': str,
                    'space': {
                        'total': int,
                        'used': int,
                        'remain': int
                    }
                },
                'message': str
            }
        """
        try:
            # 在线程池中执行同步代码
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._get_user_info_sync)
            return result
        except Exception as e:
            logger.error(f"❌ 获取用户信息异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"获取用户信息异常: {str(e)}"
            }
    
    def _get_user_info_sync(self) -> Dict[str, Any]:
        """同步获取用户信息"""
        self._init_client()
        
        try:
            # 使用p115client的fs_space_info获取空间信息
            # 这是最可靠的方法,直接调用官方封装的接口
            logger.info("📡 使用p115client.fs_space_info()获取空间信息")
            
            # fs_space_info 返回格式类似:
            # {
            #     'total': int,  # 总空间(字节)
            #     'used': int,   # 已用空间(字节)
            #     'remain': int  # 剩余空间(字节)
            # }
            space_result = self.client.fs_space_info()
            
            # 检查响应
            checked_result = check_response(space_result)
            
            logger.info(f"📦 p115client响应: {str(checked_result)[:500]}")
            
            # 提取空间信息
            total = checked_result.get('total', 0)
            used = checked_result.get('used', 0)
            remain = checked_result.get('remain', total - used)
            
            # 尝试获取用户基本信息
            user_name = ''
            is_vip = False
            vip_level = 0
            vip_name = '普通用户'
            
            try:
                # 尝试调用user_info获取用户名和VIP信息
                user_info_result = self.client.user_info()
                user_info_checked = check_response(user_info_result)
                
                user_name = user_info_checked.get('user_name', '')
                is_vip = user_info_checked.get('is_vip', False)
                vip_level = user_info_checked.get('vip_level', 0)
                vip_name = user_info_checked.get('vip_name', '普通用户')
                
                logger.info(f"✅ 用户信息: {user_name}, VIP={vip_name}")
            except Exception as user_info_error:
                logger.warning(f"⚠️ 获取用户基本信息失败(仅影响显示): {user_info_error}")
            
            if total > 0:
                logger.info(f"✅ p115client获取空间信息成功: 总={total/1024/1024/1024:.2f}GB, 已用={used/1024/1024/1024:.2f}GB")
                return {
                    'success': True,
                    'user_info': {
                        'user_id': '',  # p115client可能不返回user_id
                        'user_name': user_name,
                        'email': '',
                        'mobile': '',
                        'is_vip': is_vip,
                        'vip_level': vip_level,
                        'vip_name': vip_name,
                        'space': {
                            'total': int(total),
                            'used': int(used),
                            'remain': int(remain)
                        }
                    },
                    'message': '使用p115client获取信息成功'
                }
            else:
                logger.warning("⚠️ p115client返回的空间信息为0")
                return {
                    'success': False,
                    'message': 'p115client返回的空间信息为0'
                }
                
        except Exception as e:
            logger.error(f"❌ p115client获取信息失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"p115client失败: {str(e)}"
            }


async def get_space_info_with_p115client(cookies: str) -> Dict[str, Any]:
    """
    使用p115client库获取空间信息
    
    Args:
        cookies: 115网盘cookies字符串
    
    Returns:
        {
            'success': bool,
            'space': {'total': int, 'used': int, 'remain': int},
            'user_info': dict,  # 可选
            'message': str
        }
    """
    if not P115CLIENT_AVAILABLE:
        return {
            'success': False,
            'message': 'p115client库不可用'
        }
    
    try:
        wrapper = P115ClientWrapper(cookies)
        result = await wrapper.get_user_info()
        
        if result.get('success'):
            user_info = result.get('user_info', {})
            return {
                'success': True,
                'space': user_info.get('space', {'total': 0, 'used': 0, 'remain': 0}),
                'user_info': user_info,
                'message': result.get('message', '成功')
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'p115client获取信息失败')
            }
    except Exception as e:
        logger.error(f"❌ get_space_info_with_p115client异常: {e}")
        return {
            'success': False,
            'message': f"p115client异常: {str(e)}"
        }

