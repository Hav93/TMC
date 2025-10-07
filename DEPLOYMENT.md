# TMC 部署指南

本文档介绍如何使�?Docker Hub 预构建镜像快速部�?TMC�?

---

## 🚀 快速开�?

### 前置要求
- Docker �?Docker Compose
- Telegram API 凭证（从 https://my.telegram.org 获取�?

### 部署步骤

#### 1. 创建部署目录

```bash
mkdir tmc && cd tmc
```

#### 2. 下载配置文件

创建 `docker-compose.yml` 文件�?

```yaml
version: '3.8'

services:
  tmc:
    image: hav93/tmc:latest
    container_name: tmc
    restart: always
    ports:
      - "9393:9393"
    environment:
      - TZ=Asia/Shanghai
      # Telegram API配置（必填）
      - API_ID=${API_ID}
      - API_HASH=${API_HASH}
      - BOT_TOKEN=${BOT_TOKEN}
      - PHONE_NUMBER=${PHONE_NUMBER}
      - ADMIN_USER_IDS=${ADMIN_USER_IDS}
      
      # JWT密钥（建议自定义�?
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-secret-key-change-me}
      
      # 代理配置（可选）
      - ENABLE_PROXY=false
      
      # 权限配置（NAS推荐�?
      - PUID=${PUID:-1000}
      - PGID=${PGID:-1000}
      
      # 数据库配�?
      - DATABASE_URL=sqlite:///data/bot.db
      
      # 日志级别
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./sessions:/app/sessions
      - ./temp:/app/temp
      - ./config:/app/config
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9393/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

#### 3. 创建环境变量文件

创建 `.env` 文件�?

```bash
# Telegram API 配置（从 https://my.telegram.org 获取�?
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
PHONE_NUMBER=+8613800138000
ADMIN_USER_IDS=123456789

# JWT 密钥（建议修改）
JWT_SECRET_KEY=your-secret-key-please-change-me

# 权限配置（可选）
PUID=1000
PGID=1000

# 日志级别
LOG_LEVEL=INFO
```

#### 4. 启动服务

```bash
docker compose up -d
```

#### 5. 访问系统

打开浏览器访�? http://localhost:9393

**默认账号**:
- 用户�? `admin`
- 密码: `admin123`
- ⚠️ **首次登录后请立即修改密码�?*

---

## 📋 配置说明

### 必填配置

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `API_ID` | Telegram API ID | `12345678` |
| `API_HASH` | Telegram API Hash | `abcdef1234567890` |
| `BOT_TOKEN` | Telegram Bot Token | `123456:ABC-DEF...` |
| `PHONE_NUMBER` | 管理员手机号 | `+8613800138000` |
| `ADMIN_USER_IDS` | 管理员用户ID | `123456789` |

### 可选配�?

| 环境变量 | 说明 | 默认�?|
|---------|------|--------|
| `JWT_SECRET_KEY` | JWT加密密钥 | `your-secret-key-change-me` |
| `PUID` | 运行用户ID | `1000` |
| `PGID` | 运行组ID | `1000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `TZ` | 时区 | `Asia/Shanghai` |

### 代理配置（可选）

如果需要代理访�?Telegram�?

```env
ENABLE_PROXY=true
PROXY_TYPE=http
PROXY_HOST=127.0.0.1
PROXY_PORT=7890
```

---

## 🔧 常用命令

### 查看日志

```bash
docker compose logs -f tmc
```

### 重启服务

```bash
docker compose restart
```

### 停止服务

```bash
docker compose down
```

### 更新镜像

```bash
docker compose pull
docker compose up -d
```

### 备份数据

```bash
# 备份重要目录
tar -czf tmc-backup-$(date +%Y%m%d).tar.gz data sessions config
```

### 恢复数据

```bash
# 解压备份文件
tar -xzf tmc-backup-20251006.tar.gz
```

---

## 🐛 故障排查

### 1. 容器无法启动

```bash
# 查看详细日志
docker compose logs tmc

# 检查端口是否被占用
netstat -tuln | grep 9393
```

### 2. 登录失败

- 检查数据库是否正常初始�?
- 确认 JWT_SECRET_KEY 配置正确
- 尝试删除 `data/` 目录重新初始�?

### 3. Telegram 连接失败

- 检�?API_ID、API_HASH、BOT_TOKEN 是否正确
- 如果在国内，确认代理配置是否正确
- 检查网络连�?

### 4. 权限问题（NAS�?

如果遇到文件权限错误�?

```bash
# 查看当前用户ID
id

# 设置正确�?PUID �?PGID
# �?.env 文件中设置为你的用户ID
```

---

## 🔐 安全建议

1. **修改默认密码**: 首次登录后立即修�?admin 密码
2. **自定�?JWT 密钥**: 使用强随机密�?
   ```bash
   # 生成随机密钥
   openssl rand -hex 32
   ```
3. **限制端口访问**: 使用反向代理（Nginx）并启用 HTTPS
4. **定期备份**: 备份 `data/`、`sessions/` �?`config/` 目录
5. **更新镜像**: 定期拉取最新镜像获取安全更�?

---

## 📊 目录说明

| 目录 | 说明 | 是否需要备�?|
|------|------|------------|
| `data/` | 数据库文�?| �?必须 |
| `sessions/` | Telegram 会话 | �?必须 |
| `config/` | 配置文件 | �?推荐 |
| `logs/` | 应用日志 | �?可�?|
| `temp/` | 临时文件 | �?不需�?|

---

## 🌐 使用反向代理

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name tmc.example.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tmc.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:9393;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📱 NAS 部署指南

### Synology DSM

1. 打开 **Container Manager**（原Docker套件�?
2. �?**项目** 中点�?**新建**
3. 设置项目名称�?`tmc`
4. 粘贴上述 `docker-compose.yml` 内容
5. 配置环境变量
6. 点击 **完成** 启动

### QNAP

1. 打开 **Container Station**
2. 点击 **创建** �?**创建应用**
3. 粘贴 `docker-compose.yml` 内容
4. 配置环境变量和存储路�?
5. 启动应用

### 威联�?群晖 权限设置

```bash
# 设置正确的所有�?
sudo chown -R 1000:1000 ./data ./sessions ./config

# 或使用你的用户ID
id  # 查看你的 UID �?GID
sudo chown -R YOUR_UID:YOUR_GID ./data ./sessions ./config
```

---

## 📞 获取帮助

- **GitHub Issues**: https://github.com/your-repo/tmc/issues
- **文档**: 查看项目�?`PROJECT_STATUS.md`
- **Docker Hub**: https://hub.docker.com/r/hav93/tmc

---

## 🔄 版本更新

### 查看当前版本

```bash
docker exec tmc cat /app/VERSION
```

### 更新到最新版�?

```bash
# 1. 备份数据
tar -czf tmc-backup-$(date +%Y%m%d).tar.gz data sessions config

# 2. 拉取最新镜�?
docker compose pull

# 3. 重启容器
docker compose up -d

# 4. 查看日志确认启动成功
docker compose logs -f
```

---

**最后更新**: 2025-10-07  
**当前版本**: v1.1.0  
**镜像版本**: hav93/tmc:latest, hav93/tmc:1.1.0

