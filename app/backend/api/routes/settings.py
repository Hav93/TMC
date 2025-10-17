#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统设置API路由

管理系统配置
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from log_manager import get_logger

logger = get_logger('api.settings', 'api.log')

router = APIRouter()


@router.get("")
async def get_settings():
    """
    获取系统设置
    
    返回当前的系统配置
    """
    try:
        logger.info("📋 获取系统设置")
        from config import Config
        
        # 返回当前配置
        settings = {
            "api_id": getattr(Config, 'API_ID', ''),
            "api_hash": getattr(Config, 'API_HASH', ''),
            "bot_token": getattr(Config, 'BOT_TOKEN', ''),
            "phone_number": getattr(Config, 'PHONE_NUMBER', ''),
            "admin_user_ids": getattr(Config, 'ADMIN_USER_IDS', ''),
            "enable_proxy": getattr(Config, 'ENABLE_PROXY', False),
            "proxy_type": getattr(Config, 'PROXY_TYPE', 'http'),
            "proxy_host": getattr(Config, 'PROXY_HOST', '127.0.0.1'),
            "proxy_port": getattr(Config, 'PROXY_PORT', '7890'),
            "proxy_username": getattr(Config, 'PROXY_USERNAME', ''),
            "proxy_password": "***" if getattr(Config, 'PROXY_PASSWORD', '') else '',
            "enable_log_cleanup": getattr(Config, 'ENABLE_LOG_CLEANUP', False),
            "log_retention_days": getattr(Config, 'LOG_RETENTION_DAYS', '30'),
            "log_cleanup_time": getattr(Config, 'LOG_CLEANUP_TIME', '02:00'),
            "max_log_size": getattr(Config, 'MAX_LOG_SIZE', '100'),
        }
        
        logger.info("✅ 系统设置获取成功")
        return JSONResponse(content={
            "success": True,
            "config": settings
        })
    except Exception as e:
        logger.error(f"❌ 获取设置失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取设置失败: {str(e)}"
        }, status_code=500)


@router.post("")
async def save_settings(request: Request):
    """
    保存系统设置
    
    更新 config/app.config 文件并重新加载配置
    """
    try:
        data = await request.json()
        logger.info("💾 开始保存系统设置...")
        
        # 记录主要配置项的变更
        config_changes = []
        if data.get('api_id'):
            config_changes.append(f"API_ID: {'已设置' if data.get('api_id') else '未设置'}")
        if data.get('phone_number'):
            config_changes.append(f"Phone: {data.get('phone_number')}")
        if data.get('enable_proxy'):
            proxy_info = f"{data.get('proxy_type', 'http')}://{data.get('proxy_host', '127.0.0.1')}:{data.get('proxy_port', '7890')}"
            config_changes.append(f"代理: {proxy_info}")
        else:
            config_changes.append("代理: 已禁用")
        
        logger.info(f"📝 配置变更: {', '.join(config_changes)}")
        
        # 构建新的配置内容
        config_lines = []
        
        # Telegram配置
        config_lines.append("# Telegram API配置")
        config_lines.append(f"API_ID={data.get('api_id', '')}")
        config_lines.append(f"API_HASH={data.get('api_hash', '')}")
        config_lines.append(f"BOT_TOKEN={data.get('bot_token', '')}")
        config_lines.append(f"PHONE_NUMBER={data.get('phone_number', '')}")
        config_lines.append(f"ADMIN_USER_IDS={data.get('admin_user_ids', '')}")
        config_lines.append("")
        
        # 代理配置
        config_lines.append("# 代理配置")
        enable_proxy = data.get('enable_proxy', False)
        config_lines.append(f"ENABLE_PROXY={str(enable_proxy).lower()}")
        
        # 只有在启用代理时才写入代理参数
        if enable_proxy:
            config_lines.append(f"PROXY_TYPE={data.get('proxy_type', 'http')}")
            config_lines.append(f"PROXY_HOST={data.get('proxy_host', '127.0.0.1')}")
            config_lines.append(f"PROXY_PORT={data.get('proxy_port', '7890')}")
            config_lines.append(f"PROXY_USERNAME={data.get('proxy_username', '')}")
            if data.get('proxy_password') and data.get('proxy_password') != '***':
                config_lines.append(f"PROXY_PASSWORD={data.get('proxy_password', '')}")
            logger.info(f"🌐 代理配置已启用: {data.get('proxy_type', 'http')}://{data.get('proxy_host', '127.0.0.1')}:{data.get('proxy_port', '7890')}")
        else:
            config_lines.append("# PROXY_TYPE=http")
            config_lines.append("# PROXY_HOST=127.0.0.1") 
            config_lines.append("# PROXY_PORT=7890")
            config_lines.append("# PROXY_USERNAME=")
            config_lines.append("# PROXY_PASSWORD=")
            logger.info("🚫 代理配置已禁用")
        
        config_lines.append("")
        
        # 日志配置
        config_lines.append("# 日志管理配置")
        config_lines.append(f"ENABLE_LOG_CLEANUP={str(data.get('enable_log_cleanup', False)).lower()}")
        config_lines.append(f"LOG_RETENTION_DAYS={data.get('log_retention_days', '30')}")
        config_lines.append(f"LOG_CLEANUP_TIME={data.get('log_cleanup_time', '02:00')}")
        config_lines.append(f"MAX_LOG_SIZE={data.get('max_log_size', '100')}")
        config_lines.append("")
        
        logger.info(f"📊 日志清理: {'启用' if data.get('enable_log_cleanup') else '禁用'}, 保留天数: {data.get('log_retention_days', '30')}天")
        
        # 写入配置文件（优先使用 config/app.config）
        import os
        from pathlib import Path
        
        config_content = "\n".join(config_lines)
        
        # 确保配置目录存在
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        
        # 写入到 config/app.config（持久化配置文件）
        config_file = config_dir / 'app.config'
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        logger.info(f"💾 配置已保存到: {config_file}")
        
        # 重新加载配置
        from config import Config
        Config.reload()
        
        # 重新加载代理管理器（重要！确保代理配置立即生效）
        from proxy_utils import reload_proxy_manager
        reload_proxy_manager()
        
        logger.info("🔄 配置重新加载完成（包括代理管理器）")
        logger.info("✅ 系统配置保存成功！代理配置已生效，新启动的客户端将使用新配置")
        
        # 检查是否有代理配置变更
        proxy_changed = enable_proxy or data.get('proxy_host') or data.get('proxy_port')
        
        return JSONResponse(content={
            "success": True,
            "message": "设置保存成功！代理配置已更新，请重启已运行的客户端以使其生效。" if proxy_changed else "设置保存成功！",
            "requires_client_restart": proxy_changed
        })
    except Exception as e:
        logger.error(f"❌ 保存设置失败: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "message": f"保存设置失败: {str(e)}"
        }, status_code=500)


