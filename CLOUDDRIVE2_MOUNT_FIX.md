# CloudDrive2 挂载点问题快速修复指南

## 🚨 您遇到的错误

```
挂载点不可用: 挂载点不存在
```

## ✅ 快速解决方案（推荐）

### 方案 A：使用本地共享挂载

这是**最简单、最可靠**的方案。

#### 1. 检查 CloudDrive2 的挂载配置

登录到 CloudDrive2 Web 管理界面（通常是 `http://your-server:9798`）：

1. 查看 **挂载点管理**
2. 找到 **115 网盘**
3. 记下 **挂载路径**（例如：`/CloudNAS/115`）

#### 2. 修改 docker-compose.yml

编辑您的 `docker-compose.yml`，添加共享卷：

```yaml
version: '3.8'

services:
  # CloudDrive2（如果已经运行，跳过此配置）
  clouddrive2:
    image: clouddriveapi/clouddrive2
    container_name: clouddrive2
    ports:
      - "19798:19798"
      - "9798:9798"
    volumes:
      - /mnt/clouddrive:/CloudNAS  # 主机挂载目录
    restart: unless-stopped

  # TMC
  tmc:
    build: .
    container_name: tmc-backend
    ports:
      - "9393:8000"
    volumes:
      - ./config:/app/config
      - ./media:/app/media
      - /mnt/clouddrive:/CloudNAS  # 共享相同的挂载目录 ← 关键！
    environment:
      - CLOUDDRIVE2_ENABLED=true
      - CLOUDDRIVE2_HOST=clouddrive2
      - CLOUDDRIVE2_PORT=19798
      - CLOUDDRIVE2_MOUNT_POINT=/CloudNAS/115  # 容器内路径
    restart: unless-stopped
```

**关键点：**
- CloudDrive2 和 TMC 必须挂载**相同的主机目录**（`/mnt/clouddrive`）
- 这样 TMC 就能直接访问 CloudDrive2 的挂载点

#### 3. 重启服务

```bash
cd /path/to/TMC
docker-compose down
docker-compose up -d
```

#### 4. 验证挂载点

```bash
# 检查 TMC 容器是否能访问挂载点
docker exec -it tmc-backend ls -la /CloudNAS/115

# 应该能看到 115 网盘的文件和目录
```

#### 5. 更新 TMC 配置

在 TMC Web 界面中：

```
系统设置 → CloudDrive2 → 挂载点路径: /CloudNAS/115
```

或者在监控规则中留空，使用全局默认路径。

#### 6. 测试上传

发送一个测试文件到 Telegram，检查是否能成功上传到 115 网盘。

---

## 🔧 您的当前配置问题

根据您的日志：

```
挂载点路径: /115open/测试
```

**问题分析：**

1. `/115open/测试` 是 CloudDrive2 **服务器上**的路径
2. TMC 容器**看不到**这个路径（除非通过共享挂载）
3. 当前 TMC 尝试直接访问 `/115open/测试`，但容器内不存在这个目录

**解决方法：**

### 选项 1：修改挂载点路径（推荐）

将挂载点路径改为 TMC 容器内**实际可以访问**的路径。

**步骤：**

1. **在 CloudDrive2 中创建/确认挂载点：**
   ```
   挂载名称: 115
   挂载路径: /CloudNAS/115
   云盘类型: 115
   ```

2. **在 docker-compose.yml 中添加共享卷：**
   ```yaml
   tmc:
     volumes:
       - /mnt/clouddrive:/CloudNAS
   ```

3. **在 TMC 设置中修改：**
   ```
   挂载点路径: /CloudNAS/115
   ```

4. **在监控规则中设置：**
   ```
   CloudDrive2 远程路径: /测试  （或留空）
   ```

**最终效果：**
```
文件上传到: /CloudNAS/115/测试/2025/10/19/video_xxx.mp4
```

### 选项 2：调整 docker-compose.yml 挂载

如果您坚持使用 `/115open/测试` 这个路径：

```yaml
tmc:
  volumes:
    - /actual/host/path:/115open  # 将主机路径挂载到 /115open
```

然后：
```
挂载点路径: /115open/测试
```

但这样不如方案 A 清晰。

---

## 📋 完整配置示例

