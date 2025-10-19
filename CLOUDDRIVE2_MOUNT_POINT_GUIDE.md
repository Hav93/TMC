# CloudDrive2 挂载点配置指南

## 问题说明

您遇到的错误：
```
挂载点不可用: 挂载点不存在
```

**原因：** 挂载点路径 `/115open/测试` 在 TMC 容器中不存在。

## CloudDrive2 的两种部署架构

### 架构 1：本地共享挂载（推荐）✅

CloudDrive2 和 TMC 运行在**同一台服务器上**，共享挂载目录。

```
[服务器物理机]
     ↓
[CloudDrive2 Container]  [TMC Container]
     ↓                        ↓
 挂载115网盘到              访问共享目录
 /CloudNAS/115         读取 /CloudNAS/115
     ↓_____________________↓
            [共享挂载目录]
```

**docker-compose.yml 配置：**

```yaml
version: '3.8'

services:
  # CloudDrive2 服务
  clouddrive2:
    image: clouddriveapi/clouddrive2
    container_name: clouddrive2
    restart: unless-stopped
    ports:
      - "19798:19798"  # API端口
      - "9798:9798"    # Web管理界面
    volumes:
      - ./clouddrive2/config:/Config       # CloudDrive2配置
      - /mnt/clouddrive:/CloudNAS          # 挂载点目录（主机路径）
      - ./clouddrive2/data:/CloudNAS:shared # 或使用命名卷
    environment:
      - TZ=Asia/Shanghai

  # TMC 服务
  tmc:
    build: .
    container_name: tmc-backend
    restart: unless-stopped
    ports:
      - "9393:8000"
    volumes:
      - ./config:/app/config
      - ./media:/app/media
      - /mnt/clouddrive:/CloudNAS          # 共享同一个挂载点
    environment:
      - CLOUDDRIVE2_ENABLED=true
      - CLOUDDRIVE2_HOST=clouddrive2       # 容器名
      - CLOUDDRIVE2_PORT=19798
      - CLOUDDRIVE2_USERNAME=your_email
      - CLOUDDRIVE2_PASSWORD=your_password
      - CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115  # 容器内的挂载路径
```

**TMC 设置界面配置：**
```
启用CloudDrive2: ✅
主机地址: clouddrive2 (或容器IP)
端口: 19798
用户名: your_email
密码: your_password
挂载点路径: /CloudNAS/115  ← 关键！必须是容器内能访问的路径
```

**验证步骤：**

1. **检查 TMC 容器内是否能访问挂载点**
   ```bash
   docker exec -it tmc-backend ls -la /CloudNAS/115
   ```
   
   应该能看到 115 网盘的文件。

2. **测试写入权限**
   ```bash
   docker exec -it tmc-backend touch /CloudNAS/115/test.txt
   docker exec -it tmc-backend rm /CloudNAS/115/test.txt
   ```

3. **测试上传**
   在 TMC 中触发媒体上传，应该成功。

---

### 架构 2：远程 CloudDrive2（需要额外实现）⚠️

CloudDrive2 和 TMC 运行在**不同的服务器上**。

```
[服务器 A - CloudDrive2]          [服务器 B - TMC]
     ↓                                 ↓
CloudDrive2 服务             通过 gRPC API
挂载 /115open/测试      →    上传文件（不能直接访问挂载点）
```

**当前状态：** ❌ 此架构**暂不支持**

**原因：** 当前实现使用的是 **文件复制** 方式（将文件复制到挂载目录），无法跨服务器工作。

**需要实现：**
- 通过 CloudDrive2 gRPC API 的 `Upload` 方法上传文件
- 需要读取文件内容，通过网络传输到 CloudDrive2
- 参考官方文档：https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html

---

## 当前解决方案

### 方案 A：修改为本地共享挂载（推荐）✅

1. **修改 docker-compose.yml**
   
   添加共享挂载目录：
   ```yaml
   services:
     tmc:
       volumes:
         - /path/to/clouddrive/mount:/CloudNAS  # 与CloudDrive2共享
   ```

2. **重启 TMC**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **修改 TMC 配置**
   
   在 `config/app.config` 中：
   ```ini
   CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115
   ```
   
   或在 Web 界面中设置：
   ```
   挂载点路径: /CloudNAS/115
   ```

4. **验证**
   ```bash
   # 检查挂载点
   docker exec -it tmc-backend ls /CloudNAS/115
   
   # 应该能看到文件
   ```

### 方案 B：直接在 CloudDrive2 服务器上运行 TMC（最简单）✅

将 TMC 部署在与 CloudDrive2 相同的服务器上，使用方案 A 的配置。

### 方案 C：等待远程 gRPC 上传实现（开发中）⏳

如果必须使用远程 CloudDrive2，需要等待以下功能实现：

