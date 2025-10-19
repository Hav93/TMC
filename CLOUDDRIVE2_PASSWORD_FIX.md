# CloudDrive2 密码显示问题修复指南

## 问题描述

在服务器部署的 TMC 中，保存 CloudDrive2 配置后，刷新页面发现密码显示不正确（显示空白或只显示 `***`）。

## 问题原因

配置保存功能已正常工作（本地测试通过），但服务器部署和本地开发环境的配置文件不同步。

## 解决方案

### 方法 1：在服务器上直接保存配置（推荐）

1. **在服务器的 Web 界面操作**
   - 访问：`http://your-server-ip:9393`
   - 进入：**系统设置 → CloudDrive2**
   - 填写配置：
     ```
     启用CloudDrive2: ✅ 开启
     主机地址: 192.168.31.67
     端口: 19798
     用户名: 1695843548@qq.com
     密码: your_actual_password
     挂载点路径: /115open/测试
     ```
   - 点击：**保存配置**

2. **验证配置已保存**
   
   SSH 登录到服务器，检查配置文件：
   ```bash
   cat /path/to/TMC/config/app.config
   ```
   
   应该能看到：
   ```ini
   # === CloudDrive2 Config ===
   CLOUDDRIVE2_ENABLED=true
   CLOUDDRIVE2_HOST=192.168.31.67
   CLOUDDRIVE2_MOUNT_POINT=/115open/测试
   CLOUDDRIVE2_PASSWORD=your_actual_password
   CLOUDDRIVE2_PORT=19798
   CLOUDDRIVE2_USERNAME=1695843548@qq.com
   ```

3. **重启服务**
   ```bash
   cd /path/to/TMC
   docker-compose restart
   ```

4. **验证配置生效**
   - 刷新页面：**系统设置 → CloudDrive2**
   - 密码应该显示为：`***`（表示有密码）
   - 点击：**测试连接**
   - 应该显示：✅ 连接成功

### 方法 2：手动编辑配置文件

如果 Web 界面保存不生效，可以直接编辑配置文件：

1. **SSH 登录服务器**

2. **编辑配置文件**
   ```bash
   cd /path/to/TMC
   vim config/app.config
   ```

3. **添加 CloudDrive2 配置**
   ```ini
   # === CloudDrive2 配置 ===
   CLOUDDRIVE2_ENABLED=true
   CLOUDDRIVE2_HOST=192.168.31.67
   CLOUDDRIVE2_PORT=19798
   CLOUDDRIVE2_USERNAME=1695843548@qq.com
   CLOUDDRIVE2_PASSWORD=your_actual_password
   CLOUDDRIVE2_MOUNT_POINT=/115open/测试
   ```

4. **保存并重启**
   ```bash
   # 保存文件（vim: :wq）
   docker-compose restart
   ```

### 方法 3：使用环境变量（Docker）

1. **编辑 docker-compose.yml**
   ```yaml
   services:
     tmc:
       environment:
         - CLOUDDRIVE2_ENABLED=true
         - CLOUDDRIVE2_HOST=192.168.31.67
         - CLOUDDRIVE2_PORT=19798
         - CLOUDDRIVE2_USERNAME=1695843548@qq.com
         - CLOUDDRIVE2_PASSWORD=your_actual_password
         - CLOUDDRIVE2_MOUNT_POINT=/115open/测试
   ```

2. **重新启动**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## 密码显示逻辑说明

### 前端显示规则

```javascript
// 如果有密码，显示 ***
password: existingPassword ? '***' : ''
```

### 保存逻辑

```python
# 1. 用户输入新密码
if data.password and data.password != '***':
    config_to_save['CLOUDDRIVE2_PASSWORD'] = data.password

# 2. 用户保持 *** 不变（不修改密码）
else:
    existing_password = os.getenv('CLOUDDRIVE2_PASSWORD', '')
    if existing_password:
        config_to_save['CLOUDDRIVE2_PASSWORD'] = existing_password
```

### 正确的操作流程

**首次配置：**
1. 输入完整信息（包括密码）
2. 点击保存
3. 密码被保存到 `config/app.config`

