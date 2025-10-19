# CloudDrive2 上传问题解决方案

## 当前问题

1. ✅ **认证成功**：JWT token 获取成功
2. ✅ **挂载点发现**：找到 `/CloudNAS/115`
3. ❌ **远程上传协议不可用**：`StatusCode.UNIMPLEMENTED`

## 根本原因

您的 CloudDrive2 版本不支持 `StartRemoteUpload` (远程上传协议)

## 解决方案

### 方案 A：使用本地挂载（推荐，最简单）

您需要让 TMC 容器能访问 CloudDrive2 的挂载点。

#### 1. 检查 CloudDrive2 的挂载配置

在 CloudDrive2 服务器上：
```bash
# 检查挂载点
mount | grep CloudNAS
# 或
df -h | grep CloudNAS
```

应该看到类似：
```
/CloudNAS/115 -> 挂载到某个目录
```

#### 2. 配置 Docker Volume 共享

**如果 CloudDrive2 和 TMC 在同一台机器**：

修改 `docker-compose.yml`：
```yaml
services:
  tmc:
    volumes:
      # ... 其他挂载
      - /CloudNAS:/CloudNAS  # 共享 CloudDrive2 挂载点
```

然后：
```bash
docker-compose down
docker-compose up -d
```

#### 3. 更新 CloudDrive2 配置

在 TMC 设置页面，CloudDrive2 配置中：
- **挂载点路径**：`/CloudNAS/115`（而不是 `/115open/测试`）

或者，在监控规则中：
- **CloudDrive2 远程路径**：`/CloudNAS/115/测试`

### 方案 B：使用 WebDAV（如果不能共享挂载）

CloudDrive2 支持 WebDAV，我们可以通过 WebDAV 上传文件。

需要修改代码以支持 WebDAV 上传。

### 方案 C：使用 WriteToFile API

使用 CloudDrive2 的 `WriteToFile` 或 `WriteToFileStream` gRPC 方法上传文件。

需要修改代码实现这个 API。

## 推荐操作步骤

### 立即可用：方案 A

1. **在服务器上配置 Docker 卷共享**

编辑 `docker-compose.yml`（在服务器上）：
```yaml
volumes:
  - /CloudNAS:/CloudNAS:ro  # 只读挂载，更安全
```

2. **重启容器**
```bash
docker-compose down
docker-compose up -d
```

3. **更新配置**

在 TMC 设置 -> CloudDrive2：
- 挂载点路径：`/CloudNAS/115`

在监控规则中：
- CloudDrive2 远程路径：`/CloudNAS/115/测试` 或 `/CloudNAS/115/测试/2025/10/19`

4. **测试上传**

应该会走本地文件复制路径：
```
🔧 使用方案1: 本地挂载上传
📂 目标路径: /CloudNAS/115/测试/2025/10/19/video_63087.mp4
```

### 长期方案：支持 WriteToFile API

如果无法共享挂载点（比如 CloudDrive2 在另一台机器），我需要实现 `WriteToFile` API。

## 检查清单

- [ ] 确认 CloudDrive2 的实际挂载点路径（`/CloudNAS/115`）
- [ ] 配置 Docker volume 共享
- [ ] 更新 TMC 中的挂载点配置
- [ ] 测试文件上传
- [ ] 确认文件出现在 115 网盘中

## 技术细节

### 为什么远程上传协议不可用？

`StartRemoteUpload` 是 CloudDrive2 的新特性，可能：
1. 您的 CloudDrive2 版本较旧
2. 该功能需要特定配置启用
3. 该功能仍在开发中

### 本地挂载上传的优势

1. ✅ **最快**：直接文件系统操作
2. ✅ **最稳定**：无需网络传输
3. ✅ **最简单**：已经实现好了
4. ✅ **支持秒传**：CloudDrive2 会自动处理

---

**现在请按照"方案 A"配置 Docker 卷共享！**

