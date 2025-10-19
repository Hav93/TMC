# CloudDrive2 直接挂载解决方案

## 问题分析

当前问题的根本原因：
1. `StartRemoteUpload` gRPC API 返回 `UNIMPLEMENTED` - 说明你的 CloudDrive2 版本不支持此新协议
2. `WriteToFile` API 需要 `fileHandle`，这需要正确的文件系统路径
3. TMC 容器和 CloudDrive2 容器是分离的，无法直接访问挂载点

## 最佳解决方案：共享 CloudDrive2 挂载卷

### 方案 A：Docker Compose 共享卷（推荐）

如果 CloudDrive2 也是 Docker 部署，修改 `docker-compose.yml`：

```yaml
services:
  tmc:
    volumes:
      # 添加 CloudDrive2 的挂载点
      - clouddrive2_mount:/CloudNAS:ro  # 只读挂载，安全
    
  clouddrive2:  # 如果没有，需要添加
    image: cloudnas/clouddrive2:latest
    volumes:
      - clouddrive2_mount:/CloudNAS
    # ... 其他配置

volumes:
  clouddrive2_mount:
    external: true  # 或者让 CloudDrive2 创建
```

### 方案 B：直接挂载宿主机目录

如果 CloudDrive2 在宿主机上运行，并挂载到 `/mnt/CloudNAS/115`：

```yaml
services:
  tmc:
    volumes:
      - /mnt/CloudNAS:/CloudNAS:ro  # 挂载宿主机的 CloudDrive2 目录
```

### 方案 C：使用 CloudDrive2 的 WebDAV（如果支持）

CloudDrive2 可能提供 WebDAV 接口，我们可以通过 HTTP 上传：

```python
import requests
from requests.auth import HTTPBasicAuth

def upload_via_webdav(local_file, remote_path, webdav_url, username, password):
    with open(local_file, 'rb') as f:
        response = requests.put(
            f"{webdav_url}{remote_path}",
            data=f,
            auth=HTTPBasicAuth(username, password)
        )
    return response.status_code == 201
```

## 实施步骤

### 第一步：确认 CloudDrive2 部署方式

请提供以下信息：

1. CloudDrive2 是如何部署的？
   - [ ] Docker 容器
   - [ ] 直接安装在宿主机
   - [ ] 其他方式

2. CloudDrive2 的挂载点在哪里？
   - 容器内路径：`/CloudNAS/115`
   - 宿主机路径：`?`

3. CloudDrive2 是否开启了 WebDAV？
   - 端口：`?`
   - 认证方式：`?`

### 第二步：选择最适合的方案

根据部署方式选择：
- **Docker 部署** → 方案 A（共享卷）
- **宿主机部署** → 方案 B（直接挂载）
- **都不方便** → 方案 C（WebDAV）

### 第三步：实施

提供具体信息后，我将帮你实施最优方案。

## 为什么这些方案更好？

1. **简单可靠**：直接文件复制，不依赖复杂的 gRPC 协议
2. **高性能**：本地文件系统操作，速度快
3. **兼容性好**：不受 CloudDrive2 版本限制
4. **易于调试**：出问题容易排查

## 临时workaround

如果以上方案都不可行，还有最后一个选择：
- 使用 CloudDrive2 的 Web 界面的上传接口（通过 HTTP POST 模拟）
- 这需要抓包分析 CloudDrive2 Web UI 的上传请求

请告诉我你的 CloudDrive2 部署情况，我们立即实施最佳方案！