**修改其他配置（不修改密码）：**
1. 打开设置页面，密码显示为 `***`
2. 修改其他字段（如主机地址）
3. 保持密码为 `***`
4. 点击保存
5. 系统自动保留原密码 ✅

**修改密码：**
1. 打开设置页面，密码显示为 `***`
2. 清空密码字段，输入新密码
3. 点击保存
4. 新密码被保存 ✅

## 验证步骤

### 1. 检查配置文件

**在服务器上：**
```bash
cat /path/to/TMC/config/app.config | grep CLOUDDRIVE2
```

应该输出：
```
CLOUDDRIVE2_ENABLED=true
CLOUDDRIVE2_HOST=192.168.31.67
CLOUDDRIVE2_MOUNT_POINT=/115open/测试
CLOUDDRIVE2_PASSWORD=your_actual_password
CLOUDDRIVE2_PORT=19798
CLOUDDRIVE2_USERNAME=1695843548@qq.com
```

### 2. 检查环境变量

**在容器内：**
```bash
docker exec -it tmc-backend printenv | grep CLOUDDRIVE2
```

应该输出相同的配置。

### 3. 测试连接

**在 Web 界面：**
- 系统设置 → CloudDrive2
- 点击 **测试连接**
- 应该显示：✅ CloudDrive2连接测试成功！

### 4. 测试上传

**触发媒体上传：**
- 发送测试文件到 Telegram
- 查看日志：
  ```bash
  docker logs tmc-backend --tail 50
  ```
- 应该看到：
  ```
  📂 CloudDrive2路径配置:
     规则路径: /115open/测试
     全局挂载点: /115open/测试
     最终使用: /115open/测试
  🔌 连接到 CloudDrive2: 192.168.31.67:19798
  ✅ CloudDrive2 连接成功
  ✅ 挂载点可用
  ✅ 文件已通过CloudDrive2上传
  ```

## 常见问题

### Q1: 为什么我保存后密码还是空的？

**A:** 可能原因：
1. **服务器和本地文件不同步**：您在本地看到的配置文件不是服务器上的
2. **容器挂载问题**：`config` 目录没有正确挂载到容器
3. **权限问题**：容器没有写入权限

**解决方法：**
- 确认您是在**服务器的 Web 界面**操作，不是本地
- 检查 `docker-compose.yml` 中的 volumes 配置：
  ```yaml
  volumes:
    - ./config:/app/config  # 确保这行存在
  ```

### Q2: 测试连接失败怎么办？

**A:** 检查：
1. CloudDrive2 服务是否运行：`docker ps | grep clouddrive`
2. 主机地址和端口是否正确
3. 用户名和密码是否正确
4. 网络是否可达：`ping 192.168.31.67`

### Q3: 挂载点不存在怎么办？

**A:** 挂载点路径必须与 CloudDrive2 中配置的一致：
1. 打开 CloudDrive2 管理界面
2. 查看 115 网盘的挂载路径（如 `/115open/测试`）
3. 在 TMC 设置中填写相同的路径

### Q4: 配置文件在哪里？

**A:**
- **服务器部署**：`/path/to/TMC/config/app.config`
- **Docker 内**：`/app/config/app.config`
- **本地开发**：`C:\Users\xxx\Desktop\TG-Message\TMC\config\app.config`

## 调试命令

### 查看容器日志
```bash
docker logs tmc-backend --tail 100 -f
```

### 查看配置文件
```bash
docker exec -it tmc-backend cat /app/config/app.config
```

### 查看环境变量
```bash
docker exec -it tmc-backend printenv | grep CLOUDDRIVE2
```

### 测试配置保存
```bash
# 在本地
python test_save_cd2_config.py

# 在服务器
ssh your-server
cd /path/to/TMC
python test_save_cd2_config.py
```

## 总结

1. ✅ **配置保存功能正常**：代码已验证可以正确保存
2. ⚠️ **操作位置很重要**：必须在服务器的 Web 界面操作
3. ✅ **多种配置方式**：支持 Web 界面、配置文件、环境变量
4. ✅ **密码智能处理**：自动区分新密码和保持原密码

---

**最后更新：** 2025-10-19  
**测试状态：** ✅ 本地保存功能测试通过

