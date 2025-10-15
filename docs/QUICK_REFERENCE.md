# TMC 快速参考手册

## 📚 快速导航

- [文件位置](#文件位置)
- [API端点](#api端点)
- [核心类](#核心类)
- [常用方法](#常用方法)
- [配置参数](#配置参数)

---

## 文件位置

### 核心服务

| 功能 | 文件路径 |
|------|---------|
| 消息上下文 | `services/message_context.py` |
| 消息分发器 | `services/message_dispatcher.py` |
| 资源监控服务 | `services/resource_monitor_service.py` |
| 消息缓存 | `services/common/message_cache.py` |
| 过滤引擎 | `services/common/filter_engine.py` |
| 重试队列 | `services/common/retry_queue.py` |
| 批量写入器 | `services/common/batch_writer.py` |

### API路由

| 功能 | 文件路径 |
|------|---------|
| 资源监控API | `api/routes/resource_monitor.py` |
| 性能监控API | `api/routes/performance.py` |

### 数据模型

| 模型 | 文件路径 | 表名 |
|------|---------|------|
| ResourceMonitorRule | `models.py` | `resource_monitor_rules` |
| ResourceRecord | `models.py` | `resource_records` |

---

## API端点

### 资源监控 (`/api/resources`)

```
POST   /rules              创建规则
GET    /rules              获取所有规则
GET    /rules/{id}         获取指定规则
PUT    /rules/{id}         更新规则
DELETE /rules/{id}         删除规则
GET    /records            获取所有记录
GET    /records/{id}       获取指定记录
GET    /stats              获取统计信息
```

### 性能监控 (`/api/performance`)

```
GET    /stats                      获取所有统计
GET    /cache/stats                缓存统计
POST   /cache/clear                清空缓存
GET    /retry-queue/stats          重试队列统计
GET    /batch-writer/stats         批量写入器统计
POST   /batch-writer/flush         手动刷新
GET    /filter-engine/stats        过滤引擎统计
POST   /filter-engine/clear-cache  清空过滤缓存
```

---

## 核心类

### MessageContext

```python
from services.message_context import MessageContext

context = MessageContext(message, client_manager, chat_id)
links = await context.get_extracted_links()
matched = await context.get_matched_keywords(['关键词'])
```

### MessageDispatcher

```python
from services.message_dispatcher import get_message_dispatcher

dispatcher = get_message_dispatcher()
dispatcher.register(processor)
results = await dispatcher.dispatch(context)
```

### ResourceMonitorService

```python
from services.resource_monitor_service import ResourceMonitorService

async for db in get_db():
    service = ResourceMonitorService(db)
    await service.handle_new_message(context)
```

### LinkExtractor

```python
from services.resource_monitor_service import LinkExtractor

links = LinkExtractor.extract_all(text)
# 返回: {'pan115': [...], 'magnet': [...], 'ed2k': [...]}

link_hash = LinkExtractor.calculate_hash(url)
```

---

## 常用方法

### 缓存操作

```python
from services.common.message_cache import get_message_cache

cache = get_message_cache()
await cache.set('key', 'value')
value = await cache.get('key')
stats = cache.get_stats()
```

### 过滤引擎

```python
from services.common.filter_engine import get_filter_engine

engine = get_filter_engine()
matched = engine.match_keywords(text, ['关键词1', '关键词2'])
```

### 重试队列

```python
from services.common.retry_queue import get_retry_queue, RetryStrategy

queue = get_retry_queue()
await queue.add_task(
    task_id="task_1",
    task_type="resource_115_save",
    task_data={'record_id': 123},
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL
)
```

### 批量写入

```python
from services.common.batch_writer import get_batch_writer

writer = get_batch_writer()
await writer.add_insert(Model, {'field': 'value'})
await writer.add_update(Model, {'id': 1, 'field': 'new_value'})
await writer.flush_all()
```

---

## 配置参数

### 缓存管理器

```python
MessageCacheManager(
    max_size=1000,        # 最大缓存数
    default_ttl=3600,     # TTL（秒）
    cleanup_interval=300  # 清理间隔（秒）
)
```

### 重试队列

```python
SmartRetryQueue(
    max_concurrent=5,                        # 并发数
    persistence_enabled=True,                # 启用持久化
    persistence_path="data/retry_queue.json",
    persistence_interval=60                  # 持久化间隔（秒）
)
```

### 批量写入器

```python
BatchDatabaseWriter(
    batch_size=50,        # 批量大小
    flush_interval=10,    # 刷新间隔（秒）
    max_queue_size=1000   # 最大队列大小
)
```

---

## 数据模型字段

### ResourceMonitorRule（规则）

```python
{
    "name": "规则名称",
    "source_chats": ["123456789"],
    "is_active": true,
    "link_types": ["pan115", "magnet", "ed2k"],
    "keywords": [{"keyword": "关键词", "mode": "contains"}],
    "auto_save_to_115": false,
    "target_path": "/path",
    "enable_deduplication": true,
    "dedup_time_window": 3600
}
```

### ResourceRecord（记录）

```python
{
    "rule_id": 1,
    "link_type": "pan115",
    "link_url": "https://115.com/s/abc",
    "link_hash": "hash...",
    "save_status": "pending|saving|success|failed",
    "save_path": "/path",
    "retry_count": 0
}
```

---

## 快速命令

### 查看日志

```bash
# 应用日志
docker-compose logs -f tmc

# 特定模块
grep "resource_monitor" logs/enhanced_bot.log
```

### API测试

```bash
# 创建规则
curl -X POST http://localhost:8000/api/resources/rules \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","source_chats":["123"],"is_active":true}'

# 查看统计
curl http://localhost:8000/api/performance/stats \
  -H "Authorization: Bearer TOKEN"
```

### 数据库操作

```bash
# 进入容器
docker-compose exec tmc bash

# 查看数据库
sqlite3 data/tmc.db
.tables
SELECT * FROM resource_monitor_rules;
```

---

## 故障排查

### 问题：缓存未生效

```python
# 检查缓存统计
cache = get_message_cache()
stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']}")
```

### 问题：重试队列未持久化

```bash
# 检查持久化文件
ls -lh data/retry_queue.json

# 查看日志
grep "persistence" logs/enhanced_bot.log
```

### 问题：批量写入慢

```python
# 检查队列状态
writer = get_batch_writer()
stats = writer.get_stats()
print(f"队列大小: {stats['current_queue_size']}")
print(f"刷新次数: {stats['total_flushes']}")
```

---

**完整文档：** `docs/DEVELOPMENT_SUMMARY_STAGE1_2.md`

