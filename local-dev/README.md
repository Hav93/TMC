# TMC 本地开发工具

这个文件夹包含了本地开发所需的所有配置和脚本，让你不用每次都记住复杂的命令。

## 📁 文件说明

- **`docker-compose.local.yml`** - 本地开发专用的 Docker Compose 配置
- **`build-local.ps1`** - 交互式构建脚本（推荐）
- **`build-quick.ps1`** - 快速构建脚本（使用缓存）
- **`build-clean.ps1`** - 完全重新构建脚本（不使用缓存）
- **`env.example`** - 环境变量示例文件

## 🚀 快速开始

### 1. 配置环境变量

```powershell
# 复制环境变量示例文件
cd local-dev
Copy-Item env.example ..\.env
# 编辑 .env 文件，填写您的配置
notepad ..\.env
```

### 2. 选择构建方式

#### 方式一：交互式菜单（推荐）
```powershell
.\local-dev\build-local.ps1
```

**功能菜单：**
1. 快速构建并启动 (使用缓存) - 日常开发用
2. 完全重新构建 (不使用缓存) - 修改了依赖或遇到问题时用
3. 仅启动容器
4. 停止容器
5. 查看日志
6. 进入容器Shell
7. 清理所有容器和镜像
0. 退出

#### 方式二：快速构建（推荐日常使用）
```powershell
.\local-dev\build-quick.ps1
```

#### 方式三：完全重新构建（修复问题时使用）
```powershell
.\local-dev\build-clean.ps1
```

## 📝 常用命令

### 查看容器状态
```powershell
docker compose -f local-dev/docker-compose.local.yml ps
```

### 查看日志
```powershell
# 实时查看日志
docker compose -f local-dev/docker-compose.local.yml logs -f tmc

# 查看最近100行日志
docker compose -f local-dev/docker-compose.local.yml logs --tail=100 tmc
```

### 进入容器
```powershell
docker compose -f local-dev/docker-compose.local.yml exec tmc /bin/bash
```

### 停止容器
```powershell
docker compose -f local-dev/docker-compose.local.yml down
```

### 重启容器
```powershell
docker compose -f local-dev/docker-compose.local.yml restart
```

## ⚙️ 自定义代理

如果你的代理地址不是 `192.168.31.6:7890`，可以：

### 方式一：修改 env.example
```env
LOCAL_PROXY_HOST=your_proxy_ip:port
```

### 方式二：临时设置环境变量
```powershell
$env:LOCAL_PROXY_HOST = "10.0.0.1:8080"
.\local-dev\build-quick.ps1
```

## 🔧 故障排查

### 构建失败？
1. 检查代理是否正常工作
2. 尝试使用 `build-clean.ps1` 完全重新构建
3. 检查 Docker Desktop 是否正常运行

### 容器启动失败？
1. 查看日志：`docker compose -f local-dev/docker-compose.local.yml logs tmc`
2. 检查 `.env` 文件配置是否正确
3. 确认端口 9393 没有被占用

### 代理问题？
1. 确认代理服务正在运行
2. 检查代理地址和端口是否正确
3. 尝试在浏览器中测试代理

## 📊 访问应用

构建完成后，访问：

- **前端界面**: http://localhost:9393
- **API文档**: http://localhost:9393/docs
- **健康检查**: http://localhost:9393/health

## 💡 提示

- 日常开发推荐使用 `build-quick.ps1`（快，使用缓存）
- 修改了 `requirements.txt` 或 `package.json` 后，使用 `build-clean.ps1`
- 遇到奇怪问题时，先尝试 `build-clean.ps1` 完全重新构建
- 所有脚本都会自动配置代理，不用手动设置

