# 115网盘集成完整实现指南

## 📋 目录

1. [概述](#概述)
2. [前置准备](#前置准备)
3. [集成架构](#集成架构)
4. [详细实现步骤](#详细实现步骤)
5. [核心功能实现](#核心功能实现)
6. [安全与最佳实践](#安全与最佳实践)
7. [常见问题与故障排查](#常见问题与故障排查)
8. [API接口说明](#api接口说明)

---

## 概述

### 115云开放平台简介

115云开放平台（https://www.yuque.com/115yun/open）提供了完整的云存储服务API，支持文件管理、上传下载、分享等功能。本指南将详细说明如何在项目中集成115云服务。

### 集成方式

本项目支持**两种集成方式**：

1. **常规Cookie登录** ✅ **推荐用于快速开始**
   - 通过扫码登录获取Cookie凭证
   - 简单快速，无需申请开放平台账号
   - 适用于基础文件操作
   - Cookie有效期约30天

2. **开放平台OAuth认证** 🔐 **推荐用于生产环境**
   - 需要申请开放平台AppID
   - 更稳定的API访问权限
   - Access Token有效期2小时（可刷新）
   - 支持更多高级功能

---

## 前置准备

### 1. 获取115账号

- 注册115账号：https://115.com/
- 下载115 APP（iOS/Android）或115生活APP
- 建议开通VIP会员（非必须，但会有更好的体验）

### 2. 申请开放平台AppID（可选，用于OAuth方式）

#### 步骤：

1. **访问115开放平台文档**
   - 网址：https://www.yuque.com/115yun/open
   
2. **了解开放平台接入流程**
   - 阅读官方文档中的"接入指南"
   - 了解API权限和限流规则
   
3. **申请AppID**
   - 目前115开放平台采用白名单制
   - 需要联系115官方申请开放平台权限
   - 提供应用说明和使用场景
   
4. **获取AppID**
   - 审核通过后会获得AppID（纯数字）
   - **不需要AppSecret**（本项目使用OAuth 2.0 Device Flow with PKCE）

### 3. 环境准备

#### 系统要求：
- Python 3.8+
- httpx（HTTP客户端库）
- 稳定的网络连接（115是国内服务，通常不需要代理）

#### 安装依赖：
```bash
cd app/backend
pip install httpx
```

---

## 集成架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面 (Frontend)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  扫码登录    │  │  OAuth授权   │  │  文件管理    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API路由层 (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /api/pan115/regular-qrcode     - 获取登录二维码          │  │
│  │  /api/pan115/regular-qrcode/status - 检查扫码状态        │  │
│  │  /api/pan115/activate-open-api  - 激活开放平台API        │  │
│  │  /api/pan115/poll-device-token  - 轮询OAuth Token        │  │
│  │  /api/pan115/config             - 配置管理                │  │
│  │  /api/pan115/upload             - 文件上传                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Pan115Client)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  认证模块                                                  │  │
│  │  - get_regular_qrcode()      获取登录二维码               │  │
│  │  - check_regular_qrcode_status() 检查扫码状态            │  │
│  │  - get_device_code()         OAuth Device Flow           │  │
│  │  - poll_device_token()       轮询获取Token               │  │
│  │  - get_access_token()        使用Cookie+AppID获取Token   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  文件操作模块                                              │  │
│  │  - upload_file()             上传文件                     │  │
│  │  - list_files()              列出文件                     │  │
│  │  - delete_files()            删除文件                     │  │
│  │  - move_files()              移动文件                     │  │
│  │  - create_directory()        创建目录                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  用户信息模块                                              │  │
│  │  - get_user_info()           获取用户信息                 │  │
│  │  - _get_space_info_only()    获取空间信息                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      115云服务器 API                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  常规登录API                                               │  │
│  │  - qrcodeapi.115.com         二维码服务                   │  │
│  │  - passportapi.115.com       登录认证                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  开放平台API                                               │  │
│  │  - passportapi.115.com/open  OAuth认证                    │  │
│  │  - passportapi.115.com/app   Token管理                    │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Web API                                                   │  │
│  │  - webapi.115.com            文件操作                     │  │
│  │  - proapi.115.com            开放平台文件API              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │                          │
          ▼                          ▼
┌──────────────────┐        ┌──────────────────┐
│  数据库存储      │        │  文件系统存储    │
│  - Cookie        │        │  - Cookies文件   │
│  - Access Token  │        │  - 用户信息缓存  │
│  - 用户信息      │        │  - 上传临时文件  │
└──────────────────┘        └──────────────────┘
```

### 技术栈

- **后端**：Python + FastAPI + SQLAlchemy + httpx
- **前端**：React + TypeScript + Ant Design + React Query
- **认证**：OAuth 2.0 Device Flow with PKCE
- **存储**：SQLite/PostgreSQL (数据库) + 文件系统 (Cookie持久化)

---

## 详细实现步骤

### 第一步：后端核心客户端实现

#### 1.1 创建Pan115Client类

文件：`app/backend/services/pan115_client.py`

```python
"""
115网盘 Open API 客户端
基于官方文档: https://www.yuque.com/115yun/open/fd7fidbgsritauxm
"""
import httpx
import hashlib
import time
import os
import base64
import secrets
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from log_manager import get_logger

logger = get_logger('pan115')

class Pan115Client:
    """115网盘 Open API 客户端（同时支持常规登录）"""
    
    def __init__(self, app_id: str, app_key: str, user_id: str, user_key: str, use_proxy: bool = False):
        """
        初始化115网盘客户端
        
        Args:
            app_id: 应用ID (开放平台AppID)
            app_key: 应用密钥 (本项目中不使用，使用OAuth PKCE)
            user_id: 用户ID
            user_key: 用户密钥（可以是cookies字符串或access_token）
            use_proxy: 是否使用系统代理(默认False,因为115是国内服务)
        """
        self.app_id = app_id
        self.app_key = app_key
        self.user_id = user_id
        self.user_key = user_key
        self.use_proxy = use_proxy
        self.base_url = "https://proapi.115.com"  # 开放平台API
        self.open_api_url = "https://passportapi.115.com"  # OAuth API
        self.auth_url = "https://passportapi.115.com"  # 认证API
        self.webapi_url = "https://webapi.115.com"  # 常规 Web API
        self.access_token = None  # Bearer Token
    
    def _get_client_kwargs(self, timeout: float = 10.0, **extra_kwargs) -> Dict[str, Any]:
        """获取httpx.AsyncClient的参数配置"""
        kwargs = {'timeout': timeout}
        kwargs.update(extra_kwargs)
        
        if self.use_proxy:
            kwargs['trust_env'] = True  # 使用环境变量中的代理
        else:
            kwargs['trust_env'] = False
            kwargs['proxies'] = None  # 明确禁用所有代理
        
        return kwargs
```

#### 1.2 实现常规登录功能

```python
    async def get_regular_qrcode(self, app: str = "web") -> Dict[str, Any]:
        """
        获取115登录二维码
        
        Args:
            app: 应用类型
                - "web": 网页版
                - "android": Android客户端
                - "ios": iOS客户端
                - "qandroid": 115生活Android版（推荐）
                
        Returns:
            {
                "success": bool,
                "qrcode_url": str,  # 二维码图片URL
                "qrcode_token": {   # 二维码token数据
                    "uid": str,
                    "time": int,
                    "sign": str
                },
                "expires_in": int,
                "message": str
            }
        """
        try:
            # 如果配置了AppID，使用开放平台二维码
            if self.app_id:
                return await self.get_device_code()
            
            # 常规登录二维码API
            url = f"https://qrcodeapi.115.com/api/1.0/{app}/1.0/token"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') or result.get('code') == 0:
                    data = result.get('data', {})
                    
                    qrcode_token = {
                        'uid': data.get('uid', ''),
                        'time': data.get('time', 0),
                        'sign': data.get('sign', ''),
                    }
                    
                    return {
                        'success': True,
                        'qrcode_url': data.get('qrcode', ''),
                        'qrcode_token': qrcode_token,
                        'expires_in': 300,
                        'app': app,
                        'message': '获取二维码成功'
                    }
            
            return {'success': False, 'message': f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"获取二维码异常: {e}")
            return {'success': False, 'message': str(e)}

    async def check_regular_qrcode_status(self, qrcode_token: Dict[str, Any], app: str = "web") -> Dict[str, Any]:
        """
        检查常规115登录二维码状态
        
        Args:
            qrcode_token: 二维码token数据
            app: 应用类型（与获取二维码时保持一致）
            
        Returns:
            {
                "success": bool,
                "status": str,  # "waiting" | "scanned" | "confirmed" | "expired"
                "cookies": str,  # 登录成功后的cookies（status=confirmed时返回）
                "user_id": str,
                "user_info": dict,  # 完整的用户信息
                "message": str
            }
        """
        try:
            uid = qrcode_token.get('uid')
            time_val = qrcode_token.get('time')
            sign = qrcode_token.get('sign')
            
            # 检查扫码状态
            status_url = "https://qrcodeapi.115.com/get/status/"
            params = {'uid': uid, 'time': time_val, 'sign': sign}
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=30.0)) as client:
                response = await client.get(status_url, params=params)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                status_code = data.get('status', 0)
                
                # status: 0=等待扫码, 1=已扫码待确认, 2=已确认
                if status_code == 2:
                    # 获取登录凭证
                    login_url = f"https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode"
                    login_params = {'account': uid, 'app': app}
                    
                    async with httpx.AsyncClient(**self._get_client_kwargs()) as login_client:
                        login_response = await login_client.post(login_url, data=login_params)
                    
                    if login_response.status_code == 200:
                        login_result = login_response.json()
                        
                        if login_result.get('state'):
                            login_data = login_result.get('data', {})
                            cookie_dict = login_data.get('cookie', {})
                            user_id = str(login_data.get('user_id', ''))
                            
                            # 构建cookies字符串
                            cookies_parts = []
                            for key in ['UID', 'CID', 'SEID', 'KID']:
                                if key in cookie_dict:
                                    cookies_parts.append(f"{key}={cookie_dict[key]}")
                            
                            cookies_str = '; '.join(cookies_parts)
                            
                            # 构建用户信息
                            user_info = {
                                'user_id': user_id,
                                'user_name': login_data.get('user_name', ''),
                                'email': login_data.get('email', ''),
                                'is_vip': bool(login_data.get('is_vip', 0)),
                                'vip_level': login_data.get('is_vip', 0),
                                'vip_name': self._get_vip_name(login_data.get('is_vip', 0))
                            }
                            
                            return {
                                'success': True,
                                'status': 'confirmed',
                                'cookies': cookies_str,
                                'user_id': user_id,
                                'user_info': user_info,
                                'message': '登录成功'
                            }
                
                elif status_code == 1:
                    return {'success': True, 'status': 'scanned', 'message': '已扫码，等待确认'}
                else:
                    return {'success': True, 'status': 'waiting', 'message': '等待扫码'}
            
            return {'success': False, 'status': 'error', 'message': f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"检查二维码状态异常: {e}")
            return {'success': False, 'status': 'error', 'message': str(e)}
```

#### 1.3 实现OAuth 2.0 Device Flow with PKCE

```python
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """
        生成PKCE所需的code_verifier和code_challenge
        
        PKCE (Proof Key for Code Exchange) 用于防止授权码拦截攻击
        
        Returns:
            (code_verifier, code_challenge)
        """
        # 生成code_verifier: 43-128个字符的随机字符串
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # 生成code_challenge: code_verifier的SHA256哈希的base64编码
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge

    async def get_device_code(self) -> Dict[str, Any]:
        """
        获取设备授权码(OAuth Device Code Flow第一步)
        
        适用于已有AppID的情况，扫码后会自动绑定AppID权限
        
        Returns:
            {
                'success': bool,
                'device_code': str,        # 设备码（用于后续轮询）
                'user_code': str,          # 用户授权码（给用户看的）
                'verification_uri': str,   # 二维码URL
                'expires_in': int,         # 有效期（秒）
                'interval': int,           # 轮询间隔（秒）
                'code_verifier': str,      # PKCE验证码（用于后续获取token）
                'message': str
            }
        """
        try:
            if not self.app_id:
                return {'success': False, 'message': '未配置AppID'}
            
            # 生成PKCE参数
            code_verifier, code_challenge = self._generate_pkce_pair()
            
            params = {
                'client_id': self.app_id,
                'code_challenge': code_challenge,
                'code_challenge_method': 'sha256',
                'scope': 'basic'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
                response = await client.post(
                    f"{self.open_api_url}/open/authDeviceCode",
                    data=params,
                    headers=headers
                )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('state') == 1 or result.get('code') == 0:
                    data = result.get('data', result)
                    uid = data.get('uid')
                    qrcode_url = data.get('qrcode')
                    
                    if uid and qrcode_url:
                        return {
                            'success': True,
                            'device_code': uid,
                            'user_code': '',
                            'verification_uri': qrcode_url,
                            'qrcode_token': data,
                            'expires_in': 300,
                            'interval': 2,
                            'code_verifier': code_verifier,
                            'message': '请使用115 APP扫描二维码完成开放平台授权'
                        }
            
            return {'success': False, 'message': '获取授权信息失败'}
        except Exception as e:
            logger.error(f"获取设备授权码异常: {e}")
            return {'success': False, 'message': str(e)}
```

### 第二步：数据库模型设计

文件：`app/backend/models.py`

```python
from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime

class MediaSettings(Base):
    """媒体设置模型"""
    __tablename__ = 'media_settings'
    
    id = Column(Integer, primary_key=True)
    
    # 115网盘基础配置
    pan115_app_id = Column(String, comment='115开放平台AppID')
    pan115_user_id = Column(String, comment='115用户ID')
    pan115_user_key = Column(String, comment='115用户凭证(cookies)')
    pan115_device_type = Column(String, default='qandroid', comment='登录设备类型')
    pan115_request_interval = Column(Float, default=1.0, comment='API请求间隔(秒)')
    pan115_use_proxy = Column(Boolean, default=False, comment='是否使用代理')
    
    # OAuth Token管理
    pan115_access_token = Column(String, comment='115开放平台访问令牌')
    pan115_refresh_token = Column(String, comment='115开放平台刷新令牌')
    pan115_token_expires_at = Column(DateTime, comment='令牌过期时间')
    
    # 用户信息缓存
    pan115_user_info = Column(Text, comment='115用户信息(JSON格式)')
    pan115_last_refresh_at = Column(DateTime, comment='上次刷新时间')
```

### 第三步：API路由实现

文件：`app/backend/api/routes/pan115.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(tags=["115网盘"])

class RegularQRCodeRequest(BaseModel):
    """常规115登录二维码请求"""
    app: str = "qandroid"  # 推荐使用qandroid

@router.post("/regular-qrcode")
async def get_regular_qrcode(
    request: RegularQRCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取常规115登录二维码
    
    设备类型说明：
    - qandroid: 115生活Android版（推荐，最稳定）
    - android: 115网盘Android版
    - ios: 115网盘iOS版
    - web: 网页版
    """
    try:
        # 读取配置
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        
        app_id = getattr(settings, 'pan115_app_id', '') if settings else ''
        use_proxy = getattr(settings, 'pan115_use_proxy', False) if settings else False
        
        # 创建客户端
        client = Pan115Client(
            app_id=app_id,
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        
        # 获取二维码
        result = await client.get_regular_qrcode(app=request.app)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('message', '获取二维码失败'))
    except Exception as e:
        logger.error(f"获取二维码失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regular-qrcode/status")
async def check_regular_qrcode_status(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查常规115登录二维码状态
    
    请求参数：
    - qrcode_token: 二维码token数据
    - app: 设备类型
    """
    try:
        qrcode_token = request.get('qrcode_token')
        app = request.get('app', 'qandroid')
        
        if not qrcode_token:
            raise HTTPException(status_code=400, detail="缺少qrcode_token参数")
        
        # 读取配置
        result = await db.execute(select(MediaSettings))
        settings = result.scalars().first()
        use_proxy = getattr(settings, 'pan115_use_proxy', False) if settings else False
        
        # 创建客户端
        client = Pan115Client(
            app_id="",
            app_key="",
            user_id="",
            user_key="",
            use_proxy=use_proxy
        )
        
        # 检查状态
        result = await client.check_regular_qrcode_status(qrcode_token, app)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        
        # 如果登录成功，保存cookies和用户信息
        if result.get('status') == 'confirmed':
            cookies = result.get('cookies')
            user_id = result.get('user_id')
            user_info = result.get('user_info', {})
            
            if cookies and user_id:
                # 保存到数据库
                if not settings:
                    settings = MediaSettings()
                    db.add(settings)
                
                setattr(settings, 'pan115_user_id', user_id)
                setattr(settings, 'pan115_user_key', cookies)
                setattr(settings, 'pan115_device_type', app)
                
                # 保存用户信息
                import json
                setattr(settings, 'pan115_user_info', json.dumps(user_info, ensure_ascii=False))
                setattr(settings, 'pan115_last_refresh_at', datetime.utcnow())
                
                # 保存cookies到文件（持久化）
                import os
                cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
                os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
                with open(cookies_file, 'w', encoding='utf-8') as f:
                    f.write(cookies)
                
                await db.commit()
                
                logger.info(f"115登录成功: user_id={user_id}, user_name={user_info.get('user_name')}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查二维码状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 第四步：前端UI实现

文件：`app/frontend/src/pages/Settings/Pan115Settings.tsx`

关键代码片段：

```typescript
const Pan115Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [qrcodeModalVisible, setQrcodeModalVisible] = useState(false);
  const [qrcodeUrl, setQrcodeUrl] = useState('');
  const [deviceType, setDeviceType] = useState('qandroid');
  
  // 获取配置
  const { data: config } = useQuery({
    queryKey: ['pan115Config'],
    queryFn: pan115Api.getConfig,
  });
  
  // 获取二维码
  const getRegularQRCodeMutation = useMutation({
    mutationFn: (deviceType: string) => pan115Api.getRegularQRCode(deviceType),
    onSuccess: (data: any) => {
      setQrcodeUrl(data.qrcode_url);
      setQrcodeModalVisible(true);
      startPolling(data.qrcode_token, deviceType);
      message.success('请使用115 APP扫码登录');
    },
  });
  
  // 轮询检查状态
  const startPolling = (tokenData: any, loginDeviceType: string) => {
    const poll = async () => {
      const result = await pan115Api.checkRegularQRCodeStatus(tokenData, loginDeviceType);
      
      if (result.status === 'confirmed') {
        message.success('登录成功！');
        stopPolling();
        setQrcodeModalVisible(false);
        queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
      }
    };
    
    // 立即执行一次，然后每2秒轮询
    poll();
    pollingTimerRef.current = setInterval(poll, 2000);
  };
  
  return (
    <Card title="115网盘配置">
      <Form form={form} layout="vertical">
        <Form.Item label="步骤1：登录115账号">
          <Space>
            <Select value={deviceType} onChange={setDeviceType} style={{ width: 260 }}>
              <Select.Option value="qandroid">🤖 115生活 - Android</Select.Option>
              <Select.Option value="android">🤖 115网盘 - Android</Select.Option>
              <Select.Option value="ios">📱 115网盘 - iOS</Select.Option>
              <Select.Option value="web">🌐 网页版</Select.Option>
            </Select>
            <Button
              type="primary"
              icon={<QrcodeOutlined />}
              onClick={() => getRegularQRCodeMutation.mutate(deviceType)}
              loading={getRegularQRCodeMutation.isPending}
            >
              扫码登录
            </Button>
          </Space>
        </Form.Item>
        
        {/* 显示登录状态和用户信息 */}
        {config?.user_info && (
          <Alert
            message="115网盘账号已连接"
            description={
              <div>
                <p>用户: {config.user_info.user_name}</p>
                <p>会员等级: {config.user_info.vip_name}</p>
                <p>空间: {formatFileSize(config.user_info.space?.used)} / {formatFileSize(config.user_info.space?.total)}</p>
              </div>
            }
            type="success"
          />
        )}
      </Form>
      
      {/* 二维码弹窗 */}
      <Modal
        title="115网盘扫码登录"
        open={qrcodeModalVisible}
        onCancel={() => setQrcodeModalVisible(false)}
        footer={null}
      >
        <div style={{ textAlign: 'center' }}>
          <QRCode value={qrcodeUrl} size={200} />
          <p>请使用115 APP扫描二维码</p>
        </div>
      </Modal>
    </Card>
  );
};
```

---

## 核心功能实现

### 1. 文件上传

```python
async def upload_file(self, file_path: str, target_dir_id: str = "0",
                     target_path: Optional[str] = None) -> Dict[str, Any]:
    """
    上传文件到115网盘
    
    Args:
        file_path: 本地文件路径
        target_dir_id: 目标目录ID，0表示根目录
        target_path: 目标路径（如果提供，会先创建目录）
        
    Returns:
        {"success": bool, "message": str, "file_id": str, "quick_upload": bool}
    """
    try:
        # 如果提供了路径，先创建目录
        if target_path and target_path != '/':
            dir_result = await self.create_directory_path(target_path)
            if dir_result['success']:
                target_dir_id = dir_result['dir_id']
        
        # 获取上传信息
        upload_info = await self.get_upload_info(file_path, target_dir_id)
        
        if not upload_info['success']:
            return upload_info
        
        data = upload_info['data']
        
        # 检查是否已存在（秒传）
        if data.get('status') == 2 or data.get('pick_code'):
            return {
                'success': True,
                'message': '文件秒传成功',
                'file_id': data.get('file_id', ''),
                'quick_upload': True
            }
        
        # 需要真实上传
        upload_url = data.get('upload_url') or data.get('host')
        file_name = os.path.basename(file_path)
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            
            upload_params = {
                'app_id': self.app_id,
                'user_id': self.user_id,
                'user_key': self.user_key,
                'timestamp': str(int(time.time())),
                'target': target_dir_id,
            }
            
            if 'upload_params' in data:
                upload_params.update(data['upload_params'])
            
            upload_params['sign'] = self._generate_signature(upload_params)
            
            async with httpx.AsyncClient(**self._get_client_kwargs(timeout=600.0)) as client:
                response = await client.post(upload_url, files=files, data=upload_params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('state') == True or result.get('code') == 0:
                file_id = result.get('data', {}).get('file_id', '')
                return {
                    'success': True,
                    'message': '文件上传成功',
                    'file_id': file_id,
                    'quick_upload': False
                }
        
        return {'success': False, 'message': '上传失败'}
    except Exception as e:
        logger.error(f"上传文件异常: {e}")
        return {'success': False, 'message': str(e)}
```

### 2. 获取用户信息和空间信息

```python
async def get_user_info(self) -> Dict[str, Any]:
    """
    获取用户信息和空间信息
    
    支持两种方式：
    1. Cookie方式（常规登录）
    2. Access Token方式（开放平台API）
    """
    try:
        # 判断是否为常规登录
        is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)
        
        if is_cookie_auth:
            # 使用Cookie方式
            return await self._get_user_info_by_cookie()
        
        # 使用开放平台API
        params = {
            'app_id': self.app_id,
            'user_id': self.user_id,
            'user_key': self.user_key,
            'timestamp': str(int(time.time())),
        }
        params['sign'] = self._generate_signature(params)
        
        async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
            response = await client.post(f"{self.base_url}/2.0/user/info", data=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('state') == True:
                data = result.get('data', {})
                user_info = {
                    'user_id': data.get('user_id'),
                    'user_name': data.get('user_name'),
                    'is_vip': data.get('vip', {}).get('is_vip', False),
                    'vip_level': data.get('vip', {}).get('level', 0),
                    'space': {
                        'total': data.get('space', {}).get('all_total', {}).get('size', 0),
                        'used': data.get('space', {}).get('all_use', {}).get('size', 0),
                        'remain': data.get('space', {}).get('all_remain', {}).get('size', 0),
                    }
                }
                return {'success': True, 'user_info': user_info}
        
        return {'success': False, 'message': '获取用户信息失败'}
    except Exception as e:
        logger.error(f"获取用户信息异常: {e}")
        return {'success': False, 'message': str(e)}
```

---

## 安全与最佳实践

### 1. Cookie持久化

```python
# 保存Cookie到文件（防止数据库问题导致Cookie丢失）
import os

cookies_file = os.path.join('/app', 'config', '115-cookies.txt')
os.makedirs(os.path.dirname(cookies_file), exist_ok=True)

with open(cookies_file, 'w', encoding='utf-8') as f:
    f.write(cookies_str)

logger.info(f"✅ Cookies已保存到文件: {cookies_file}")
```

### 2. Token过期处理

```python
async def refresh_access_token(self) -> Dict[str, Any]:
    """
    刷新Access Token
    
    当access_token过期时，可以使用refresh_token获取新的token
    """
    if not self.refresh_token:
        return await self.get_access_token()  # 回退到使用Cookie+AppID重新获取
    
    # 使用refresh_token刷新
    # 注意：115可能不支持refresh_token，需要根据实际API调整
```

### 3. API限流处理

```python
import asyncio

class Pan115Client:
    def __init__(self, ..., request_interval: float = 1.0):
        self.request_interval = request_interval
        self.last_request_time = 0
    
    async def _rate_limit(self):
        """API限流控制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    async def upload_file(self, ...):
        await self._rate_limit()  # 每次调用API前等待
        # ... 实际上传逻辑
```

### 4. 错误重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _request_with_retry(self, method: str, url: str, **kwargs):
    """带重试的HTTP请求"""
    async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
        if method == 'GET':
            return await client.get(url, **kwargs)
        elif method == 'POST':
            return await client.post(url, **kwargs)
```

### 5. 代理配置（可选）

115是国内服务，通常不需要代理。但如果您的服务器在国外，可能需要配置代理：

```python
class Pan115Client:
    def _get_client_kwargs(self, timeout: float = 10.0, **extra_kwargs):
        kwargs = {'timeout': timeout}
        
        if self.use_proxy:
            # 使用环境变量中的代理配置
            # export HTTP_PROXY=http://proxy.example.com:8080
            # export HTTPS_PROXY=http://proxy.example.com:8080
            kwargs['trust_env'] = True
        else:
            kwargs['trust_env'] = False
            kwargs['proxies'] = None
        
        return kwargs
```

---

## 常见问题与故障排查

### 问题1：获取二维码失败

**症状**：调用`get_regular_qrcode()`返回错误

**可能原因**：
- 网络连接问题
- 115服务器临时故障
- 代理配置错误

**解决方案**：
```bash
# 1. 测试网络连接
curl https://qrcodeapi.115.com/

# 2. 检查日志
tail -f app/backend/logs/pan115.log

# 3. 禁用代理重试
# 在设置页面关闭"使用代理"选项
```

### 问题2：扫码成功但Cookie未保存

**症状**：扫码成功，但刷新后显示未登录

**可能原因**：
- 数据库写入失败
- Cookie文件写入权限问题

**解决方案**：
```bash
# 1. 检查Cookie文件权限
ls -la /app/config/115-cookies.txt

# 2. 确保目录有写权限
chmod 755 /app/config
chmod 644 /app/config/115-cookies.txt

# 3. 查看数据库
sqlite3 data/bot.db "SELECT pan115_user_id FROM media_settings;"
```

### 问题3：空间信息显示为0

**症状**：登录成功，但空间信息全为0

**可能原因**：
- 115 API限流（最常见）
- Cookie已过期
- API返回格式变化

**解决方案**：
```python
# 1. 等待1-2分钟后点击"刷新用户信息"
# 2. 检查后端日志查看详细错误
# 3. 尝试使用开放平台API（更稳定）

# 前端会自动使用缓存数据，不会影响正常使用
```

### 问题4：文件上传失败

**症状**：上传文件时报错

**可能原因**：
- 文件过大（超过VIP限制）
- 网络超时
- 目标目录不存在
- 签名验证失败

**解决方案**：
```python
# 1. 检查文件大小
import os
file_size = os.path.getsize(file_path)
print(f"文件大小: {file_size / 1024 / 1024:.2f} MB")

# 2. 增加超时时间
client = Pan115Client(..., timeout=600)  # 10分钟

# 3. 测试创建目录
result = await client.create_directory('test_dir')
```

### 问题5：OAuth激活失败

**症状**：点击"启用OPENAPI"后报错

**可能原因**：
- AppID未配置或无效
- Cookie已过期，需要重新登录
- 115服务器问题

**解决方案**：
```python
# 1. 确认AppID正确
# 2. 先扫码登录获取Cookie
# 3. 再激活开放平台API

# 查看详细错误日志
tail -f app/backend/logs/pan115.log | grep "activate"
```

---

## API接口说明

### 后端API端点

#### 1. 获取配置
```
GET /api/pan115/config
```

**响应**：
```json
{
  "pan115_app_id": "123456",
  "pan115_user_id": "987654321",
  "pan115_user_key": "UID=****",
  "is_configured": true,
  "open_api_activated": false,
  "user_info": {
    "user_name": "用户名",
    "vip_name": "年费VIP",
    "space": {
      "total": 107374182400,
      "used": 53687091200,
      "remain": 53687091200
    }
  }
}
```

#### 2. 更新配置
```
POST /api/pan115/config
```

**请求**：
```json
{
  "pan115_app_id": "123456",
  "pan115_request_interval": 1.0,
  "pan115_use_proxy": false
}
```

#### 3. 获取登录二维码
```
POST /api/pan115/regular-qrcode
```

**请求**：
```json
{
  "app": "qandroid"
}
```

**响应**：
```json
{
  "success": true,
  "qrcode_url": "data:image/png;base64,...",
  "qrcode_token": {
    "uid": "abc123",
    "time": 1698765432,
    "sign": "xyz789"
  },
  "expires_in": 300,
  "message": "获取二维码成功"
}
```

#### 4. 检查扫码状态
```
POST /api/pan115/regular-qrcode/status
```

**请求**：
```json
{
  "qrcode_token": {
    "uid": "abc123",
    "time": 1698765432,
    "sign": "xyz789"
  },
  "app": "qandroid"
}
```

**响应**：
```json
{
  "success": true,
  "status": "confirmed",
  "user_id": "987654321",
  "user_info": {
    "user_name": "用户名",
    "is_vip": true,
    "vip_level": 5,
    "vip_name": "年费VIP"
  },
  "message": "登录成功"
}
```

#### 5. 激活开放平台API
```
POST /api/pan115/activate-open-api
```

**响应**：
```json
{
  "success": true,
  "message": "✅ 开放平台API已激活",
  "user_info": {...},
  "has_space_info": true
}
```

#### 6. 上传文件
```
POST /api/pan115/upload
```

**请求**：
```json
{
  "file_path": "/path/to/local/file.mp4",
  "remote_path": "/telegram_downloads"
}
```

**响应**：
```json
{
  "success": true,
  "file_id": "file123",
  "file_name": "file.mp4",
  "is_quick": false,
  "message": "上传成功"
}
```

#### 7. 刷新用户信息
```
POST /api/pan115/refresh-user-info
```

**响应**：
```json
{
  "success": true,
  "message": "✅ 用户信息已刷新",
  "user_info": {...},
  "from_cache": false
}
```

---

## 总结

### 完整集成流程

```
1. 用户扫码登录 (常规方式)
   └─> 获取Cookie
       └─> 保存到数据库和文件系统
           └─> 可以使用基础文件操作功能

2. (可选) 激活开放平台API
   └─> 配置AppID
       └─> 使用Cookie+AppID获取Access Token
           └─> 获得更稳定的API访问权限
```

### 技术特点

✅ **双模式支持**：Cookie登录（快速） + OAuth API（稳定）  
✅ **安全可靠**：PKCE防拦截 + Cookie持久化  
✅ **用户友好**：自动轮询 + 实时状态反馈  
✅ **容错机制**：缓存用户信息 + 自动重试  
✅ **防抖优化**：30秒防抖 + API限流控制  

### 下一步

1. **测试上传功能**：实现文件上传到115
2. **实现自动备份**：定时备份重要文件
3. **添加分享功能**：生成115分享链接
4. **监控Token有效期**：自动刷新过期Token

---

## 参考资料

- 📚 [115开放平台官方文档](https://www.yuque.com/115yun/open)
- 🔐 [OAuth 2.0 Device Flow RFC 8628](https://datatracker.ietf.org/doc/html/rfc8628)
- 🛡️ [PKCE RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636)
- 🎯 [项目现有实现参考](./115_OAUTH_DEVICE_FLOW_GUIDE.md)

---

**文档版本**：v1.0  
**最后更新**：2025-01-17  
**作者**：TMC项目团队