@router.post("/test-proxy")
async def test_proxy(request: Request):
    """
    测试代理连接
    
    从请求中获取代理配置并测试连接性
    """
    try:
        data = await request.json()
        logger.info(f"🧪 测试代理连接: {data.get('proxy_type', 'http')}://{data.get('proxy_host', '127.0.0.1')}:{data.get('proxy_port', '7890')}")
        
        # 验证必需参数
        if not data.get('enable_proxy'):
            return JSONResponse(content={
                "success": False,
                "message": "代理未启用"
            }, status_code=400)
        
        proxy_host = data.get('proxy_host')
        proxy_port = data.get('proxy_port')
        
        if not proxy_host or not proxy_port:
            return JSONResponse(content={
                "success": False,
                "message": "代理配置不完整：缺少主机或端口"
            }, status_code=400)
        
        # 测试代理连接到Telegram
        import socket
        import time
        import httpx
        from proxy_utils import get_proxy_manager
        
        try:
            # 第1步: 测试TCP连接到代理服务器
            logger.info(f"🔌 步骤1: 测试代理服务器连接 {proxy_host}:{proxy_port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            start_time = time.time()
            tcp_result = sock.connect_ex((proxy_host, int(proxy_port)))
            tcp_time = time.time()
            sock.close()
            
            tcp_latency_ms = (tcp_time - start_time) * 1000
            
            if tcp_result != 0:
                error_codes = {
                    10061: "连接被拒绝 (目标端口未开放)",
                    10060: "连接超时 (目标主机无响应)",
                    10051: "网络不可达",
                    10065: "主机不可达"
                }
                error_msg = error_codes.get(tcp_result, f"连接失败 (错误码: {tcp_result})")
                logger.warning(f"❌ 代理TCP连接失败: {error_msg}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"❌ 代理连接失败\n{error_msg}\n\n请检查:\n1. 代理服务器是否运行\n2. IP和端口是否正确\n3. 防火墙设置"
                }, status_code=400)
            
            logger.info(f"✅ TCP连接成功, 延迟: {tcp_latency_ms:.0f}ms")
            
            # 第2步: 通过代理访问Telegram网站
            logger.info(f"🌐 步骤2: 通过代理访问Telegram网站...")
            
            try:
                # 构建代理URL
                proxy_type = data.get('proxy_type', 'http').lower()
                proxy_username = data.get('proxy_username', '')
                proxy_password = data.get('proxy_password', '')
                
                # 构建代理认证信息
                if proxy_username and proxy_password:
                    proxy_url = f"{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
                else:
                    proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
                
                # 测试访问Telegram网站
                test_url = "https://telegram.org"
                
                async with httpx.AsyncClient(
                    proxies=proxy_url,
                    timeout=10.0,
                    follow_redirects=True
                ) as client:
                    tg_start_time = time.time()
                    response = await client.get(test_url)
                    tg_end_time = time.time()
                    
                    tg_latency_ms = (tg_end_time - tg_start_time) * 1000
                    
                    if response.status_code == 200:
                        # 成功访问Telegram
                        total_latency = tcp_latency_ms + tg_latency_ms
                        
                        # 根据总延迟给出评价
                        if total_latency < 500:
                            speed_rating = "极快 🚀"
                        elif total_latency < 1000:
                            speed_rating = "很快 ✨"
                        elif total_latency < 2000:
                            speed_rating = "良好 ✅"
                        elif total_latency < 5000:
                            speed_rating = "一般 ⚠️"
                        else:
                            speed_rating = "较慢 🐢"
                        
                        logger.info(f"✅ Telegram访问成功: {response.status_code}, 延迟: {tg_latency_ms:.0f}ms")
                        return JSONResponse(content={
                            "success": True,
                            "message": f"✅ 代理测试成功\n\n主机: {proxy_host}\n端口: {proxy_port}\nTCP延迟: {tcp_latency_ms:.0f}ms\nTelegram延迟: {tg_latency_ms:.0f}ms\n总延迟: {total_latency:.0f}ms ({speed_rating})\n\n✅ 可以正常访问Telegram",
                            "latency_ms": round(total_latency, 2),
                            "tcp_latency_ms": round(tcp_latency_ms, 2),
                            "tg_latency_ms": round(tg_latency_ms, 2)
                        })
                    else:
                        logger.warning(f"⚠️ Telegram访问HTTP错误: {response.status_code}")
                        return JSONResponse(content={
                            "success": False,
                            "message": f"⚠️ 代理连接成功,但访问Telegram失败\n\nTCP延迟: {tcp_latency_ms:.0f}ms\nHTTP状态: {response.status_code}\n\n可能原因:\n1. 代理不支持HTTPS\n2. 代理限制了Telegram访问\n3. 网络环境问题"
                        }, status_code=400)
                        
            except httpx.ProxyError as proxy_err:
                logger.error(f"❌ 代理协议错误: {proxy_err}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"❌ 代理配置错误\n\nTCP连接: ✅ 成功 ({tcp_latency_ms:.0f}ms)\nTelegram访问: ❌ 失败\n\n错误: {str(proxy_err)}\n\n可能原因:\n1. 代理类型选择错误\n2. 需要用户名密码认证\n3. 代理协议不兼容"
                }, status_code=400)
                
            except httpx.TimeoutException:
                logger.error(f"❌ Telegram访问超时")
                return JSONResponse(content={
                    "success": False,
                    "message": f"❌ 访问Telegram超时\n\nTCP连接: ✅ 成功 ({tcp_latency_ms:.0f}ms)\nTelegram访问: ❌ 超时(>10秒)\n\n可能原因:\n1. 代理速度太慢\n2. 代理不稳定\n3. 网络环境差"
                }, status_code=400)
                
            except Exception as http_err:
                logger.error(f"❌ HTTP请求异常: {http_err}")
                return JSONResponse(content={
                    "success": False,
                    "message": f"❌ 代理测试失败\n\nTCP连接: ✅ 成功 ({tcp_latency_ms:.0f}ms)\nTelegram访问: ❌ 失败\n\n错误: {str(http_err)}"
                }, status_code=400)
                
        except socket.gaierror as e:
            logger.error(f"❌ DNS解析失败: {e}")
            return JSONResponse(content={
                "success": False,
                "message": f"❌ 无法解析主机名: {proxy_host}\n请检查主机名是否正确"
            }, status_code=400)
            
        except ValueError as e:
            logger.error(f"❌ 端口格式错误: {e}")
            return JSONResponse(content={
                "success": False,
                "message": f"❌ 端口格式错误: {proxy_port}\n请输入1-65535之间的数字"
            }, status_code=400)
            
        except Exception as e:
            logger.error(f"❌ 代理连接测试异常: {e}")
            return JSONResponse(content={
                "success": False,
                "message": f"❌ 测试失败: {str(e)}"
            }, status_code=500)
            
    except Exception as e:
        logger.error(f"❌ 测试代理失败: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False,
            "message": f"测试失败: {str(e)}"
        }, status_code=500)


"""
✅ 所有3个端点已完成!

- GET /api/settings - 获取系统设置
- POST /api/settings - 保存系统设置
- POST /api/settings/test-proxy - 测试代理连接
"""