### 示例 1：标准配置

**CloudDrive2 配置：**
- 挂载路径：`/CloudNAS/115`

**docker-compose.yml：**
```yaml
services:
  clouddrive2:
    volumes:
      - /mnt/clouddrive:/CloudNAS
  
  tmc:
    volumes:
      - ./config:/app/config
      - ./media:/app/media
      - /mnt/clouddrive:/CloudNAS  # 共享
```

**TMC 设置：**
```
挂载点路径: /CloudNAS/115
```

**监控规则：**
```
CloudDrive2 远程路径: (留空，使用默认)
```

**上传路径：**
```
/CloudNAS/115/Telegram媒体/2025/10/19/video_xxx.mp4
```

---

### 示例 2：自定义子目录

**CloudDrive2 配置：**
- 挂载路径：`/CloudNAS/115`

**TMC 设置：**
```
挂载点路径: /CloudNAS/115
```

**监控规则：**
```
CloudDrive2 远程路径: /测试
```

**上传路径：**
```
/CloudNAS/115/测试/2025/10/19/video_xxx.mp4
```

---

## 🔍 诊断命令

### 1. 检查 CloudDrive2 挂载点

```bash
# 进入 CloudDrive2 容器
docker exec -it clouddrive2 sh

# 查看挂载点内容
ls -la /CloudNAS/115

# 退出
exit
```

### 2. 检查 TMC 容器挂载

```bash
# 进入 TMC 容器
docker exec -it tmc-backend bash

# 检查挂载点是否存在
ls -la /CloudNAS/115

# 如果不存在，说明 volumes 没配置好
# 如果存在，检查是否可写
touch /CloudNAS/115/test.txt
rm /CloudNAS/115/test.txt

# 退出
exit
```

### 3. 查看 TMC 日志

```bash
docker logs tmc-backend --tail 50 -f
```

### 4. 验证配置

```bash
# 检查环境变量
docker exec -it tmc-backend printenv | grep CLOUDDRIVE2

# 检查配置文件
docker exec -it tmc-backend cat /app/config/app.config | grep CLOUDDRIVE2
```

---

## ⚠️ 常见错误

### 错误 1：挂载点不存在

```
挂载点不可用: 挂载点不存在
```

**原因：** TMC 容器内看不到挂载点路径

**解决：** 
1. 检查 `docker-compose.yml` 中的 `volumes` 配置
2. 确保 TMC 和 CloudDrive2 共享同一个目录
3. 重启服务：`docker-compose restart`

### 错误 2：权限拒绝

```
挂载点不可写: Permission denied
```

**原因：** 容器没有写入权限

**解决：**
```bash
# 在主机上修改权限
sudo chown -R 1000:1000 /mnt/clouddrive
sudo chmod -R 755 /mnt/clouddrive
```

### 错误 3：路径不匹配

```
No such file or directory
```

**原因：** 挂载点路径配置不一致

**解决：**
1. 确认 CloudDrive2 的挂载路径
2. 确认 TMC 容器内能看到相同路径
3. 修改 TMC 配置使路径一致

---

## 💡 最佳实践

1. **使用标准路径：** `/CloudNAS/{云盘名称}`
2. **保持一致：** 确保所有配置中的路径一致
3. **验证后配置：** 先验证挂载点可访问，再配置 TMC
4. **查看日志：** 出现问题时第一时间查看容器日志

---

## 🎯 快速检查清单

配置前请确认：

- [ ] CloudDrive2 已成功挂载 115 网盘
- [ ] CloudDrive2 挂载路径明确（如 `/CloudNAS/115`）
- [ ] `docker-compose.yml` 中配置了共享 volumes
- [ ] TMC 容器内能访问挂载目录（`docker exec` 验证）
- [ ] TMC 配置中的挂载点路径与实际一致
- [ ] 容器有写入权限

全部确认后，重启服务并测试上传。

---

**参考文档：**
- [CloudDrive2 官方文档](https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html)
- `CLOUDDRIVE2_MOUNT_POINT_GUIDE.md` - 详细的挂载点配置指南
- `CLOUDDRIVE2_IMPLEMENTATION_SUMMARY.md` - CloudDrive2 实现总结

**最后更新：** 2025-10-19

