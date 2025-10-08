# Docker 部署指南（v1.3.0-test）

## 📋 新增媒体管理功能配置

v1.3.0-test 版本新增了自动媒体下载和管理功能，需要额外配置存储路径。

---

## 🚀 快速开始

### 1. 复制环境变量配置文件

```bash
cp env.example .env
```

### 2. 编辑 `.env` 文件（可选）

根据需要修改配置，主要新增配置：

```bash
# 媒体下载临时目录
MEDIA_DOWNLOAD_PATH=./media/downloads

# 媒体归档存储目录
MEDIA_STORAGE_PATH=./media/storage
```

### 3. 启动服务

```bash
docker-compose up -d
```

---

## 📁 目录结构说明

### 原有目录（必需）

```
.
├── data/           # 数据库文件（重要）
├── logs/           # 应用日志
├── sessions/       # Telegram 会话文件（重要：登录状态）
├── temp/           # 临时文件
└── config/         # 配置文件
```

### 新增媒体管理目录（v1.3.0）

```
.
└── media/
    ├── downloads/  # 下载临时目录（下载完成后会移动到归档目录）
    └── storage/    # 归档存储目录（长期保存）
        ├── photos/     # 图片文件
        ├── videos/     # 视频文件
        ├── documents/  # 文档文件
        └── audio/      # 音频文件
```

---

## 🌐 CloudDrive 集成配置

### 方式1：本地挂载（推荐）

如果你已经将 CloudDrive 挂载到本地（如 `/mnt/clouddrive`），可以直接映射：

#### 修改 `docker-compose.yml`

```yaml
volumes:
  # ... 其他配置 ...
  
  # 取消注释并修改为你的 CloudDrive 挂载路径
  - /mnt/clouddrive:/app/media/clouddrive
```

#### 在 Web 界面配置规则时

- **归档目标**: 选择 "CloudDrive 本地挂载"
- **目标路径**: `/app/media/clouddrive/TMC` （容器内路径）

### 方式2：Web API 上传

无需修改 docker-compose.yml，直接在 Web 界面配置：

- **归档目标**: 选择 "CloudDrive Web API"
- **CloudDrive 地址**: `http://your-clouddrive-ip:19798`
- **用户名**: CloudDrive 登录用户名
- **密码**: CloudDrive 登录密码
- **目标路径**: `/TMC` （CloudDrive 网盘内路径）

---

## 📊 存储容量管理

### 自动清理配置

在 Web 界面创建媒体监控规则时，可以配置：

1. **清理策略**
   - 保留时间：如 30 天
   - 最大文件数：如 1000 个
   - 最大容量：如 100 GB

2. **清理优先级**
   - 优先清理已归档的临时文件
   - 按时间顺序清理（先删除最旧的）

### 手动清理

```bash
# 进入容器
docker exec -it tmc bash

# 清理下载临时目录
rm -rf /app/media/downloads/*

# 查看存储使用情况
du -sh /app/media/*
```

---

## 🔧 常见配置场景

### 场景1：仅本地存储

```bash
# .env
MEDIA_DOWNLOAD_PATH=./media/downloads
MEDIA_STORAGE_PATH=./media/storage
```

### 场景2：NAS 存储

```bash
# .env
MEDIA_DOWNLOAD_PATH=./media/downloads
MEDIA_STORAGE_PATH=/volume1/TMC/media  # NAS 共享目录
```

对应的 `docker-compose.yml`:

```yaml
volumes:
  - /volume1/TMC/media:/app/media/storage
```

### 场景3：CloudDrive 本地挂载

```bash
# .env
MEDIA_DOWNLOAD_PATH=./media/downloads
MEDIA_STORAGE_PATH=/mnt/clouddrive/TMC
```

对应的 `docker-compose.yml`:

```yaml
volumes:
  - /mnt/clouddrive:/app/media/clouddrive
```

### 场景4：大容量场景（使用外部硬盘）

```bash
# .env
MEDIA_DOWNLOAD_PATH=/mnt/external_disk/tmc/downloads
MEDIA_STORAGE_PATH=/mnt/external_disk/tmc/storage
```

对应的 `docker-compose.yml`:

```yaml
volumes:
  - /mnt/external_disk/tmc:/app/media
```

---

## ⚠️ 重要注意事项

### 1. 权限配置（NAS 用户必读）

如果遇到权限问题，需要配置 PUID 和 PGID：

```bash
# 查看你的用户 ID
id

# 输出示例：
# uid=1000(username) gid=1000(groupname)

# 在 .env 中配置
PUID=1000
PGID=1000
```

### 2. 存储空间要求

建议至少预留以下空间：

- **临时下载目录**: 至少 10 GB（根据下载量调整）
- **归档存储目录**: 根据需求（100 GB - 1 TB+）

### 3. 目录权限

首次启动前，确保目录存在且有写权限：

```bash
mkdir -p media/downloads media/storage
chmod -R 755 media/
```

### 4. 数据迁移

如果需要更换存储路径：

```bash
# 停止容器
docker-compose down

# 移动数据
mv ./media/storage /new/path/storage

# 修改 .env
MEDIA_STORAGE_PATH=/new/path/storage

# 重启容器
docker-compose up -d
```

---

## 📈 监控和维护

### 查看日志

```bash
# 实时查看日志
docker-compose logs -f tmc

# 查看最近 100 行
docker-compose logs --tail=100 tmc
```

### 查看存储使用

```bash
# 宿主机查看
du -sh ./media/*

# 容器内查看
docker exec tmc du -sh /app/media/*
```

### 健康检查

```bash
# 检查容器状态
docker-compose ps

# 检查健康状态
docker inspect tmc | grep Health -A 10
```

---

## 🆘 故障排查

### 问题1: 下载失败 "Permission denied"

**解决方案**:
```bash
# 检查目录权限
ls -la media/

# 修复权限
sudo chown -R 1000:1000 media/
chmod -R 755 media/
```

### 问题2: CloudDrive 上传失败

**检查清单**:
1. CloudDrive 服务是否正常运行
2. Web API 地址是否正确（包括端口）
3. 用户名密码是否正确
4. 网络是否可达（容器能否访问 CloudDrive）

```bash
# 容器内测试连通性
docker exec tmc curl http://your-clouddrive-ip:19798
```

### 问题3: 存储空间不足

**解决方案**:
1. 在 Web 界面手动清理旧文件
2. 调整清理策略（缩短保留时间）
3. 扩展存储空间或更换存储路径

---

## 📚 更多信息

- [GitHub 项目地址](https://github.com/Hav93/TMC)
- [问题反馈](https://github.com/Hav93/TMC/issues)

---

## 🔄 版本升级

从旧版本升级到 v1.3.0-test:

```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 停止旧容器
docker-compose down

# 3. 更新 docker-compose.yml（添加媒体目录映射）

# 4. 启动新容器
docker-compose up -d

# 5. 查看日志确认启动成功
docker-compose logs -f tmc
```

**注意**: 数据库会自动迁移，无需手动操作。

---

最后更新: 2025-10-08
版本: v1.3.0-test

