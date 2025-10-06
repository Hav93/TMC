# GitHub �?Docker Hub 自动构建设置指南

本文档介绍如何设�?GitHub Actions 自动构建并推送到 Docker Hub�?

---

## 📋 前置要求

1. GitHub 账号
2. Docker Hub 账号（用户名: `hav93`�?
3. 项目仓库已创�?

---

## 🔧 步骤 1: 配置 Docker Hub

### 1.1 创建 Access Token

1. 登录 Docker Hub: https://hub.docker.com
2. 点击右上角头�?�?**Account Settings**
3. 选择 **Security** �?**New Access Token**
4. 填写描述（例如：`GitHub Actions`�?
5. 选择权限�?*Read, Write, Delete**
6. 点击 **Generate** 生成 Token
7. **⚠️ 立即复制保存�?* Token 只显示一�?

### 1.2 创建仓库（可选）

1. 访问: https://hub.docker.com/repositories
2. 点击 **Create Repository**
3. 仓库�? `tmc`
4. 可见�? **Public**（推荐）�?Private
5. 描述: `Telegram Message Center - 强大的消息转发管理系统`

---

## 🔐 步骤 2: 配置 GitHub Secrets

### 2.1 添加 Docker Hub 凭证

1. 打开你的 GitHub 仓库
2. 进入 **Settings** �?**Secrets and variables** �?**Actions**
3. 点击 **New repository secret**
4. 添加以下两个密钥�?

**Secret 1:**
- Name: `DOCKER_USERNAME`
- Secret: `hav93`

**Secret 2:**
- Name: `DOCKER_PASSWORD`
- Secret: `<粘贴你的 Docker Hub Access Token>`

### 2.2 验证配置

确保�?**Actions secrets** 页面看到�?
- �?`DOCKER_USERNAME`
- �?`DOCKER_PASSWORD`

---

## 📤 步骤 3: 推送代码触发构�?

### 3.1 初始�?Git 仓库（如果还没有�?

```bash
cd C:\Users\16958\Desktop\TG-Message\TMC

# 初始�?Git
git init

# 添加远程仓库（替换为你的仓库地址�?
git remote add origin https://github.com/Hav93/tmc.git

# 添加所有文�?
git add .

# 提交
git commit -m "Initial commit: TMC v3.2.0"

# 推送到 GitHub
git push -u origin main
```

### 3.2 推送时自动构建

每次推送到 `main` �?`master` 分支时，GitHub Actions 会自动：
1. 构建 Docker 镜像（支�?amd64 �?arm64�?
2. 推送到 Docker Hub: `hav93/tmc:latest`
3. 更新 Docker Hub 的仓库描�?

---

## 🏷�?步骤 4: 发布版本

### 4.1 创建版本标签

```bash
# 创建版本标签
git tag -a v3.2.0 -m "Release v3.2.0"

# 推送标�?
git push origin v3.2.0
```

### 4.2 自动生成的镜像标�?

推送标签后，会自动生成多个 Docker 镜像标签�?
- `hav93/tmc:latest`
- `hav93/tmc:3.2.0`
- `hav93/tmc:3.2`
- `hav93/tmc:3`
- `hav93/tmc:main`

---

## 🔍 步骤 5: 验证构建

### 5.1 查看 GitHub Actions

1. 进入仓库�?**Actions** 标签
2. 查看 **Build and Push Docker Image** 工作�?
3. 点击最新的运行记录查看详细日志

### 5.2 验证 Docker Hub

1. 访问: https://hub.docker.com/r/hav93/tmc
2. 检�?**Tags** 标签页，确认镜像已推�?
3. 检�?**Overview** 是否显示 README 内容

### 5.3 本地测试镜像

```bash
# 拉取镜像
docker pull hav93/tmc:latest

# 运行测试
docker run --rm -p 9393:9393 \
  -e API_ID=your_id \
  -e API_HASH=your_hash \
  -e BOT_TOKEN=your_token \
  hav93/tmc:latest
```

---

## 🚀 步骤 6: 用户使用

用户现在可以使用以下命令部署�?

```bash
# 1. 创建目录
mkdir tmc && cd tmc

# 2. 下载 docker-compose.yml
curl -O https://raw.githubusercontent.com/Hav93/tmc/main/docker-compose.user.yml
mv docker-compose.user.yml docker-compose.yml

# 3. 创建 .env 文件
curl -O https://raw.githubusercontent.com/Hav93/tmc/main/.env.user.example
mv .env.user.example .env

# 4. 编辑 .env 文件，填入配�?

# 5. 启动服务
docker compose up -d
```

---

## 📊 GitHub Actions 工作流说�?

### 触发条件

自动构建在以下情况触发：
- 推送到 `main` �?`master` 分支
- 推送版本标签（`v*`�?
- 提交 Pull Request（仅构建，不推送）

### 构建特�?

- �?多架构支持：`linux/amd64`, `linux/arm64`
- �?Docker 缓存加速构�?
- �?自动生成镜像标签
- �?自动更新 Docker Hub 描述
- �?构建元数据（版本、日期、Git SHA�?

### 构建时间

- 首次构建：约 10-15 分钟
- 增量构建：约 5-8 分钟（有缓存�?

---

## 🐛 故障排查

### 构建失败

1. **检�?Secrets**：确�?`DOCKER_USERNAME` �?`DOCKER_PASSWORD` 正确
2. **查看日志**：在 Actions 页面查看详细错误信息
3. **Token 权限**：确�?Docker Hub Token �?Write 权限

### 推送失�?

1. **仓库不存�?*：先�?Docker Hub 创建 `hav93/tmc` 仓库
2. **权限问题**：确�?Token 有推送权�?
3. **镜像名称**：确�?`.github/workflows/docker-build.yml` 中的镜像名正�?

### 本地测试工作�?

```bash
# 安装 act（本地运�?GitHub Actions�?
# Windows (Chocolatey)
choco install act-cli

# 运行工作�?
act -s DOCKER_USERNAME=hav93 -s DOCKER_PASSWORD=your_token
```

---

## 📝 维护建议

### 定期更新

```bash
# 1. 更新代码
git add .
git commit -m "Update: xxx"
git push

# 2. 发布新版�?
git tag -a v3.3.0 -m "Release v3.3.0"
git push origin v3.3.0
```

### 管理旧镜�?

定期清理 Docker Hub 上的旧标签：
1. 进入 Docker Hub 仓库
2. 选择 **Tags** 标签�?
3. 删除不需要的旧版本标�?

---

## 🔗 相关链接

- **GitHub Actions 文档**: https://docs.github.com/en/actions
- **Docker Hub 文档**: https://docs.docker.com/docker-hub/
- **多架构构�?*: https://docs.docker.com/build/building/multi-platform/

---

## �?检查清�?

部署前确认：

- [ ] Docker Hub 账号已创�?
- [ ] Docker Hub Access Token 已生成并保存
- [ ] GitHub 仓库已创�?
- [ ] GitHub Secrets 已配置（`DOCKER_USERNAME`, `DOCKER_PASSWORD`�?
- [ ] 代码已推送到 GitHub
- [ ] GitHub Actions 工作流运行成�?
- [ ] Docker Hub 镜像已生�?
- [ ] 本地测试镜像可用
- [ ] 用户部署文档已准备（`DEPLOYMENT.md`�?

---

**准备时间**: �?15-20 分钟  
**首次构建**: �?10-15 分钟  
**总耗时**: �?30 分钟

**最后更�?*: 2025-10-06

