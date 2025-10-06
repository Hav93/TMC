"""
中间件 - 全局请求处理
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from auth import SECRET_KEY, ALGORITHM
from log_manager import get_logger

logger = get_logger('middleware', 'api.log')

# 不需要认证的路径列表
WHITELIST_PATHS = [
    "/api/auth/login",
    "/api/auth/register",
    "/health",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    全局认证中间件
    
    - 保护所有 /api 路径（除了白名单）
    - 验证 JWT Token
    - 静态资源和前端路由不受影响
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 静态文件和前端路由不需要认证
        if (not path.startswith("/api") or 
            path in WHITELIST_PATHS or
            any(path.startswith(whitelist) for whitelist in WHITELIST_PATHS)):
            return await call_next(request)
        
        # 检查Authorization头或查询参数中的token（支持SSE/EventSource）
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            logger.debug(f"从Header获取token: {path}")
        else:
            # 从查询参数获取token（用于EventSource等无法设置请求头的场景）
            token = request.query_params.get("token")
            if token:
                logger.debug(f"从查询参数获取token: {path}, token长度={len(token)}")
            else:
                logger.warning(f"🔍 调试: {path} - 查询参数: {dict(request.query_params)}")
        
        if not token:
            logger.warning(f"🚫 未授权访问: {path} - 缺少认证令牌")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            # 将用户信息添加到request state（可选）
            request.state.username = username
            
        except JWTError as e:
            logger.warning(f"🚫 Token验证失败: {path} - {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Token验证通过，继续处理请求
        response = await call_next(request)
        return response

