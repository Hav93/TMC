# 升级到 v1.3.0-test 指南

## 🎯 新功能：媒体文件自动下载与管理

v1.3.0-test 版本新增了强大的媒体文件管理功能，包括：
- 📥 自动下载监控（图片、视频、音频、文档）
- 🎯 智能过滤（类型、大小、关键词、扩展名）
- 📂 自动归档整理
- ☁️ CloudDrive 集成（本地挂载 + Web API）
- 🗄️ 存储管理（自动清理、容量监控）

---

## 🚀 快速升级步骤

### 1. 更新 `docker-compose.yml`

在 `volumes` 部分添加以下配置：

```yaml
volumes:
  # ... 原有配置保持不变 ...
  
  # 媒体管理相关目录（v1.3.0 新增）
  - ${MEDIA_DOWNLOAD_PATH:-./media/downloads}:/app/media/downloads
  - ${MEDIA_STORAGE_PATH:-./media/storage}:/app/media/storage
  
  # 如果使用 CloudDrive 本地挂载（可选）:
  # - /mnt/clouddrive:/app/media/clouddrive
```

### 2. 创建必要的目录

```bash
# 创建媒体目录
mkdir -p media/downloads media/storage

# 设置权限（如果遇到权限问题）
chmod -R 755 media/
```

### 3. 拉取最新镜像并重启

```bash
# 停止现有容器
docker-compose down

# 拉取最新测试版镜像
docker-compose pull

# 启动新容器
docker-compose up -d

# 查看启动日志
docker-compose logs -f tmc
```

### 4. 验证升级成功

访问 Web 界面，应该看到新增的菜单项：
- 📊 **媒体监控** - 管理自动下载规则
- 📥 **下载任务** - 查看下载进度和历史
- 📂 **媒体文件库** - 浏览和管理已下载的文件

---

## ⚙️ 配置选项（可选）

### 基础配置（最简单）

使用默认路径，无需额外配置：
- 下载目录：`./media/downloads`
- 存储目录：`./media/storage`

### 自定义路径

编辑 `.env` 文件（没有则创建）：

```bash
# 自定义媒体路径
MEDIA_DOWNLOAD_PATH=/path/to/downloads
MEDIA_STORAGE_PATH=/path/to/storage
```

### CloudDrive 集成

**方式1: 本地挂载（推荐）**

```yaml
# docker-compose.yml
volumes:
  - /mnt/clouddrive:/app/media/clouddrive
```

**方式2: Web API**

无需修改配置文件，在 Web 界面创建规则时填写：
- CloudDrive 地址
- 用户名和密码
- 目标路径

---

## 📊 功能使用示例

### 示例1：自动下载频道图片

1. 进入 **媒体监控** 页面
2. 点击 **新建规则**
3. 配置：
   - 规则名称：`频道图片下载`
   - 监听频道：选择目标频道
   - 文件类型：勾选 `图片`
   - 文件大小：最小 `100 KB`，最大 `10 MB`
   - 归档目标：`本地存储` 或 `CloudDrive`
4. 保存并启用规则

### 示例2：下载视频并上传到网盘

1. 创建监控规则
2. 文件类型：勾选 `视频`
3. 归档设置：
   - 归档目标：`CloudDrive Web API`
   - CloudDrive 地址：`http://192.168.1.100:19798`
   - 用户名/密码：填写 CloudDrive 登录信息
   - 目标路径：`/TMC/Videos`
4. 清理设置：
   - 自动清理：启用
   - 保留时间：`7 天`（上传后7天自动清理本地）

---

## 🔍 故障排查

### 问题1：升级后无法访问 Web 界面

```bash
# 查看日志
docker-compose logs tmc

# 检查数据库迁移是否成功
docker exec tmc ls -la /app/data/
```

### 问题2：媒体目录权限错误

```bash
# 在 .env 中配置正确的用户 ID
PUID=1000
PGID=1000

# 或者手动修复权限
sudo chown -R 1000:1000 media/
```

### 问题3：数据库迁移失败

数据库会自动升级，如果失败：

```bash
# 查看详细日志
docker-compose logs tmc | grep -i alembic

# 进入容器手动检查
docker exec -it tmc bash
python3 fix_alembic_version.py
alembic upgrade head
```

---

## 🔄 回滚到旧版本

如果遇到问题需要回滚：

```bash
# 停止容器
docker-compose down

# 修改 docker-compose.yml
# 将 image 改为旧版本号
image: hav93/tmc:1.1.2

# 重新启动
docker-compose up -d
```

**重要**: 回滚前建议备份数据：

```bash
# 备份数据库
cp data/bot.db data/bot.db.backup

# 备份会话文件
cp -r sessions sessions.backup
```

---

## 📝 注意事项

1. **数据库会自动升级**，无需手动操作
2. **原有功能不受影响**，所有旧功能正常工作
3. **媒体功能是可选的**，不创建规则则不会下载任何文件
4. **建议先在测试环境验证**，确认无误后再用于生产环境

---

## 📚 详细文档

- [完整部署指南](./DOCKER_DEPLOYMENT.md)
- [环境变量配置](./env.example)
- [GitHub Issues](https://github.com/Hav93/TMC/issues)

---

## ✅ 升级清单

- [ ] 更新 `docker-compose.yml` 添加媒体目录映射
- [ ] 创建 `media/downloads` 和 `media/storage` 目录
- [ ] 设置目录权限（如果是 NAS）
- [ ] 拉取最新镜像
- [ ] 重启容器
- [ ] 访问 Web 界面验证新功能
- [ ] （可选）配置 CloudDrive 集成
- [ ] （可选）创建第一个媒体监控规则

---

最后更新: 2025-10-08  
版本: v1.3.0-test  
作者: Hav93

