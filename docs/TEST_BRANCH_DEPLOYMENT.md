# Test 分支部署指南

## 📋 概述

test 分支是 TMC 的开发测试分支，包含最新的功能和改进。本指南将帮助你快速部署 test 版本。

## 🚀 快速开始

### 方式一：使用默认配置（推荐）

```bash
# 1. 克隆仓库并切换到 test 分支
git clone https://github.com/Hav93/TMC.git
cd TMC
git checkout test

# 2. 复制环境变量文件
cp env.example .env

# 3. 启动服务（自动使用 test 镜像）
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 方式二：直接拉取镜像

```bash
# 拉取 test 版本镜像
docker pull hav93/tmc:test

# 使用 docker run 启动
docker run -d \
  --name tmc-test \
  -p 9393:9393 \
  -v ./data:/app/data \
  -v ./sessions:/app/sessions \
  -v ./logs:/app/logs \
  -e TZ=Asia/Shanghai \
  hav93/tmc:test
```

## 🔧 配置说明

### Docker 标签配置

test 分支的 `docker-compose.yml` 默认使用 `test` 标签，你可以通过环境变量切换：

```bash
# 使用测试版本（默认）
docker-compose up -d

# 使用稳定版本
DOCKER_TAG=latest docker-compose up -d

# 使用特定版本
DOCKER_TAG=v1.2.0 docker-compose up -d
```

### 环境变量

在 `.env` 文件中配置：

```env
# Docker 镜像标签
DOCKER_TAG=test

# 应用端口
APP_PORT=9393

# 时区
TZ=Asia/Shanghai

# 其他配置...
```

## 📦 版本对比

| 版本 | 镜像标签 | 说明 | 适用场景 |
|------|---------|------|---------|
| **Test** | `hav93/tmc:test` | 测试版本，包含最新功能 | 开发测试、功能预览 |
| **Stable** | `hav93/tmc:latest` | 稳定版本，经过充分测试 | 生产环境 |
| **Specific** | `hav93/tmc:v1.x.x` | 特定版本 | 需要固定版本 |

## ⚠️ 注意事项

### 1. 数据库兼容性

**重要：test 分支不保证向后兼容！**

- ✅ **推荐**：全新部署 test 版本
- ⚠️ **不推荐**：从 stable 版本升级到 test 版本
- 🔄 如需升级，请先备份数据：

```bash
# 备份数据库
cp data/bot.db data/bot.db.backup

# 备份会话文件
cp -r sessions sessions.backup
```

### 2. 数据库重置

如果遇到数据库版本不匹配，test 分支会提示删除数据库：

```bash
# 停止并删除容器和数据卷
docker-compose down -v

# 删除数据库文件（如果需要）
rm data/bot.db

# 重新启动
docker-compose up -d
```

### 3. 容器名称

test 分支的容器名称默认为 `tmc-test`，与稳定版本的 `tmc-latest` 区分，可以在同一台机器上同时运行（需要修改端口）。

## 🔄 更新到最新版本

```bash
# 拉取最新镜像
docker-compose pull

# 重启容器
docker-compose up -d

# 查看日志确认启动成功
docker-compose logs -f
```

## 🐛 故障排查

### 容器无法启动

```bash
# 查看日志
docker-compose logs tmc

# 检查容器状态
docker-compose ps

# 重新构建并启动
docker-compose down
docker-compose up -d
```

### 数据库版本不匹配

```bash
# test 分支策略：删除旧数据库，重新创建
docker-compose down -v
rm data/bot.db
docker-compose up -d
```

### 端口冲突

修改 `.env` 文件中的端口：

```env
APP_PORT=9394  # 使用其他端口
```

## 📊 健康检查

```bash
# 检查容器健康状态
docker-compose ps

# 访问健康检查接口
curl http://localhost:9393/api/health

# 访问 Web 界面
open http://localhost:9393
```

## 🔗 相关文档

- [Test 分支数据库策略](./TEST_BRANCH_DATABASE_STRATEGY.md)
- [升级到 Test 分支](./UPGRADE_TO_TEST_BRANCH.md)
- [清理总结](./CLEANUP_SUMMARY.md)
- [本地开发指南](../local-dev/README.md)

## 💡 最佳实践

1. **测试环境**：使用 test 分支体验最新功能
2. **生产环境**：使用 latest 标签部署稳定版本
3. **数据备份**：定期备份 `data/` 和 `sessions/` 目录
4. **版本隔离**：test 和 stable 版本使用不同的容器名称和端口

## 🆘 获取帮助

如遇到问题，请：

1. 查看 [Issues](https://github.com/Hav93/TMC/issues)
2. 提交新的 Issue（请附上日志）
3. 查看项目文档

---

**祝你使用愉快！** 🎉

