# 导入导出功能完整指南

## 📋 概述

本系统提供了完整的数据导入导出功能，支持规则配置、日志记录和聊天列表的备份与恢复。

---

## ✅ 已实现的功能

### 1. 转发规则 (Rules)

#### 导出规则
- **端点**: `POST /api/rules/export`
- **认证**: 需要登录
- **请求体**:
  ```json
  {
    "ids": [1, 2, 3]  // 可选，指定要导出的规则ID，留空导出全部
  }
  ```
- **响应**: JSON文件下载，包含完整的规则配置、关键词和替换规则

#### 导入规则
- **端点**: `POST /api/rules/import`
- **认证**: 需要登录
- **请求体**:
  ```json
  {
    "data": [
      {
        "name": "规则名称",
        "source_chat_id": "源聊天ID",
        "target_chat_id": "目标聊天ID",
        "is_active": true,
        "keywords": [...],
        "replacements": [...]
      }
    ]
  }
  ```
- **响应**: 导入结果统计

#### 导出字段说明
```json
{
  "id": 1,
  "name": "规则名称",
  "source_chat_id": "源聊天ID",
  "source_chat_name": "源聊天名称",
  "target_chat_id": "目标聊天ID",
  "target_chat_name": "目标聊天名称",
  "is_active": true,
  "enable_keyword_filter": false,
  "enable_regex_replace": false,
  "client_id": "main_user",
  "client_type": "user",
  
  // 消息类型开关
  "enable_text": true,
  "enable_media": true,
  "enable_photo": true,
  "enable_video": true,
  "enable_document": true,
  "enable_audio": true,
  "enable_voice": true,
  "enable_sticker": false,
  "enable_animation": true,
  "enable_webpage": true,
  
  // 高级设置
  "forward_delay": 0,
  "max_message_length": 4096,
  "enable_link_preview": true,
  "time_filter_type": "after_start",
  "start_time": "2025-01-01T00:00:00",
  "end_time": null,
  
  // 去重设置
  "enable_deduplication": false,
  "dedup_time_window": 3600,
  "dedup_check_content": true,
  "dedup_check_media": true,
  
  // 发送者过滤
  "enable_sender_filter": false,
  "sender_filter_mode": "whitelist",
  "sender_whitelist": "[...]",
  "sender_blacklist": "[...]",
  
  // 关键词
  "keywords": [
    {
      "keyword": "关键词",
      "is_regex": false,
      "is_exclude": false,
      "case_sensitive": false
    }
  ],
  
  // 替换规则
  "replacements": [
    {
      "name": "替换规则名称",
      "pattern": "匹配模式",
      "replacement": "替换内容",
      "priority": 0,
      "is_regex": true,
      "is_active": true,
      "is_global": false
    }
  ],
  
  // 时间戳
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

---

### 2. 消息日志 (Logs)

#### 导出日志
- **端点**: `POST /api/logs/export`
- **认证**: 需要登录
- **请求体**: 支持筛选条件
  ```json
  {
    "status": "success",           // 可选：success/failed
    "rule_id": 1,                  // 可选：规则ID
    "start_date": "2025-01-01",    // 可选：开始日期
    "end_date": "2025-01-31"       // 可选：结束日期
  }
  ```
- **响应**: JSON文件下载，包含符合条件的所有日志

#### 导入日志
- **端点**: `POST /api/logs/import`
- **认证**: 需要登录
- **请求体**:
  ```json
  {
    "data": [
      {
        "rule_id": 1,
        "source_chat_id": "源聊天ID",
        "source_message_id": 123,
        "target_chat_id": "目标聊天ID",
        "status": "success",
        ...
      }
    ]
  }
  ```
- **用途**: 用于恢复历史日志记录、数据迁移

#### 导出字段说明
```json
{
  "id": 1,
  "rule_id": 1,
  "rule_name": "规则名称",
  
  // 源消息信息
  "source_chat_id": "源聊天ID",
  "source_chat_name": "源聊天名称",
  "source_message_id": 123,
  
  // 目标消息信息
  "target_chat_id": "目标聊天ID",
  "target_chat_name": "目标聊天名称",
  "target_message_id": 456,
  
  // 消息内容
  "original_text": "原始文本",
  "processed_text": "处理后文本",
  "media_type": "photo",
  
  // 去重信息
  "content_hash": "内容哈希值",
  "media_hash": "媒体哈希值",
  "sender_id": "发送者ID",
  "sender_username": "发送者用户名",
  
  // 状态信息
  "status": "success",
  "error_message": null,
  "processing_time": 123,
  
  // 时间戳
  "created_at": "2025-01-01T12:00:00"
}
```

---

### 3. 聊天列表 (Chats)

#### 导出聊天列表
- **端点**: `POST /api/chats/export`
- **认证**: 需要登录
- **响应**: JSON文件下载，包含当前所有聊天信息

#### 导入聊天列表
- **端点**: `POST /api/chats/import`
- **认证**: 需要登录
- **请求体**:
  ```json
  {
    "data": [
      {
        "id": "聊天ID",
        "name": "聊天名称",
        "type": "channel/group/private",
        ...
      }
    ]
  }
  ```
- **注意**: 
  - 聊天列表是从Telegram实时同步的
  - 导入功能仅用于备份参考，不会影响实际的聊天列表
  - 实际聊天列表仍然从Telegram API获取

---

## 🔄 使用场景

### 场景1: 备份配置
1. 定期导出规则配置
2. 保存到安全位置
3. 需要时恢复

### 场景2: 迁移到新系统
1. 在旧系统导出规则
2. 在新系统导入规则
3. 验证规则是否正常工作

### 场景3: 分享配置模板
1. 导出精心配置的规则
2. 分享给其他用户
3. 其他用户导入后修改源/目标聊天

### 场景4: 数据分析
1. 导出日志记录
2. 使用Excel/Python进行分析
3. 生成统计报告

### 场景5: 故障恢复
1. 系统故障前有备份
2. 导入备份恢复配置
3. 快速恢复服务

---

## 📝 最佳实践

### 1. 定期备份
```bash
# 建议每周备份一次规则配置
# 文件名包含日期便于管理
rules_backup_2025-01-01.json
```

### 2. 导入前验证
- 检查JSON格式是否正确
- 确认字段名称匹配
- 测试小批量导入

### 3. 批量导入
- 支持一次导入多条记录
- 失败的记录会跳过，不影响其他记录
- 查看返回的成功/失败统计

### 4. 数据清理
- 导出前可以筛选需要的数据
- 避免导出敏感信息
- 定期清理旧日志

---

## ⚠️ 注意事项

### 导入规则时
- **聊天ID**: 需要手动修改为新系统中的实际ID
- **客户端ID**: 确保目标系统有对应的客户端
- **时间字段**: 使用ISO格式 `2025-01-01T12:00:00`
- **嵌套对象**: keywords和replacements会自动关联

### 导入日志时
- 不会检查消息ID是否真实存在
- 仅用于历史记录恢复
- created_at会保留原始时间

### 导入聊天列表时
- 仅作为备份参考
- 不影响实际的Telegram聊天列表
- 实际聊天列表从API同步

---

## 🛠️ 错误处理

### 常见错误

#### 1. 认证失败
```json
{
  "success": false,
  "message": "未授权"
}
```
**解决**: 确保已登录，token有效

#### 2. 数据格式错误
```json
{
  "success": false,
  "message": "导入数据为空"
}
```
**解决**: 检查请求体格式，确保data字段存在

#### 3. 字段缺失
```
导入规则失败 (跳过): 规则A - 缺少必需字段
```
**解决**: 补充必需字段（name, source_chat_id, target_chat_id）

#### 4. 部分导入成功
```json
{
  "success": true,
  "imported_count": 8,
  "message": "成功导入 8 条规则（总共 10 条）"
}
```
**说明**: 有2条记录失败，查看日志了解原因

---

## 🔍 API测试示例

### 使用curl导出规则
```bash
curl -X POST http://localhost:9393/api/rules/export \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": []}' \
  -o rules_backup.json
```

### 使用curl导入规则
```bash
curl -X POST http://localhost:9393/api/rules/import \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @rules_backup.json
```

### 使用curl导出日志
```bash
curl -X POST http://localhost:9393/api/logs/export \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31"}' \
  -o logs_backup.json
```

---

## 📊 数据统计

### 导出成功响应示例
```json
{
  "success": true,
  "data": [...],
  "message": "成功导出 10 条规则",
  "filename": "rules_export_20250109_220000.json"
}
```

### 导入成功响应示例
```json
{
  "success": true,
  "imported_count": 10,
  "message": "成功导入 10 条规则（总共 10 条）"
}
```

---

## 🎯 总结

本系统提供了完整的导入导出功能，支持：

✅ **规则导入导出** - 完整的配置备份与恢复  
✅ **日志导入导出** - 历史记录分析与迁移  
✅ **聊天导入导出** - 聊天列表备份参考  

所有功能都：
- 支持批量操作
- 包含错误处理
- 需要身份认证
- 提供详细日志
- 返回统计信息

---

## 📞 技术支持

如有问题，请查看：
1. 后端日志：`logs/api.log`
2. 浏览器控制台
3. 导入响应中的错误信息

更新日期: 2025-10-09
