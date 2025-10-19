# 🔍 GitHub Actions 镜像构建诊断

## 📊 问题分析

### 当前状况

1. **本地源代码**: ✅ 最新（包含OPTIONS修复）
2. **本地Docker镜像**: ✅ 重新构建后已更新
3. **GitHub Actions**: ❓ 需要检查
4. **Docker Hub镜像**: ❓ 可能是旧的
5. **服务器容器**: ❌ 使用旧镜像

### 镜像流转路径

```
本地开发代码 (git push)
    ↓
GitHub test分支
    ↓
GitHub Actions 自动构建
    ↓
Docker Hub (hav93/tmc:test)
    ↓
服务器 (docker pull)
    ↓
服务器容器 (使用旧镜像❌)
```

## 🔍 诊断步骤

### 步骤1：检查GitHub Actions构建历史

访问: https://github.com/Hav93/TMC/actions

查看最近的构建记录：
- ✅ 是否成功完成？
- ✅ 构建时间是否是今天？
- ✅ 是否推送到Docker Hub？

### 步骤2：检查Docker Hub镜像

访问: https://hub.docker.com/r/hav93/tmc/tags

查看`test`标签：
- 最后更新时间
- 镜像digest
- 大小

### 步骤3：对比Git提交和镜像

```bash
# 查看最新提交
git log --oneline -5

# 应该看到
# ab07dab fix(middleware): Allow OPTIONS requests to pass through auth
# 9b87968 fix(cors): Allow all origins to fix proxy test and API access from LAN
```

如果Docker Hub的`test`镜像**早于这些提交**，说明GitHub Actions没有自动构建。

## 🐛 可能的问题

### 问题1：GitHub Actions未触发

**原因**：
- push到test分支后，GitHub Actions可能构建失败
- 或者构建成功但没有推送到Docker Hub

**检查**：
```yaml
# .github/workflows/docker-build.yml (第71行)
push: ${{ github.event_name != 'pull_request' }}
```

这个配置是正确的，push到test分支应该会触发构建。

### 问题2：Docker Hub credentials问题

**症状**：
- GitHub Actions构建成功
- 但推送Docker Hub失败

**检查**：GitHub仓库的Secrets是否设置：
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### 问题3：服务器使用了缓存镜像

**症状**：
- Docker Hub镜像是最新的
- 但服务器pull后还是旧的

**原因**：Docker镜像层缓存

**解决**：
```bash
# 在服务器上
docker rmi hav93/tmc:test  # 删除旧镜像
docker pull hav93/tmc:test  # 重新拉取
docker-compose up -d
```

## ✅ 解决方案

### 方案A：等待GitHub Actions自动构建（推荐）

如果您刚才的`git push`已经触发了构建：

1. 等待构建完成（约5-10分钟）
2. 在服务器上：
   ```bash
   docker pull hav93/tmc:test
   docker-compose up -d
   ```

### 方案B：手动触发GitHub Actions

1. 访问: https://github.com/Hav93/TMC/actions
2. 选择"Build and Push Docker Image"工作流
3. 点击"Run workflow" → 选择`test`分支 → "Run workflow"

### 方案C：服务器本地构建（快速但不推荐）

```bash
# 在服务器上
cd /path/to/TMC
git pull origin test
docker-compose build --no-cache  # 本地构建
docker-compose up -d
```

**缺点**：
- 每次更新都要在服务器上构建
- 消耗服务器资源
- 构建时间长

### 方案D：修改docker-compose使用本地构建（仅测试）

编辑`docker-compose.yml`：

```yaml
services:
  tmc:
    # image: hav93/tmc:${DOCKER_TAG:-test}  # 注释掉
    build:  # 改为本地构建
      context: .
      dockerfile: Dockerfile
```

## 🔧 验证修复

### 在服务器上执行

```bash
# 1. 检查当前镜像信息
docker images | grep tmc

# 2. 检查容器内middleware.py
docker exec your-container head -45 /app/middleware.py | grep -A 3 "OPTIONS"

# 应该看到:
# if request.method == "OPTIONS":
#     return await call_next(request)

# 3. 测试代理连接
# 访问 http://your-server:9393/settings
# 点击"测试连接"
# 应该不再出现 "Failed to fetch"
```

## 📝 最佳实践

### 开发流程

```
1. 本地开发和测试
   └─ 使用 local-dev/docker-compose.local.yml
   
2. 提交代码
   └─ git push origin test
   
3. 等待GitHub Actions构建
   └─ 约5-10分钟
   
4. 服务器部署
   └─ docker pull hav93/tmc:test
   └─ docker-compose up -d
```

### 快速验证新代码

如果不想等GitHub Actions构建，可以：

```bash
# 方法1：临时使用本地镜像
docker build -t hav93/tmc:test-local .
docker run -d hav93/tmc:test-local

# 方法2：直接在服务器构建
cd /path/to/TMC
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## 🎯 当前建议

基于您的情况，我建议：

### 立即解决（服务器上）：

```bash
# 方案1：如果GitHub Actions已完成构建
docker pull hav93/tmc:test
docker-compose down
docker-compose up -d

# 方案2：如果GitHub Actions还在构建或失败
cd /path/to/TMC
git pull origin test
docker-compose build --no-cache
docker-compose up -d
```

### 长期方案：

1. **检查GitHub Actions**：
   - 确认构建成功
   - 确认Secrets已设置

2. **标准化流程**：
   - 开发 → 提交 → GitHub Actions构建 → 服务器pull

3. **监控**：
   - 设置GitHub Actions失败通知
   - 定期检查Docker Hub镜像更新时间

---

**相关文件**：
- `.github/workflows/docker-build.yml` - GitHub Actions配置
- `docker-compose.yml` - 生产环境配置
- `local-dev/docker-compose.local.yml` - 本地开发配置
- `Dockerfile` - Docker镜像构建配置

