# 🚀 服务器部署指南

> **重要**：修复JWT Token失效和bcrypt版本问题

---

## ⚠️ 常见部署问题修复

### 问题1：JWT Token验证失败

**症状**：
```
WARNING | middleware:dispatch:79 - 🚫 Token验证失败: /api/auth/me - Signature verification failed.
INFO: "GET /api/auth/me?_t=xxx HTTP/1.1" 401 Unauthorized
```

**原因**：
- 未设置环境变量`JWT_SECRET_KEY`
- 每次容器重启生成新的随机密钥
- 旧的token无法验证

**解决方案**：

1. **生成固定的JWT密钥**：
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **在服务器上设置环境变量**：
   
   编辑`.env`文件：
   ```bash
   # JWT密钥（生产环境必须设置！）
   JWT_SECRET_KEY=your-generated-secret-key-here
   
   # JWT过期时间（默认24小时=1440分钟）
   JWT_EXPIRE_MINUTES=1440
   ```

3. **重启容器**：
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

### 问题2：bcrypt版本错误

**症状**：
```
(trapped) error reading bcrypt version
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/passlib/handlers/bcrypt.py", line 620, in _load_backend_mixin
    version = _bcrypt.__about__.__version__
              ^^^^^^^^^^^^^^^^^
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**原因**：
- bcrypt 4.2.1版本改变了API
- passlib 1.7.4不兼容

**解决方案**：

✅ **已在requirements.txt中修复**（降级到bcrypt 4.0.1）

如果您已经部署，需要重新构建镜像：
```bash
# 拉取最新代码
git pull origin test

# 重新构建
docker-compose build --no-cache

# 启动
docker-compose up -d
```

---

## 📋 完整部署步骤

### 1. 准备环境

**服务器要求**：
- Docker 20.10+
- Docker Compose 2.0+
- 内存：≥2GB
- 磁盘：≥10GB

### 2. 克隆代码

```bash
git clone https://github.com/Hav93/TMC.git
cd TMC
git checkout test
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp env.example .env

# 编辑配置
nano .env
```

**必须配置的项目**：

```bash
# ========== 基础配置 ==========
APP_PORT=9393
TZ=Asia/Shanghai

# ========== JWT配置（重要！）==========
# 生成密钥：python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-generated-secret-key-here
JWT_EXPIRE_MINUTES=1440

# ========== Telegram配置（可选）==========
# API_ID=your-api-id
# API_HASH=your-api-hash

# ========== 代理配置（如果需要）==========
# ENABLE_PROXY=true
# PROXY_TYPE=socks5
# PROXY_HOST=127.0.0.1
# PROXY_PORT=7890
```

### 4. 启动服务

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 5. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:9393/health

# 访问Web界面
http://your-server-ip:9393
```

---

## 🔧 故障排查

### 检查日志

```bash
# 查看所有日志
docker-compose logs -f

# 只看最近100行
docker-compose logs --tail=100

# 只看错误
docker-compose logs | grep ERROR
```

### 常见错误

#### 1. 端口被占用

**错误信息**：
```
Error starting userland proxy: listen tcp4 0.0.0.0:9393: bind: address already in use
```

**解决方案**：
```bash
# 查看占用端口的进程
sudo lsof -i :9393

# 或者修改.env中的APP_PORT
APP_PORT=9394
```

#### 2. 数据库锁定

**错误信息**：
```
sqlite3.OperationalError: database is locked
```

**解决方案**：
```bash
# 停止容器
docker-compose down

# 删除锁文件
rm data/bot.db-shm data/bot.db-wal

# 重新启动
docker-compose up -d
```

#### 3. Cookie文件权限

**错误信息**：
```
PermissionError: [Errno 13] Permission denied: '/app/config/115-cookies.txt'
```

**解决方案**：
```bash
# 修改权限
chmod 755 config/
chmod 644 config/*.txt
```

---

## 🔒 安全建议

### 1. 设置防火墙

```bash
# 只允许特定IP访问
sudo ufw allow from 192.168.1.0/24 to any port 9393

# 或使用nginx反向代理
```

### 2. 使用HTTPS

**Nginx配置示例**：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:9393;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 定期备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

mkdir -p $BACKUP_DIR

# 备份数据库
cp data/bot.db $BACKUP_DIR/bot_$DATE.db

# 备份配置
cp config/*.txt $BACKUP_DIR/ 2>/dev/null

# 备份sessions
tar -czf $BACKUP_DIR/sessions_$DATE.tar.gz sessions/

echo "Backup completed: $BACKUP_DIR"
```

### 4. 环境变量安全

```bash
# 确保.env文件权限
chmod 600 .env

# 不要提交.env到git
echo ".env" >> .gitignore
```

---

## 📊 监控和维护

### 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 清理Docker资源
docker system prune -a
```

### 日志轮转

**logrotate配置**：

```bash
# /etc/logrotate.d/tmc
/path/to/TMC/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    copytruncate
}
```

### 自动更新

```bash
#!/bin/bash
# update.sh

cd /path/to/TMC

# 拉取最新代码
git pull origin test

# 重新构建
docker-compose build --no-cache

# 重启服务
docker-compose up -d

# 查看日志
docker-compose logs -f --tail=50
```

---

## 🎯 性能优化

### 1. 数据库优化

```bash
# 定期清理数据库
docker exec tmc-backend sqlite3 /app/data/bot.db "VACUUM;"
```

### 2. Docker资源限制

**docker-compose.yml**：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 1G
```

### 3. 使用外部数据库

```bash
# .env配置
DATABASE_URL=postgresql://user:pass@host:5432/tmc
```

---

## 📝 更新日志

**v1.3.1-test (2025-10-17)**
- ✅ 修复JWT Token验证失败问题
- ✅ 修复bcrypt版本兼容性问题
- ✅ 更新环境变量配置说明
- ✅ 添加服务器部署指南

---

## 🆘 需要帮助？

1. **查看文档**：
   - `docs/115_正确使用流程.md` - 115网盘使用
   - `README.md` - 项目说明
   - `DEPLOYMENT.md` - 部署文档

2. **查看日志**：
   ```bash
   docker-compose logs -f
   ```

3. **提交Issue**：
   - GitHub：https://github.com/Hav93/TMC/issues

---

**部署完成后，记得设置JWT_SECRET_KEY！** 🔐

