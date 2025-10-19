# CloudDrive2 配置指南

## 📋 概述

CloudDrive2 是一个专业的云存储挂载工具，可以解决115网盘上传签名问题，支持大文件和断点续传功能。

## 🎯 为什么使用 CloudDrive2？

1. **解决上传签名问题**：115网盘的上传需要复杂的加密签名，CloudDrive2已经处理好这些
2. **支持大文件上传**：可以稳定上传超大文件
3. **断点续传**：上传中断后可以继续，不用重新开始
4. **稳定可靠**：相比自己实现上传协议更加稳定

## 📦 安装 CloudDrive2

### 方法一：Docker 部署（推荐）

```bash
docker run -d \
  --name clouddrive2 \
  -p 19798:19798 \
  -v /path/to/config:/config \
  -v /path/to/data:/data \
  --restart unless-stopped \
  cloudnas/clouddrive2:latest
```

### 方法二：直接安装

1. 访问 [CloudDrive2 官网](https://www.clouddrive2.com/)
2. 下载对应系统的安装包
3. 按照官方文档完成安装

## ⚙️ 配置 CloudDrive2

### 1. 添加115网盘账号

1. 打开 CloudDrive2 Web界面（默认：http://localhost:19798）
2. 点击"添加云盘"
3. 选择"115网盘"
4. 输入115账号的 Cookie 信息
5. 设置挂载点路径（如：`/CloudNAS/115`）

### 2. 启用 gRPC API

1. 在 CloudDrive2 设置中找到"API设置"
2. 启用 gRPC API
3. 设置端口（默认：19798）
4. （可选）设置用户名和密码以增强安全性

### 3. 在 TMC 中配置

#### 方式一：通过 Web 界面配置（推荐）

1. 访问 TMC Web 界面
2. 进入 **设置 → CloudDrive2** 标签页
3. 填写以下信息：
   - **启用CloudDrive2上传**：开启
   - **主机地址**：CloudDrive2 服务地址（如：`localhost` 或 `192.168.1.100`）
   - **端口**：gRPC 端口（默认：`19798`）
   - **用户名**：（可选）如果启用了认证
   - **密码**：（可选）如果启用了认证
   - **挂载点路径**：115网盘在CloudDrive2中的挂载路径（如：`/CloudNAS/115`）
4. 点击"测试连接"验证配置
5. 点击"保存配置"

#### 方式二：通过环境变量配置

编辑 `env.example` 或 `.env` 文件：

```bash
# ==================== CloudDrive2 配置 ====================
# 启用 CloudDrive2 上传
CLOUDDRIVE2_ENABLED=true

# CloudDrive2 服务地址
CLOUDDRIVE2_HOST=localhost

# CloudDrive2 服务端口
CLOUDDRIVE2_PORT=19798

# CloudDrive2 用户名（如果启用了认证）
CLOUDDRIVE2_USERNAME=admin

# CloudDrive2 密码（如果启用了认证）
CLOUDDRIVE2_PASSWORD=

# 115 网盘挂载点路径
CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115
```

## 🧪 测试配置

### 方法一：Web 界面测试

1. 在 **设置 → CloudDrive2** 页面
2. 点击"测试连接"按钮
3. 查看测试结果

### 方法二：手动测试上传

1. 在媒体监控中设置一个规则
2. 配置上传到115网盘
3. 触发一次上传任务
4. 观察日志输出

## 📝 使用场景

### 场景1：Docker Compose 部署（同一网络）

```yaml
version: '3.8'

services:
  tmc:
    image: your-tmc-image:latest
    environment:
      - CLOUDDRIVE2_ENABLED=true
      - CLOUDDRIVE2_HOST=clouddrive2
      - CLOUDDRIVE2_PORT=19798
      - CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115
    depends_on:
      - clouddrive2
    networks:
      - tmc-network

  clouddrive2:
    image: cloudnas/clouddrive2:latest
    ports:
      - "19798:19798"
    volumes:
      - ./clouddrive2/config:/config
      - ./clouddrive2/data:/data
    networks:
      - tmc-network

networks:
  tmc-network:
    driver: bridge
```

### 场景2：独立部署（不同主机）

如果 CloudDrive2 部署在其他主机：

```bash
CLOUDDRIVE2_HOST=192.168.1.100  # CloudDrive2 所在主机的 IP
CLOUDDRIVE2_PORT=19798
```

### 场景3：Windows 本地开发

如果在 Windows 上运行 CloudDrive2：

```bash
CLOUDDRIVE2_HOST=host.docker.internal  # Docker 访问宿主机
CLOUDDRIVE2_PORT=19798
CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115
```

## 🔧 故障排查

### 问题1：连接测试失败

**可能原因：**
- CloudDrive2 服务未启动
- 端口配置错误
- 防火墙阻止连接
- gRPC API 未启用

**解决方法：**
1. 确认 CloudDrive2 服务正在运行
2. 检查端口是否正确（默认19798）
3. 检查防火墙规则
4. 确认 gRPC API 已在 CloudDrive2 中启用

### 问题2：上传失败

**可能原因：**
- 挂载点路径错误
- 115账号未登录或Cookie过期
- 目标目录不存在

**解决方法：**
1. 确认挂载点路径与 CloudDrive2 中配置的一致
2. 在 CloudDrive2 中重新登录115账号
3. 检查目标目录是否存在

### 问题3：grpcio 模块未安装

**错误信息：**
```
❌ CloudDrive2模块未安装
请先安装 grpcio 和 grpcio-tools
```

**解决方法：**
```bash
# 在项目的 backend 目录下
pip install grpcio grpcio-tools
```

或者在 `requirements.txt` 中添加：
```
grpcio>=1.60.0
grpcio-tools>=1.60.0
```

## 📊 上传进度监控

TMC 集成了完整的上传进度监控：

1. **实时进度**：在媒体文件管理页面查看上传进度
2. **断点续传**：上传中断后自动恢复
3. **日志记录**：详细的上传日志便于排查问题

## 🔐 安全建议

1. **启用认证**：在 CloudDrive2 中启用 gRPC 认证
2. **内网部署**：建议在内网环境中使用
3. **定期更新**：保持 CloudDrive2 版本更新
4. **限制访问**：使用防火墙限制访问端口

## 📚 相关文档

- [CloudDrive2 官方文档](https://www.clouddrive2.com/docs/)
- [CloudDrive2 gRPC API 指南](https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html)
- [TMC 上传功能说明](./CLOUDDRIVE2_UPLOAD_GUIDE.md)
- [TMC 实现总结](./CLOUDDRIVE2_IMPLEMENTATION_SUMMARY.md)

## ❓ 常见问题

**Q: 必须使用 CloudDrive2 吗？**
A: 是的，目前 TMC 的115网盘上传功能依赖 CloudDrive2。直接实现115的上传协议非常复杂且不稳定。

**Q: CloudDrive2 收费吗？**
A: CloudDrive2 有免费版和付费版，免费版功能已足够使用。

**Q: 可以同时挂载多个云盘吗？**
A: CloudDrive2 支持挂载多个云盘，但 TMC 目前只支持115网盘。

**Q: 上传速度如何？**
A: 取决于网络环境和115账号类型。VIP账号上传速度更快。

**Q: 支持大文件上传吗？**
A: 是的，CloudDrive2 支持任意大小的文件上传，且有断点续传功能。

---

最后更新：2025-10-19

