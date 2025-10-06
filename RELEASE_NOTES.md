# TMC v1.0.0 发布说明

**发布日期**: 2025-10-06  
**版本类型**: 首个生产就绪版本 🎉

---

## 🎉 重大里程�?

这是 TMC (Telegram Message Center) 的首个生产就绪版本！经过全面测试和优化，现在可以稳定用于生产环境�?

---

## �?核心功能

### 消息转发系统
- �?�?Telegram 客户端管�?
- �?灵活的转发规则配�?
- �?关键词过滤和消息替换
- �?实时消息日志记录

### 用户系统
- �?JWT Token 认证
- �?用户权限管理
- �?个人资料和头像管�?
- �?安全的密码加密存�?

### 系统管理
- �?实时容器日志流（SSE�?
- �?系统状态监�?
- �?完整的数据库迁移支持
- �?健康检查机�?

### 界面体验
- �?现代化响应式设计
- �?深色/浅色主题切换（带流畅动画�?
- �?玻璃态视觉效�?
- �?完整�?TypeScript 类型支持

---

## 🔧 本版本修�?

### 关键问题修复
1. **主题切换问题** �?
   - 修复主题切换需要刷新页面的问题
   - 实现统一的色彩管理系�?
   - 添加 View Transitions API 动画效果

2. **认证问题** �?
   - 修复容器日志 401 未授权错�?
   - 修复系统状态接口认证失�?
   - 统一 localStorage key �?`access_token`
   - 支持 EventSource �?query 参数认证

3. **数据库迁�?* �?
   - 解决 Alembic "Multiple head revisions" 冲突
   - 修正迁移文件依赖�?

4. **项目结构** �?
   - 清理非生产文件到 `_archived` 目录
   - 优化 Docker 构建配置
   - 完善部署文档

---

## 🚀 部署方式

### Docker Hub 部署（推荐）

```bash
# 1. 创建目录
mkdir tmc && cd tmc

# 2. 下载配置文件
wget https://raw.githubusercontent.com/Hav93/tmc/main/docker-compose.yml
wget https://raw.githubusercontent.com/Hav93/tmc/main/.env.user.example
mv .env.user.example .env

# 3. 编辑 .env 文件，填�?Telegram API 配置

# 4. 启动服务
docker compose up -d
```

### 访问地址
- Web 界面: http://localhost:9393
- API 文档: http://localhost:9393/docs
- 默认账号: admin / admin123（首次登录后请立即修改！�?

---

## 📦 Docker 镜像

### 镜像标签
- `hav93/tmc:latest` - 最新稳定版
- `hav93/tmc:1.0.0` - 本版�?
- `hav93/tmc:1.0` - 1.0.x 系列最新版
- `hav93/tmc:1` - 1.x.x 系列最新版

### 支持架构
- �?linux/amd64 (x86_64)
- �?linux/arm64 (ARM v8, Apple Silicon)

---

## 📋 系统要求

### 最低配�?
- CPU: 2 �?
- 内存: 2 GB
- 磁盘: 5 GB
- Docker: 20.10+
- Docker Compose: 2.0+

### 推荐配置
- CPU: 4 �?
- 内存: 4 GB
- 磁盘: 10 GB SSD

---

## 🔐 安全更新

1. **JWT 认证**
   - 完整�?Token 认证机制
   - 支持自定义密钥和过期时间
   - 安全的密码哈希存储（bcrypt�?

2. **数据隔离**
   - 容器化运行，环境隔离
   - 数据卷持久化
   - 支持自定�?PUID/PGID（NAS 友好�?

3. **安全建议**
   - 首次登录后立即修改默认密�?
   - 使用强随�?JWT 密钥
   - 生产环境建议使用反向代理 + HTTPS

---

## 📖 文档

- **快速开�?*: `README.md`
- **部署指南**: `DEPLOYMENT.md`
- **GitHub 设置**: `GITHUB_SETUP.md`
- **项目状�?*: `PROJECT_STATUS.md`
- **更新日志**: `CHANGELOG.md`

---

## 🐛 已知问题

无重大已知问题�?

---

## 🔄 升级指南

### 从内部版本升�?

如果你之前使用的是内部开发版本：

```bash
# 1. 备份数据
tar -czf tmc-backup-$(date +%Y%m%d).tar.gz data sessions config

# 2. 拉取新镜�?
docker compose pull

# 3. 停止旧容�?
docker compose down

# 4. 启动新版�?
docker compose up -d

# 5. 查看日志
docker compose logs -f
```

---

## 🤝 贡献

欢迎提交 Issue �?Pull Request�?

### 报告问题
- GitHub Issues: https://github.com/Hav93/tmc/issues

### 功能建议
- 提交 Feature Request
- 详细描述使用场景和预期效�?

---

## 📊 统计

- **代码行数**: ~25,000+ �?
- **提交次数**: 100+ commits
- **开发周�?*: 2 个月
- **测试覆盖**: 核心功能已测�?

---

## 🙏 致谢

感谢所有测试用户的反馈和建议！

---

## 📅 下一步计�?

### v1.1.0 (计划�?
- [ ] 消息统计图表增强
- [ ] 规则导入/导出功能
- [ ] 性能优化
- [ ] 更多主题选项

### v1.2.0 (规划�?
- [ ] 多语言支持 (i18n)
- [ ] WebSocket 实时通知
- [ ] 高级过滤规则（正则表达式�?

---

## 📞 联系方式

- **项目主页**: https://github.com/Hav93/tmc
- **Docker Hub**: https://hub.docker.com/r/hav93/tmc
- **问题反馈**: GitHub Issues

---

**祝使用愉快！** 🎉

如果 TMC 对你有帮助，请给项目一�?⭐️ Star�?