1. ✅ CloudDrive2 gRPC 连接 - 已实现
2. ✅ CloudDrive2 身份验证 - 已实现
3. ❌ CloudDrive2 文件上传 API - **待实现**
4. ❌ 流式传输大文件 - **待实现**

---

## 快速诊断

### 1. 确认您的部署架构

**问题：** CloudDrive2 和 TMC 在同一台服务器上吗？

- **是** → 使用方案 A（本地共享挂载）
- **否** → 暂时无法使用，需要等待方案 C 实现

### 2. 检查挂载点路径

**在 TMC 容器内执行：**
```bash
docker exec -it tmc-backend bash
ls -la /CloudNAS/115        # 检查默认路径
ls -la /115open/测试         # 检查您配置的路径
```

**期望结果：**
- ✅ 能看到目录和文件 → 路径正确
- ❌ `No such file or directory` → 路径不存在，需要修改配置

### 3. 检查 CloudDrive2 挂载配置

**打开 CloudDrive2 Web 界面：**
```
http://your-server:9798
```

**查看 115 网盘挂载信息：**
1. 进入：挂载管理
2. 找到：115网盘
3. 查看：挂载路径（如 `/CloudNAS/115`）
4. 确保：状态为"已挂载"

**在 TMC 中使用相同的路径！**

---

## 配置示例

### 示例 1：CloudDrive2 挂载到 `/CloudNAS/115`

**CloudDrive2 配置：**
- 115网盘挂载路径：`/CloudNAS/115`

**docker-compose.yml：**
```yaml
services:
  clouddrive2:
    volumes:
      - /mnt/clouddrive:/CloudNAS
  
  tmc:
    volumes:
      - /mnt/clouddrive:/CloudNAS  # 共享
```

**TMC 设置：**
```
挂载点路径: /CloudNAS/115
```

**监控规则设置：**
```
CloudDrive2 远程路径: (留空，使用全局默认)
```

**最终上传路径：**
```
/CloudNAS/115/Telegram媒体/2025/10/19/video_xxx.mp4
```

---

### 示例 2：CloudDrive2 挂载到 `/115`

**CloudDrive2 配置：**
- 115网盘挂载路径：`/115`

**docker-compose.yml：**
```yaml
services:
  clouddrive2:
    volumes:
      - /mnt/115:/115
  
  tmc:
    volumes:
      - /mnt/115:/115  # 共享
```

**TMC 设置：**
```
挂载点路径: /115
```

**监控规则设置：**
```
CloudDrive2 远程路径: /测试
```

**最终上传路径：**
```
/115/测试/2025/10/19/video_xxx.mp4
```

---

## 常见问题

### Q1: 我的 CloudDrive2 在另一台服务器上，怎么办？

**A:** 当前版本不支持远程 CloudDrive2。您可以：

1. **临时方案：** 将 TMC 部署到 CloudDrive2 所在服务器
2. **等待更新：** 关注项目更新，等待远程 gRPC 上传功能

### Q2: 挂载点路径应该填什么？

**A:** 填写 **TMC 容器内**能访问到的 CloudDrive2 挂载目录路径。

**验证方法：**
```bash
docker exec -it tmc-backend ls /your/mount/path
```

### Q3: 为什么之前能连接但上传失败？

**A:** 
- ✅ **连接成功** = CloudDrive2 gRPC 服务可以连接
- ❌ **上传失败** = 挂载点路径不存在或不可访问

这是两个独立的检查步骤。

### Q4: 监控规则中的"CloudDrive2 远程路径"和"挂载点路径"有什么区别？

**A:**

| 配置项 | 位置 | 含义 | 示例 |
|--------|------|------|------|
| 挂载点路径 | 系统设置 → CloudDrive2 | CloudDrive2 的挂载根目录 | `/CloudNAS/115` |
| CloudDrive2 远程路径 | 监控规则 | 相对于挂载点的子目录 | `/测试` |

**最终路径 = 挂载点路径 + 远程路径 + 组织规则生成的路径**

例如：
```
挂载点：/CloudNAS/115
规则路径：/测试
组织规则：/{year}/{month}/{day}
文件名：video_xxx.mp4

最终路径：/CloudNAS/115/测试/2025/10/19/video_xxx.mp4
```

---

## 总结

1. ✅ **推荐配置：** TMC 和 CloudDrive2 在同一台服务器，使用共享挂载
2. ⚠️ **关键步骤：** 确保 TMC 容器能访问 CloudDrive2 的挂载目录
3. 🔍 **验证方法：** `docker exec -it tmc-backend ls /your/mount/path`
4. ⏳ **远程支持：** 需要进一步开发，当前版本暂不支持

---

**最后更新：** 2025-10-19  
**相关文档：** CLOUDDRIVE2_IMPLEMENTATION_SUMMARY.md

