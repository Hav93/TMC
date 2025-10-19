# CloudDrive2 快速开始指南 🚀

## 📋 前置条件

1. ✅ CloudDrive2 已安装并运行
2. ✅ CloudDrive2 中已添加115网盘账号
3. ✅ CloudDrive2 gRPC API 已启用
4. ✅ 已知115网盘的挂载点路径

## ⚡ 3分钟快速配置

### 步骤1: 访问设置页面

1. 打开 TMC Web 界面
2. 点击左侧菜单 **设置**
3. 切换到 **CloudDrive2** 标签页

### 步骤2: 填写配置

```
✓ 启用CloudDrive2上传：[开启]
✓ 主机地址：localhost          (如果CloudDrive2在其他主机，填写IP地址)
✓ 端口：19798                   (默认端口)
✓ 用户名：admin                 (如果启用了认证，否则留空)
✓ 密码：******                  (如果启用了认证，否则留空)
✓ 挂载点路径：/CloudNAS/115     (115网盘在CloudDrive2中的挂载路径)
```

### 步骤3: 测试连接

点击 **测试连接** 按钮，确认显示：
```
✅ CloudDrive2连接测试成功！
服务正常运行
```

### 步骤4: 保存配置

点击 **保存配置** 按钮，看到成功提示。

### 步骤5: 验证功能

1. 创建或编辑一个媒体监控规则
2. 配置上传到115网盘
3. 触发一次上传任务
4. 查看上传进度和日志

## 🎯 常见配置场景

### 场景1: 本地开发（Windows/Mac）

```
主机地址：localhost
端口：19798
挂载点：/CloudNAS/115
```

### 场景2: Docker Compose 同一网络

```
主机地址：clouddrive2        (服务名)
端口：19798
挂载点：/CloudNAS/115
```

### 场景3: 独立服务器

```
主机地址：192.168.1.100      (CloudDrive2服务器IP)
端口：19798
挂载点：/CloudNAS/115
```

### 场景4: 启用了认证

```
主机地址：localhost
端口：19798
用户名：admin
密码：your-password
挂载点：/CloudNAS/115
```

## ❓ 故障排查

### ❌ 连接测试失败

**检查清单：**
- [ ] CloudDrive2 服务是否运行？
- [ ] 端口是否正确（默认19798）？
- [ ] 防火墙是否允许访问？
- [ ] gRPC API 是否启用？

**解决方法：**
```bash
# 1. 检查CloudDrive2是否运行
# Windows: 任务管理器中查找 CloudDrive2
# Linux: ps aux | grep clouddrive

# 2. 测试端口是否开放
telnet localhost 19798

# 3. 查看CloudDrive2日志
# 在CloudDrive2界面中查看日志
```

### ❌ 上传失败

**检查清单：**
- [ ] 挂载点路径是否正确？
- [ ] 115账号是否登录？
- [ ] 目标目录是否存在？

**解决方法：**
1. 在 CloudDrive2 中确认挂载路径
2. 重新登录115账号
3. 手动创建目标目录

### ❌ grpcio 模块未安装

**解决方法：**
```bash
# 进入后端目录
cd app/backend

# 安装依赖
pip install grpcio grpcio-tools

# 或者重新安装所有依赖
pip install -r requirements.txt
```

## 📊 验证上传功能

### 方法1: 通过媒体监控

1. 创建媒体监控规则
2. 配置"归档到115网盘"
3. 选择目标目录
4. 触发一次媒体下载
5. 观察上传进度

### 方法2: 查看日志

```bash
# 后端日志
tail -f logs/api.log | grep CloudDrive2

# 查找上传相关日志
grep "CloudDrive2" logs/api.log
```

## 💡 使用技巧

### 技巧1: 使用秒传功能

CloudDrive2 支持115网盘的秒传（快速上传）功能：
- 系统会自动计算文件SHA1
- 如果115网盘已有该文件，秒传完成
- 节省上传时间和带宽

### 技巧2: 断点续传

上传大文件时：
- 如果上传中断，自动保存进度
- 再次上传时，从断点继续
- 无需重新上传整个文件

### 技巧3: 批量上传

- 多个文件可以并发上传
- 在媒体配置中设置并发数
- 建议设置为 2-3 以保持稳定

## 🔐 安全建议

1. **内网使用**：建议在内网环境使用CloudDrive2
2. **启用认证**：在CloudDrive2中启用gRPC认证
3. **定期更新**：保持CloudDrive2和TMC版本更新
4. **备份配置**：定期备份CloudDrive2配置

## 📚 更多资源

- [详细配置指南](./CLOUDDRIVE2_CONFIG_GUIDE.md)
- [实现总结](./CLOUDDRIVE2_IMPLEMENTATION_SUMMARY.md)
- [功能说明](./CLOUDDRIVE2_SETTINGS_ADDED.md)
- [上传指南](./CLOUDDRIVE2_UPLOAD_GUIDE.md)
- [CloudDrive2 官网](https://www.clouddrive2.com/)
- [CloudDrive2 API 文档](https://www.clouddrive2.com/api/)

## 🎉 完成！

配置完成后，您就可以：
- ✅ 自动上传媒体到115网盘
- ✅ 享受秒传和断点续传
- ✅ 通过Web界面查看上传进度
- ✅ 管理115网盘文件

有问题？查看[故障排查指南](./CLOUDDRIVE2_CONFIG_GUIDE.md#故障排查)

---

**最后更新：** 2025-10-19  
**版本：** v1.3.0-test

