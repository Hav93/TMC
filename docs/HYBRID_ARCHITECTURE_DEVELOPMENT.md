# 混合架构开发完整文档

## 📋 目录

1. [架构概述](#架构概述)
2. [现状分析](#现状分析)
3. [开发计划](#开发计划)
4. [详细设计](#详细设计)
5. [实施步骤](#实施步骤)
6. [测试方案](#测试方案)
7. [部署方案](#部署方案)
8. [115Bot借鉴与优化](#115bot借鉴与优化)
9. [附录](#附录)

---

## 1. 架构概述

### 1.1 核心思想

**混合架构 = 规则独立 + 处理统一 + 基础设施共享**

```
┌─────────────────────────────────────────────────────────────┐
│                    数据层：规则独立                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ForwardRule   │  │ResourceRule  │  │MediaMonitor  │     │
│  │(已有)        │  │(新建)        │  │Rule(已有)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              业务层：处理统一（消息处理器模式）               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            MessageDispatcher (消息分发器)             │  │
│  └───────────────────────────────────────────────────────┘  │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Forward      │  │Resource     │  │Media        │        │
│  │Processor    │  │Processor    │  │Processor    │        │
│  │(重构)       │  │(新建)       │  │(包装)       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           基础设施层：共享基础设施（新建）                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • MessageCacheManager (消息缓存)                       │  │
│  │ • SharedFilterEngine (共享过滤引擎)                    │  │
│  │ • SmartRetryQueue (智能重试队列)                       │  │
│  │ • BatchDatabaseWriter (批量数据库写入)                 │  │
│  │ • PerformanceMonitor (性能监控)                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 设计原则

1. **最小化改动**：保留现有代码，渐进式重构
2. **向后兼容**：不破坏现有功能
3. **性能优先**：通过缓存和批量处理提升性能
4. **可扩展性**：易于添加新的处理器
5. **可观测性**：完善的监控和日志

---

## 2. 现状分析

### 2.1 已有代码清单

#### ✅ 完整实现的模块

| 文件路径 | 功能 | 代码行数 | 状态 |
|---------|------|---------|------|
| `app/backend/telegram_client_manager.py` | Telegram客户端管理 | 2513行 | ✅ 完整 |
| `app/backend/models.py` | 数据模型定义 | 571行 | ✅ 完整 |
| `app/backend/services/media_monitor_service.py` | 媒体监控服务 | 1316行 | ✅ 完整 |
| `app/backend/services/business_services.py` | 业务服务层 | 661行 | ✅ 完整 |
| `app/backend/filters.py` | 关键词过滤和正则替换 | 154行 | ✅ 完整 |
| `app/backend/database.py` | 数据库连接 | ~100行 | ✅ 完整 |

#### 🔧 需要重构的模块

| 模块 | 当前位置 | 问题 | 重构方案 |
|------|---------|------|---------|
| **转发逻辑** | `TelegramClientManager._process_message()` | 800+行代码混在客户端管理器中 | 提取到 `ForwardProcessor` |
| **消息处理** | `TelegramClientManager._forward_message()` | 直接调用 `self.client` | 通过 `MessageContext` 封装 |
| **日志记录** | `TelegramClientManager._log_message()` | 每条消息单独写入 | 改为批量写入 |

#### ❌ 缺失的模块

| 模块 | 功能 | 优先级 |
|------|------|--------|
| `ResourceMonitorRule` 模型 | 资源监控规则数据模型 | 🔴 P0 |
| `ResourceRecord` 模型 | 资源记录数据模型 | 🔴 P0 |
| `ResourceMonitorService` | 资源监控服务 | 🔴 P0 |
| `MessageContext` | 消息处理上下文 | 🔴 P0 |
| `MessageDispatcher` | 消息分发器 | 🔴 P0 |
| `SharedFilterEngine` | 共享过滤引擎 | 🟡 P1 |
| `MessageCacheManager` | 消息缓存管理器 | 🟡 P1 |
| `SmartRetryQueue` | 智能重试队列 | 🟡 P1 |
| `BatchDatabaseWriter` | 批量数据库写入 | 🟢 P2 |
| `PerformanceMonitor` | 性能监控 | 🟢 P2 |

### 2.2 现有代码分析

#### 2.2.1 消息处理流程（当前）

```python
# 文件：app/backend/telegram_client_manager.py (第730-798行)
async def _process_message(self, event, is_edited: bool = False):
    """处理消息（在独立任务中运行）- 优化版"""
    message = event.message
    
    # 1. 获取聊天ID
    chat_id = self._get_chat_id(message)
    
    # 2. 检查是否在监听列表
    if chat_id not in self.monitored_chats:
        return
    
    # 3. 处理转发规则（内联逻辑，800+行）
    rules = await self._get_applicable_rules(chat_id)
    for rule in rules:
        await self._process_rule_safe(rule, message, event)
    
    # 4. 处理媒体监控规则
    await self._process_media_monitor(chat_id, message)
    
    # ❌ 问题：
    # - 转发逻辑混在客户端管理器中
    # - 没有资源监控处理
    # - 没有统一的分发机制
```

#### 2.2.2 转发消息实现（当前）

```python
# 文件：app/backend/telegram_client_manager.py (第1106-1139行)
async def _forward_message(self, rule: ForwardRule, original_message, text_to_forward: str):
    """转发消息（支持文本和媒体消息）"""
    target_chat_id = int(rule.target_chat_id)
    
    # ✅ 优点：实现完整，支持文本和媒体
    if original_message.media:
        await self.client.send_message(
            target_chat_id,
            text_to_forward,
            file=original_message.media
        )
    else:
        await self.client.send_message(
            target_chat_id,
            text_to_forward
        )
    
    # ❌ 问题：
    # - 直接调用 self.client（事件循环问题）
    # - 没有重试机制
    # - 没有批量处理
```

#### 2.2.3 媒体监控实现（当前）

```python
# 文件：app/backend/services/media_monitor_service.py (第238-618行)
class MediaMonitorService:
    """媒体监控服务"""
    
    def __init__(self):
        self.active_monitors: Dict[int, bool] = {}
        self.download_queue = asyncio.Queue()
        self.download_workers: List[asyncio.Task] = []
    
    async def process_message(self, client, message, rule_id: int):
        """处理消息"""
        # 1. 检查规则
        # 2. 应用过滤器
        # 3. 创建下载任务
        # 4. 加入队列
        pass
    
    # ✅ 优点：
    # - 已经是独立服务
    # - 有队列和工作线程
    # - 实现完整
    
    # 🔧 需要优化：
    # - 与新架构集成
    # - 添加批量处理
```

### 2.3 数据库结构分析

#### 已有表结构

```sql
-- 1. forward_rules (转发规则) ✅
CREATE TABLE forward_rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    source_chat_id VARCHAR(50),  -- 单个聊天ID
    target_chat_id VARCHAR(50),
    is_active BOOLEAN,
    enable_keyword_filter BOOLEAN,
    enable_regex_replace BOOLEAN,
    -- ... 其他字段
);

-- 2. media_monitor_rules (媒体监控规则) ✅
CREATE TABLE media_monitor_rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    source_chats TEXT,  -- JSON: 多个聊天ID
    is_active BOOLEAN,
    -- ... 其他字段
);

-- 3. message_logs (消息日志) ✅
CREATE TABLE message_logs (
    id INTEGER PRIMARY KEY,
    rule_id INTEGER,
    source_chat_id VARCHAR(50),
    status VARCHAR(20),
    -- ... 其他字段
);

-- 4. download_tasks (下载任务) ✅
CREATE TABLE download_tasks (
    id INTEGER PRIMARY KEY,
    rule_id INTEGER,
    message_id INTEGER,
    status VARCHAR(20),
    -- ... 其他字段
);

-- 5. media_files (媒体文件) ✅
CREATE TABLE media_files (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,
    file_name VARCHAR(500),
    file_type VARCHAR(50),
    -- ... 其他字段
);
```

#### 需要新建的表

```sql
-- 6. resource_monitor_rules (资源监控规则) ❌ 新建
CREATE TABLE resource_monitor_rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    source_chats TEXT NOT NULL,  -- JSON: ["chat_id1", "chat_id2"]
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 链接过滤
    link_types TEXT,  -- JSON: ["pan115", "magnet", "ed2k"]
    keywords TEXT,  -- JSON: [{"keyword": "xxx", "is_exclude": false}]
    
    -- 115配置
    auto_save_to_115 BOOLEAN DEFAULT FALSE,
    target_path VARCHAR(500),
    pan115_user_key VARCHAR(100),  -- 可以为空，使用全局配置
    
    -- 标签
    default_tags TEXT,  -- JSON: ["tag1", "tag2"]
    
    -- 去重
    enable_deduplication BOOLEAN DEFAULT TRUE,
    dedup_time_window INTEGER DEFAULT 3600,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. resource_records (资源记录) ❌ 新建
CREATE TABLE resource_records (
    id INTEGER PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    rule_name VARCHAR(100),
    
    -- 消息信息
    source_chat_id VARCHAR(50),
    source_chat_name VARCHAR(200),
    message_id INTEGER,
    message_text TEXT,
    message_date DATETIME,
    
    -- 链接信息
    link_type VARCHAR(20),  -- 'pan115', 'magnet', 'ed2k'
    link_url TEXT NOT NULL,
    link_hash VARCHAR(64),  -- MD5哈希，用于去重
    
    -- 115转存信息
    save_status VARCHAR(20) DEFAULT 'pending',  -- pending, saving, success, failed, ignored
    save_path VARCHAR(500),
    save_error TEXT,
    save_time DATETIME,
    retry_count INTEGER DEFAULT 0,
    
    -- 标签
    tags TEXT,  -- JSON: ["tag1", "tag2"]
    
    -- 消息快照
    message_snapshot TEXT,  -- JSON: 完整消息数据
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rule_id) REFERENCES resource_monitor_rules(id) ON DELETE CASCADE
);

-- 8. retry_tasks (重试任务) ❌ 新建
CREATE TABLE retry_tasks (
    id INTEGER PRIMARY KEY,
    task_id VARCHAR(64) UNIQUE NOT NULL,  -- MD5哈希
    task_type VARCHAR(20) NOT NULL,  -- 'forward', 'resource', 'media'
    task_data TEXT NOT NULL,  -- JSON
    
    -- 错误信息
    error_type VARCHAR(50),
    last_error TEXT,
    
    -- 重试信息
    attempt INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    next_retry_time DATETIME,
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 9. notification_rules (通知规则) ❌ 新建
CREATE TABLE notification_rules (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,  -- 用户ID，NULL表示全局规则
    notification_type VARCHAR(50) NOT NULL,  -- 通知类型
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 通知渠道配置
    telegram_chat_id VARCHAR(50),  -- Telegram聊天ID
    webhook_url VARCHAR(500),  -- Webhook URL
    email_address VARCHAR(200),  -- 邮箱地址
    
    -- 通知频率控制
    min_interval INTEGER DEFAULT 0,  -- 最小间隔（秒）
    max_per_hour INTEGER DEFAULT 0,  -- 每小时最大数量（0表示不限制）
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_notification_type (notification_type),
    INDEX idx_user_id (user_id)
);

-- 10. notification_logs (通知历史) ❌ 新建
CREATE TABLE notification_logs (
    id INTEGER PRIMARY KEY,
    notification_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    channels VARCHAR(200),  -- 通知渠道（逗号分隔）
    user_id INTEGER,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_sent_at (sent_at),
    INDEX idx_notification_type (notification_type)
);
```

---

## 3. 开发计划

### 3.1 阶段划分

#### 🔴 阶段1：核心架构（P0，3-4天）

**目标**：建立混合架构基础，实现资源监控MVP

| 任务 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 1.1 创建数据模型 | `models.py` | 0.5天 | 无 |
| 1.2 创建数据库迁移 | `alembic/versions/xxx.py` | 0.5天 | 1.1 |
| 1.3 创建消息上下文 | `services/message_context.py` | 0.5天 | 无 |
| 1.4 创建消息分发器 | `services/message_dispatcher.py` | 1天 | 1.3 |
| 1.5 创建资源监控服务 | `services/resource_monitor_service.py` | 1天 | 1.1 |
| 1.6 集成到客户端管理器 | `telegram_client_manager.py` | 0.5天 | 1.4, 1.5 |
| 1.7 创建API路由 | `api/routes/resource_monitor.py` | 0.5天 | 1.5 |

#### 🟡 阶段2：性能优化（P1，2-3天）

**目标**：添加缓存、批量处理、智能重试

| 任务 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 2.1 消息缓存管理器 | `services/common/message_cache.py` | 0.5天 | 阶段1 |
| 2.2 共享过滤引擎 | `services/common/filter_engine.py` | 0.5天 | 阶段1 |
| 2.3 智能重试队列 | `services/common/retry_queue.py` | 1天 | 阶段1 |
| 2.4 批量数据库写入 | `services/common/batch_writer.py` | 1天 | 阶段1 |

#### 🟢 阶段3：前端界面（P1，2-3天）

**目标**：完善前端界面，提升用户体验

| 任务 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 3.1 规则列表页面 | `frontend/src/pages/ResourceMonitor/RuleList.tsx` | 0.5天 | 阶段1 |
| 3.2 规则表单页面 | `frontend/src/pages/ResourceMonitor/RuleForm.tsx` | 1天 | 阶段1 |
| 3.3 记录列表页面 | `frontend/src/pages/ResourceMonitor/RecordList.tsx` | 1天 | 阶段1 |
| 3.4 快捷创建向导 | `frontend/src/pages/ResourceMonitor/QuickWizard.tsx` | 0.5天 | 3.1, 3.2 |

#### 🟢 阶段4：监控和优化（P2，1-2天）

**目标**：添加监控面板，优化性能

| 任务 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 4.1 性能监控器 | `services/common/performance_monitor.py` | 0.5天 | 阶段2 |
| 4.2 监控API | `api/routes/monitor.py` | 0.5天 | 4.1 |
| 4.3 监控面板 | `frontend/src/pages/Monitor/Dashboard.tsx` | 1天 | 4.2 |

#### 🟡 阶段5：推送通知系统（P1，2-3天）

**目标**：实现完整的推送通知功能

| 任务 | 文件 | 工作量 | 依赖 |
|------|------|--------|------|
| 5.1 通知服务核心 | `services/notification_service.py` | 1天 | 阶段1 |
| 5.2 通知模板引擎 | `services/notification_templates.py` | 0.5天 | 5.1 |
| 5.3 通知API | `api/routes/notifications.py` | 0.5天 | 5.1 |
| 5.4 前端通知中心 | `frontend/src/components/NotificationCenter.tsx` | 1天 | 5.3 |

### 3.2 时间线

```
Week 1:
  Day 1-2: 阶段1.1-1.4 (数据模型 + 消息分发器)
  Day 3-4: 阶段1.5-1.7 (资源监控服务 + API)
  Day 5:   测试和修复

Week 2:
  Day 1-2: 阶段2.1-2.4 (性能优化)
  Day 3-4: 阶段3.1-3.3 (前端界面)
  Day 5:   阶段4 (监控面板)

Week 3:
  Day 1-2: 阶段5 (推送通知系统)
  Day 3-5: 完整测试和优化

Week 4:
  Day 1-3: 115Bot借鉴功能 (秒传/过滤/调度)
  Day 4-5: 文档和部署
```

---

## 4. 详细设计

### 4.1 核心类设计

#### 4.1.1 MessageContext（消息上下文）

```python
# 文件：app/backend/services/message_context.py
from dataclasses import dataclass
from typing import Any, Optional
import asyncio

@dataclass
class MessageContext:
    """
    消息处理上下文
    
    作用：
    1. 封装消息和客户端管理器
    2. 提供安全的客户端操作方法
    3. 处理事件循环问题
    """
    
    message: Any  # Telethon Message 对象
    client_manager: 'TelegramClientManager'
    chat_id: int
    is_edited: bool = False
    
    # 缓存的处理结果（避免重复计算）
    _extracted_links: Optional[dict] = None
    _matched_keywords: Optional[list] = None
    
    async def send_message(self, chat_id: int, text: str, **kwargs):
        """
        安全地发送消息
        
        自动处理：
        - 事件循环切换
        - 连接状态检查
        - 超时控制
        """
        return await self.client_manager._safe_send_message(
            chat_id, text, **kwargs
        )
    
    async def download_media(self, file_path: str):
        """安全地下载媒体"""
        return await self.client_manager._safe_download_media(
            self.message, file_path
        )
    
    def is_connected(self) -> bool:
        """检查客户端连接状态"""
        return self.client_manager.connected
    
    def get_extracted_links(self) -> dict:
        """获取提取的链接（带缓存）"""
        if self._extracted_links is None:
            from services.link_extractor import LinkExtractor
            self._extracted_links = LinkExtractor.extract_all(
                self.message.text or ""
            )
        return self._extracted_links
    
    def get_matched_keywords(self, keywords: list) -> list:
        """获取匹配的关键词（带缓存）"""
        cache_key = tuple(sorted(keywords))
        if self._matched_keywords is None:
            self._matched_keywords = {}
        
        if cache_key not in self._matched_keywords:
            from filters import KeywordFilter
            filter_engine = KeywordFilter()
            self._matched_keywords[cache_key] = filter_engine.match(
                self.message.text or "", keywords
            )
        
        return self._matched_keywords[cache_key]
```

**关键点：**
- ✅ 封装客户端操作，避免直接访问 `self.client`
- ✅ 自动处理事件循环问题
- ✅ 缓存处理结果，避免重复计算
- ✅ 提供便捷方法，简化处理器代码

#### 4.1.2 MessageDispatcher（消息分发器）

```python
# 文件：app/backend/services/message_dispatcher.py
from typing import List, Dict
import asyncio
import time

class MessageProcessor:
    """消息处理器基类"""
    
    async def should_process(self, context: MessageContext) -> bool:
        """判断是否应该处理这条消息"""
        raise NotImplementedError
    
    async def process(self, context: MessageContext) -> bool:
        """处理消息，返回是否成功"""
        raise NotImplementedError

class MessageDispatcher:
    """
    消息分发器
    
    作用：
    1. 统一管理所有处理器
    2. 并发执行处理器
    3. 收集处理结果
    4. 性能监控
    """
    
    def __init__(self):
        self.processors: List[MessageProcessor] = []
        self.stats = {
            'total_messages': 0,
            'total_processing_time': 0,
            'processor_stats': {}
        }
    
    def register(self, processor: MessageProcessor):
        """注册处理器"""
        self.processors.append(processor)
        processor_name = processor.__class__.__name__
        self.stats['processor_stats'][processor_name] = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'avg_time': 0
        }
    
    async def dispatch(self, context: MessageContext) -> Dict[str, bool]:
        """
        分发消息给所有处理器
        
        返回：{processor_name: success}
        """
        start_time = time.time()
        self.stats['total_messages'] += 1
        
        # 1. 筛选需要处理的处理器
        active_processors = []
        for processor in self.processors:
            if await processor.should_process(context):
                active_processors.append(processor)
        
        if not active_processors:
            return {}
        
        # 2. 并发执行所有处理器
        tasks = []
        for processor in active_processors:
            task = asyncio.create_task(
                self._process_with_stats(processor, context)
            )
            tasks.append((processor.__class__.__name__, task))
        
        # 3. 等待所有处理器完成
        results = {}
        for processor_name, task in tasks:
            try:
                success = await task
                results[processor_name] = success
            except Exception as e:
                logger.error(f"处理器 {processor_name} 执行失败: {e}")
                results[processor_name] = False
        
        # 4. 更新统计
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return results
    
    async def _process_with_stats(self, processor: MessageProcessor, context: MessageContext) -> bool:
        """执行处理器并记录统计"""
        processor_name = processor.__class__.__name__
        stats = self.stats['processor_stats'][processor_name]
        
        start_time = time.time()
        stats['processed'] += 1
        
        try:
            success = await processor.process(context)
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # 更新平均处理时间
            processing_time = time.time() - start_time
            stats['avg_time'] = (
                (stats['avg_time'] * (stats['processed'] - 1) + processing_time) 
                / stats['processed']
            )
            
            return success
            
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"处理器 {processor_name} 执行异常: {e}")
            return False
    
    def get_stats(self) -> dict:
        """获取统计数据"""
        return {
            'total_messages': self.stats['total_messages'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_messages']
                if self.stats['total_messages'] > 0 else 0
            ),
            'processors': self.stats['processor_stats']
        }
```

**关键点：**
- ✅ 统一的处理器接口
- ✅ 并发执行，互不阻塞
- ✅ 完整的统计数据
- ✅ 异常隔离，单个处理器失败不影响其他

#### 4.1.3 ResourceMonitorService（资源监控服务）

```python
# 文件：app/backend/services/resource_monitor_service.py
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger
from database import get_db
from models import ResourceMonitorRule, ResourceRecord

logger = get_logger("resource_monitor", "enhanced_bot.log")

class LinkExtractor:
    """链接提取器"""
    
    PATTERNS = {
        'pan115': [
            r'https?://(?:115|115cdn)\.com/s/[a-zA-Z0-9]+(?:\?password=[a-zA-Z0-9]+)?',
            r'115://[a-zA-Z0-9]+',
        ],
        'magnet': [
            r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,40}[^\s]*',
        ],
        'ed2k': [
            r'ed2k://\|file\|[^\|]+\|[0-9]+\|[a-fA-F0-9]{32}\|[^\s]*',
        ]
    }
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, List[str]]:
        """提取所有类型的链接"""
        import re
        
        results = {}
        for link_type, patterns in cls.PATTERNS.items():
            links = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                links.extend(matches)
            
            if links:
                results[link_type] = list(set(links))  # 去重
        
        return results
    
    @classmethod
    def calculate_hash(cls, link: str) -> str:
        """计算链接哈希（用于去重）"""
        return hashlib.md5(link.encode()).hexdigest()

class ResourceMonitorService:
    """
    资源监控服务
    
    功能：
    1. 监控消息中的资源链接
    2. 提取115/磁力/ed2k链接
    3. 自动转存到115网盘
    4. 去重和标签管理
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_active_rules_for_chat(self, chat_id: int) -> List[ResourceMonitorRule]:
        """获取聊天的活跃规则"""
        result = await self.db.execute(
            select(ResourceMonitorRule).where(
                ResourceMonitorRule.is_active == True
            )
        )
        all_rules = result.scalars().all()
        
        # 过滤匹配的规则
        matched_rules = []
        for rule in all_rules:
            source_chats = json.loads(rule.source_chats) if rule.source_chats else []
            source_chat_ids = [int(c) for c in source_chats]
            
            if int(chat_id) in source_chat_ids:
                matched_rules.append(rule)
        
        return matched_rules
    
    async def handle_new_message(self, context: MessageContext):
        """
        处理新消息
        
        流程：
        1. 获取适用的规则
        2. 提取链接
        3. 关键词过滤
        4. 去重检查
        5. 创建记录
        6. 自动转存（如果启用）
        """
        try:
            # 1. 获取规则
            rules = await self.get_active_rules_for_chat(context.chat_id)
            if not rules:
                return
            
            logger.info(f"找到 {len(rules)} 个资源监控规则")
            
            # 2. 提取链接
            links = context.get_extracted_links()
            if not links:
                logger.info("消息中未找到链接")
                return
            
            logger.info(f"提取到链接: {links}")
            
            # 3. 处理每个规则
            for rule in rules:
                await self._process_rule(context, rule, links)
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
    
    async def _process_rule(self, context: MessageContext, rule: ResourceMonitorRule, links: dict):
        """处理单个规则"""
        try:
            # 1. 关键词过滤
            if rule.keywords:
                keywords = json.loads(rule.keywords)
                matched = context.get_matched_keywords([k['keyword'] for k in keywords])
                if not matched:
                    logger.info(f"规则 {rule.name} 关键词不匹配")
                    return
            
            # 2. 链接类型过滤
            link_types = json.loads(rule.link_types) if rule.link_types else []
            
            # 3. 处理每个链接
            for link_type in link_types:
                if link_type not in links:
                    continue
                
                for link_url in links[link_type]:
                    await self._process_link(context, rule, link_type, link_url)
                    
        except Exception as e:
            logger.error(f"处理规则 {rule.name} 失败: {e}", exc_info=True)
    
    async def _process_link(self, context: MessageContext, rule: ResourceMonitorRule, 
                           link_type: str, link_url: str):
        """处理单个链接"""
        try:
            # 1. 去重检查
            link_hash = LinkExtractor.calculate_hash(link_url)
            
            if rule.enable_deduplication:
                if await self._is_duplicate(link_hash, rule.dedup_time_window):
                    logger.info(f"链接已存在（去重）: {link_url[:50]}")
                    return
            
            # 2. 创建记录
            record = await self._create_record(context, rule, link_type, link_url, link_hash)
            
            # 3. 自动转存
            if rule.auto_save_to_115 and link_type == 'pan115':
                await self._auto_save_to_115(record, rule)
                
        except Exception as e:
            logger.error(f"处理链接失败: {e}", exc_info=True)
    
    async def _is_duplicate(self, link_hash: str, time_window: int) -> bool:
        """检查链接是否重复"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window)
        
        result = await self.db.execute(
            select(ResourceRecord).where(
                and_(
                    ResourceRecord.link_hash == link_hash,
                    ResourceRecord.created_at >= cutoff_time
                )
            ).limit(1)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def _create_record(self, context: MessageContext, rule: ResourceMonitorRule,
                            link_type: str, link_url: str, link_hash: str) -> ResourceRecord:
        """创建资源记录"""
        # 获取默认标签
        default_tags = json.loads(rule.default_tags) if rule.default_tags else []
        
        # 创建消息快照
        message_snapshot = {
            'id': context.message.id,
            'date': context.message.date.isoformat() if context.message.date else None,
            'text': context.message.text or "",
            'chat_id': context.chat_id
        }
        
        record = ResourceRecord(
            rule_id=rule.id,
            rule_name=rule.name,
            source_chat_id=str(context.chat_id),
            message_id=context.message.id,
            message_text=context.message.text or "",
            message_date=context.message.date,
            link_type=link_type,
            link_url=link_url,
            link_hash=link_hash,
            save_status='pending',
            tags=json.dumps(default_tags),
            message_snapshot=json.dumps(message_snapshot)
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        
        logger.info(f"✅ 创建资源记录: {record.id}")
        return record
    
    async def _auto_save_to_115(self, record: ResourceRecord, rule: ResourceMonitorRule):
        """自动转存到115"""
        try:
            from services.pan115_service import Pan115Service
            
            # 更新状态为"转存中"
            record.save_status = 'saving'
            await self.db.commit()
            
            # 执行转存
            pan115_service = Pan115Service(self.db)
            
            # 提取分享码
            import re
            match = re.search(r'/s/([a-zA-Z0-9]+)', record.link_url)
            if not match:
                raise ValueError("无法提取分享码")
            
            share_code = match.group(1)
            
            # 调用转存API
            result = await pan115_service.save_share(
                share_code=share_code,
                target_path=rule.target_path or "/",
                user_key=rule.pan115_user_key
            )
            
            # 更新记录
            record.save_status = 'success'
            record.save_path = rule.target_path
            record.save_time = datetime.now()
            await self.db.commit()
            
            logger.info(f"✅ 转存成功: {record.id}")
            
        except Exception as e:
            logger.error(f"转存失败: {e}", exc_info=True)
            
            # 更新失败状态
            record.save_status = 'failed'
            record.save_error = str(e)
            record.retry_count += 1
            await self.db.commit()
            
            # 加入重试队列
            from services.common.retry_queue import get_retry_queue
            retry_queue = get_retry_queue()
            await retry_queue.add_task('resource', {
                'record_id': record.id,
                'share_code': share_code,
                'target_path': rule.target_path
            }, e)
```

**关键点：**
- ✅ 完整的链接提取逻辑
- ✅ 关键词过滤和去重
- ✅ 自动转存到115
- ✅ 错误处理和重试
- ✅ 消息快照保存

#### 4.1.4 NotificationService（推送通知服务）

```python
# 文件：app/backend/services/notification_service.py
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from log_manager import get_logger
from database import get_db
from models import NotificationRule, NotificationLog

logger = get_logger("notification", "enhanced_bot.log")

class NotificationType(Enum):
    """通知类型"""
    DOWNLOAD_COMPLETE = "download_complete"      # 下载完成
    DOWNLOAD_FAILED = "download_failed"          # 下载失败
    RESOURCE_CAPTURED = "resource_captured"      # 资源捕获
    SAVE_115_SUCCESS = "save_115_success"        # 115转存成功
    SAVE_115_FAILED = "save_115_failed"          # 115转存失败
    TASK_STALE = "task_stale"                    # 任务卡住
    STORAGE_WARNING = "storage_warning"          # 存储空间警告
    DAILY_REPORT = "daily_report"                # 每日报告

class NotificationChannel(Enum):
    """通知渠道"""
    TELEGRAM = "telegram"        # Telegram消息
    WEB_PUSH = "web_push"        # Web推送
    EMAIL = "email"              # 邮件
    WEBHOOK = "webhook"          # Webhook

class NotificationService:
    """
    推送通知服务
    
    功能：
    1. 多渠道推送（Telegram/Web/Email/Webhook）
    2. 模板化消息
    3. 通知规则管理
    4. 通知历史记录
    5. 批量推送
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_engine = NotificationTemplateEngine()
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        channels: Optional[List[NotificationChannel]] = None,
        user_id: Optional[int] = None
    ):
        """
        发送通知
        
        Args:
            notification_type: 通知类型
            data: 通知数据
            channels: 通知渠道（None表示使用默认渠道）
            user_id: 用户ID（None表示发送给所有用户）
        """
        try:
            # 1. 获取通知规则
            rules = await self._get_applicable_rules(notification_type, user_id)
            if not rules:
                logger.debug(f"没有适用的通知规则: {notification_type.value}")
                return
            
            # 2. 生成通知内容
            message = self.template_engine.render(notification_type, data)
            
            # 3. 确定通知渠道
            if channels is None:
                channels = [NotificationChannel.TELEGRAM]  # 默认Telegram
            
            # 4. 发送到各个渠道
            for channel in channels:
                await self._send_to_channel(channel, message, data, rules)
            
            # 5. 记录通知历史
            await self._log_notification(notification_type, message, channels, user_id)
            
            logger.info(f"✅ 通知发送成功: {notification_type.value}")
            
        except Exception as e:
            logger.error(f"❌ 通知发送失败: {e}", exc_info=True)
    
    async def _get_applicable_rules(
        self, 
        notification_type: NotificationType, 
        user_id: Optional[int]
    ) -> List[NotificationRule]:
        """获取适用的通知规则"""
        query = select(NotificationRule).where(
            NotificationRule.is_active == True,
            NotificationRule.notification_type == notification_type.value
        )
        
        if user_id:
            query = query.where(NotificationRule.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _send_to_channel(
        self,
        channel: NotificationChannel,
        message: str,
        data: Dict[str, Any],
        rules: List[NotificationRule]
    ):
        """发送到指定渠道"""
        if channel == NotificationChannel.TELEGRAM:
            await self._send_telegram(message, data, rules)
        elif channel == NotificationChannel.WEB_PUSH:
            await self._send_web_push(message, data, rules)
        elif channel == NotificationChannel.EMAIL:
            await self._send_email(message, data, rules)
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook(message, data, rules)
    
    async def _send_telegram(
        self,
        message: str,
        data: Dict[str, Any],
        rules: List[NotificationRule]
    ):
        """发送Telegram通知"""
        from telegram_client_manager import get_client_manager
        
        for rule in rules:
            if not rule.telegram_chat_id:
                continue
            
            try:
                client_manager = get_client_manager()
                if client_manager and client_manager.connected:
                    # 使用MessageContext安全发送
                    await client_manager.send_notification(
                        chat_id=int(rule.telegram_chat_id),
                        message=message
                    )
                    logger.info(f"📱 Telegram通知已发送: {rule.telegram_chat_id}")
            except Exception as e:
                logger.error(f"Telegram通知发送失败: {e}")
    
    async def _send_web_push(
        self,
        message: str,
        data: Dict[str, Any],
        rules: List[NotificationRule]
    ):
        """发送Web推送通知"""
        # TODO: 实现Web Push通知
        logger.info("📲 Web推送通知（待实现）")
    
    async def _send_email(
        self,
        message: str,
        data: Dict[str, Any],
        rules: List[NotificationRule]
    ):
        """发送邮件通知"""
        # TODO: 实现邮件通知
        logger.info("📧 邮件通知（待实现）")
    
    async def _send_webhook(
        self,
        message: str,
        data: Dict[str, Any],
        rules: List[NotificationRule]
    ):
        """发送Webhook通知"""
        import aiohttp
        
        for rule in rules:
            if not rule.webhook_url:
                continue
            
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        'message': message,
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    }
                    async with session.post(rule.webhook_url, json=payload) as resp:
                        if resp.status == 200:
                            logger.info(f"🔗 Webhook通知已发送: {rule.webhook_url}")
                        else:
                            logger.error(f"Webhook通知失败: {resp.status}")
            except Exception as e:
                logger.error(f"Webhook通知发送失败: {e}")
    
    async def _log_notification(
        self,
        notification_type: NotificationType,
        message: str,
        channels: List[NotificationChannel],
        user_id: Optional[int]
    ):
        """记录通知历史"""
        log = NotificationLog(
            notification_type=notification_type.value,
            message=message,
            channels=','.join([c.value for c in channels]),
            user_id=user_id,
            sent_at=datetime.now()
        )
        self.db.add(log)
        await self.db.commit()

class NotificationTemplateEngine:
    """通知模板引擎"""
    
    TEMPLATES = {
        NotificationType.DOWNLOAD_COMPLETE: """
✅ 下载完成

文件名: {file_name}
大小: {file_size_mb}MB
用时: {duration}
归档路径: {final_path}
        """,
        
        NotificationType.DOWNLOAD_FAILED: """
❌ 下载失败

文件名: {file_name}
错误: {error_message}
重试次数: {retry_count}
        """,
        
        NotificationType.RESOURCE_CAPTURED: """
🔍 捕获到新资源

规则: {rule_name}
链接类型: {link_type}
链接: {link_url}
来源: {source_chat}
        """,
        
        NotificationType.SAVE_115_SUCCESS: """
⚡ 115转存成功

文件名: {file_name}
目标路径: {target_path}
是否秒传: {is_quick}
        """,
        
        NotificationType.SAVE_115_FAILED: """
❌ 115转存失败

文件名: {file_name}
错误: {error_message}
重试次数: {retry_count}
        """,
        
        NotificationType.TASK_STALE: """
⚠️ 任务异常

发现 {count} 个长时间未完成的任务
最长时间: {max_duration}
建议检查系统状态
        """,
        
        NotificationType.STORAGE_WARNING: """
⚠️ 存储空间警告

已用空间: {used_gb}GB
总空间: {total_gb}GB
使用率: {usage_percent}%
剩余空间: {remain_gb}GB
        """,
        
        NotificationType.DAILY_REPORT: """
📊 每日统计报告

日期: {date}

下载任务:
- 总计: {total_downloads}
- 成功: {success_downloads}
- 失败: {failed_downloads}

资源捕获:
- 总计: {total_resources}
- 已转存: {saved_resources}

存储使用:
- 本地: {local_storage_gb}GB
- 115: {pan115_storage_gb}GB
        """
    }
    
    def render(self, notification_type: NotificationType, data: Dict[str, Any]) -> str:
        """渲染通知消息"""
        template = self.TEMPLATES.get(notification_type, "{message}")
        
        try:
            return template.format(**data)
        except KeyError as e:
            logger.error(f"模板渲染失败，缺少字段: {e}")
            return f"通知: {notification_type.value}\n数据: {data}"

# 全局通知服务实例
_notification_service = None

async def get_notification_service() -> NotificationService:
    """获取通知服务实例"""
    global _notification_service
    if _notification_service is None:
        async for db in get_db():
            _notification_service = NotificationService(db)
            break
    return _notification_service
```

**使用示例：**

```python
# 在下载完成后发送通知
async def _execute_download(self, task_data: Dict[str, Any]):
    # ... 下载逻辑 ...
    
    # 下载成功，发送通知
    notification_service = await get_notification_service()
    await notification_service.send_notification(
        notification_type=NotificationType.DOWNLOAD_COMPLETE,
        data={
            'file_name': task_data['file_name'],
            'file_size_mb': file_size_mb,
            'duration': f"{duration:.1f}秒",
            'final_path': final_path
        },
        channels=[NotificationChannel.TELEGRAM, NotificationChannel.WEB_PUSH]
    )

# 在资源捕获后发送通知
async def _create_record(self, context, rule, link_type, link_url, link_hash):
    # ... 创建记录 ...
    
    # 发送通知
    notification_service = await get_notification_service()
    await notification_service.send_notification(
        notification_type=NotificationType.RESOURCE_CAPTURED,
        data={
            'rule_name': rule.name,
            'link_type': link_type,
            'link_url': link_url[:50] + '...',
            'source_chat': context.chat_id
        }
    )
```

**关键点：**
- ✅ 多渠道支持（Telegram/Web/Email/Webhook）
- ✅ 模板化消息，易于定制
- ✅ 通知规则管理，灵活控制
- ✅ 通知历史记录
- ✅ 异步非阻塞发送

### 4.2 数据流程图

#### 4.2.1 消息处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                  1. 消息接收                                 │
│  TelegramClientManager._process_message(event)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. 创建上下文                               │
│  context = MessageContext(                                  │
│      message=event.message,                                 │
│      client_manager=self,                                   │
│      chat_id=self._get_chat_id(message)                     │
│  )                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. 分发消息                                 │
│  results = await dispatcher.dispatch(context)               │
└─────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ForwardProcessor│ │ResourceProcessor│ │ MediaProcessor  │
│                 │ │                 │ │                 │
│ should_process()│ │ should_process()│ │ should_process()│
│       │         │ │       │         │ │       │         │
│       ▼         │ │       ▼         │ │       ▼         │
│   process()     │ │   process()     │ │   process()     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. 返回结果                                 │
│  {                                                          │
│    'ForwardProcessor': True,                                │
│    'ResourceProcessor': True,                               │
│    'MediaProcessor': False                                  │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

#### 4.2.2 资源监控流程

```
┌─────────────────────────────────────────────────────────────┐
│              1. ResourceProcessor.process()                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         2. 获取适用的规则                                     │
│  rules = await service.get_active_rules_for_chat(chat_id)  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         3. 提取链接（使用缓存）                               │
│  links = context.get_extracted_links()                      │
│  # 返回: {'pan115': [...], 'magnet': [...]}                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         4. 遍历规则                                          │
│  for rule in rules:                                         │
│      await service._process_rule(context, rule, links)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         5. 关键词过滤（使用缓存）                             │
│  matched = context.get_matched_keywords(keywords)           │
│  if not matched: return                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         6. 遍历链接                                          │
│  for link_type in link_types:                               │
│      for link_url in links[link_type]:                      │
│          await service._process_link(...)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         7. 去重检查                                          │
│  link_hash = calculate_hash(link_url)                       │
│  if is_duplicate(link_hash): return                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         8. 创建记录                                          │
│  record = ResourceRecord(...)                               │
│  db.add(record)                                             │
│  await db.commit()                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         9. 自动转存（如果启用）                               │
│  if rule.auto_save_to_115:                                  │
│      await service._auto_save_to_115(record, rule)          │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        ┌──────────┐               ┌──────────┐
        │ 转存成功 │               │ 转存失败 │
        │ status=  │               │ status=  │
        │ success  │               │ failed   │
        └──────────┘               └──────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │ 加入重试队列      │
                              │ retry_queue.add()│
                              └──────────────────┘
```

---

## 5. 实施步骤

### 5.1 阶段1详细步骤

#### Step 1.1: 创建数据模型（0.5天）

**文件：`app/backend/models.py`**

```python
# 在文件末尾添加以下模型

class ResourceMonitorRule(Base):
    """资源监控规则模型"""
    __tablename__ = 'resource_monitor_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='规则名称')
    source_chats = Column(Text, nullable=False, comment='源聊天列表(JSON)')
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 链接过滤
    link_types = Column(Text, comment='链接类型(JSON): ["pan115", "magnet", "ed2k"]')
    keywords = Column(Text, comment='关键词(JSON)')
    
    # 115配置
    auto_save_to_115 = Column(Boolean, default=False, comment='是否自动转存到115')
    target_path = Column(String(500), comment='目标路径')
    pan115_user_key = Column(String(100), comment='115用户密钥（可选）')
    
    # 标签
    default_tags = Column(Text, comment='默认标签(JSON)')
    
    # 去重
    enable_deduplication = Column(Boolean, default=True, comment='是否启用去重')
    dedup_time_window = Column(Integer, default=3600, comment='去重时间窗口(秒)')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    # 关系
    records = relationship("ResourceRecord", back_populates="rule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ResourceMonitorRule(id={self.id}, name='{self.name}')>"

class ResourceRecord(Base):
    """资源记录模型"""
    __tablename__ = 'resource_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('resource_monitor_rules.id'), nullable=False)
    rule_name = Column(String(100), comment='规则名称（冗余）')
    
    # 消息信息
    source_chat_id = Column(String(50), comment='源聊天ID')
    source_chat_name = Column(String(200), comment='源聊天名称')
    message_id = Column(Integer, comment='消息ID')
    message_text = Column(Text, comment='消息文本')
    message_date = Column(DateTime, comment='消息时间')
    
    # 链接信息
    link_type = Column(String(20), comment='链接类型')
    link_url = Column(Text, nullable=False, comment='链接URL')
    link_hash = Column(String(64), index=True, comment='链接哈希（用于去重）')
    
    # 115转存信息
    save_status = Column(String(20), default='pending', comment='转存状态')
    save_path = Column(String(500), comment='转存路径')
    save_error = Column(Text, comment='转存错误信息')
    save_time = Column(DateTime, comment='转存时间')
    retry_count = Column(Integer, default=0, comment='重试次数')
    
    # 标签
    tags = Column(Text, comment='标签(JSON)')
    
    # 消息快照
    message_snapshot = Column(Text, comment='消息快照(JSON)')
    
    # 时间戳
    created_at = Column(DateTime, default=get_local_now, comment='创建时间')
    updated_at = Column(DateTime, default=get_local_now, onupdate=get_local_now, comment='更新时间')
    
    # 关系
    rule = relationship("ResourceMonitorRule", back_populates="records")
    
    def __repr__(self):
        return f"<ResourceRecord(id={self.id}, link_type='{self.link_type}', status='{self.save_status}')>"
```

**测试：**
```bash
# 检查模型定义
python -c "from app.backend.models import ResourceMonitorRule, ResourceRecord; print('✅ 模型定义正确')"
```

#### Step 1.2: 创建数据库迁移（0.5天）

**文件：`app/backend/alembic/versions/20250112_add_resource_monitor.py`**

```python
"""add resource monitor tables

Revision ID: 20250112_add_resource_monitor
Revises: <上一个迁移ID>
Create Date: 2025-01-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250112_add_resource_monitor'
down_revision = '<上一个迁移ID>'  # 需要填写
branch_labels = None
depends_on = None

def upgrade():
    # 创建 resource_monitor_rules 表
    op.create_table(
        'resource_monitor_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('source_chats', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('link_types', sa.Text()),
        sa.Column('keywords', sa.Text()),
        sa.Column('auto_save_to_115', sa.Boolean(), default=False),
        sa.Column('target_path', sa.String(length=500)),
        sa.Column('pan115_user_key', sa.String(length=100)),
        sa.Column('default_tags', sa.Text()),
        sa.Column('enable_deduplication', sa.Boolean(), default=True),
        sa.Column('dedup_time_window', sa.Integer(), default=3600),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建 resource_records 表
    op.create_table(
        'resource_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=100)),
        sa.Column('source_chat_id', sa.String(length=50)),
        sa.Column('source_chat_name', sa.String(length=200)),
        sa.Column('message_id', sa.Integer()),
        sa.Column('message_text', sa.Text()),
        sa.Column('message_date', sa.DateTime()),
        sa.Column('link_type', sa.String(length=20)),
        sa.Column('link_url', sa.Text(), nullable=False),
        sa.Column('link_hash', sa.String(length=64)),
        sa.Column('save_status', sa.String(length=20), default='pending'),
        sa.Column('save_path', sa.String(length=500)),
        sa.Column('save_error', sa.Text()),
        sa.Column('save_time', sa.DateTime()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('tags', sa.Text()),
        sa.Column('message_snapshot', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rule_id'], ['resource_monitor_rules.id'], ondelete='CASCADE')
    )
    
    # 创建索引
    op.create_index('idx_resource_records_link_hash', 'resource_records', ['link_hash'])
    op.create_index('idx_resource_records_save_status', 'resource_records', ['save_status'])
    op.create_index('idx_resource_records_created_at', 'resource_records', ['created_at'])

def downgrade():
    op.drop_index('idx_resource_records_created_at', table_name='resource_records')
    op.drop_index('idx_resource_records_save_status', table_name='resource_records')
    op.drop_index('idx_resource_records_link_hash', table_name='resource_records')
    op.drop_table('resource_records')
    op.drop_table('resource_monitor_rules')
```

**执行迁移：**
```bash
cd app/backend
alembic upgrade head
```

**测试：**
```bash
# 检查表是否创建成功
sqlite3 data/bot.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'resource%';"
```

#### Step 1.3-1.7: 创建服务和API

由于篇幅限制，完整代码已在前面的章节中给出。

---

## 6. 测试方案

### 6.1 单元测试

**文件：`tests/test_resource_monitor.py`**

```python
import pytest
from app.backend.services.resource_monitor_service import LinkExtractor, ResourceMonitorService
from app.backend.models import ResourceMonitorRule, ResourceRecord

class TestLinkExtractor:
    """链接提取器测试"""
    
    def test_extract_pan115_link(self):
        """测试提取115链接"""
        text = "这是一个115链接: https://115.com/s/abc123?password=xyz"
        links = LinkExtractor.extract_all(text)
        
        assert 'pan115' in links
        assert len(links['pan115']) == 1
        assert 'abc123' in links['pan115'][0]
    
    def test_extract_magnet_link(self):
        """测试提取磁力链接"""
        text = "磁力链接: magnet:?xt=urn:btih:abcd1234567890abcd1234567890abcd12345678"
        links = LinkExtractor.extract_all(text)
        
        assert 'magnet' in links
        assert len(links['magnet']) == 1
    
    def test_extract_multiple_links(self):
        """测试提取多个链接"""
        text = """
        115链接: https://115.com/s/abc123
        磁力链接: magnet:?xt=urn:btih:abcd1234567890abcd1234567890abcd12345678
        ed2k链接: ed2k://|file|test.mkv|1234567890|ABCD1234567890ABCD1234567890AB|/
        """
        links = LinkExtractor.extract_all(text)
        
        assert 'pan115' in links
        assert 'magnet' in links
        assert 'ed2k' in links

@pytest.mark.asyncio
class TestResourceMonitorService:
    """资源监控服务测试"""
    
    async def test_create_record(self, db_session):
        """测试创建资源记录"""
        # TODO: 实现测试
        pass
    
    async def test_deduplication(self, db_session):
        """测试去重功能"""
        # TODO: 实现测试
        pass
```

### 6.2 集成测试

**测试场景：**

1. **消息接收测试**
   - 发送包含115链接的消息
   - 验证是否创建了资源记录

2. **关键词过滤测试**
   - 创建带关键词的规则
   - 发送匹配/不匹配的消息
   - 验证过滤结果

3. **去重测试**
   - 发送相同链接的消息
   - 验证只创建一条记录

4. **自动转存测试**
   - 创建启用自动转存的规则
   - 发送115链接
   - 验证转存状态

### 6.3 性能测试

**测试指标：**

| 指标 | 目标值 | 测试方法 |
|------|--------|---------|
| 消息处理延迟 | < 100ms | 发送100条消息，计算平均延迟 |
| 链接提取速度 | < 10ms | 提取包含10个链接的消息 |
| 数据库写入速度 | < 50ms | 批量写入100条记录 |
| 缓存命中率 | > 80% | 重复发送相同消息 |

---

## 7. 部署方案

### 7.1 部署前检查

```bash
# 1. 检查代码
git status
git diff

# 2. 运行测试
pytest tests/

# 3. 检查数据库迁移
cd app/backend
alembic current
alembic upgrade head

# 4. 检查依赖
pip list | grep -E "telethon|sqlalchemy|fastapi"
```

### 7.2 部署步骤

#### 本地开发环境

```bash
# 1. 停止服务
docker-compose down

# 2. 清理数据（可选）
# rm -rf data/ logs/ sessions/

# 3. 重新构建
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 查看日志
docker-compose logs -f backend
```

#### 生产环境

```bash
# 1. 备份数据库
cp data/bot.db data/bot.db.backup.$(date +%Y%m%d_%H%M%S)

# 2. 拉取代码
git pull origin main

# 3. 执行迁移
docker-compose exec backend alembic upgrade head

# 4. 重启服务
docker-compose restart backend

# 5. 验证服务
curl http://localhost:9393/api/health
```

### 7.3 回滚方案

```bash
# 1. 停止服务
docker-compose down

# 2. 回滚代码
git checkout <上一个稳定版本>

# 3. 回滚数据库
docker-compose exec backend alembic downgrade -1

# 4. 恢复数据库（如果需要）
cp data/bot.db.backup.<timestamp> data/bot.db

# 5. 重启服务
docker-compose up -d
```

---

## 8. 115Bot借鉴与优化

> 基于 `115BOT_ANALYSIS.md` 和 `VIDEO_TRANSFER_COMPARISON.md` 的深度分析

### 8.1 核心借鉴点

#### 8.1.1 任务调度系统 ⭐⭐⭐⭐⭐

**115Bot的实现：**
- 定时轮询离线任务状态（每5分钟）
- 自动清理临时文件（每天凌晨2点）
- 订阅更新检查（每天早上8点）

**TMC可借鉴：**

```python
# 文件：app/backend/services/task_scheduler.py (新建)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class TaskScheduler:
    """任务调度器 - 借鉴115Bot"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """启动调度器"""
        # 1. 每5分钟检查下载任务状态
        self.scheduler.add_job(
            self.check_download_tasks,
            trigger=IntervalTrigger(minutes=5),
            id='check_download_tasks',
            name='检查下载任务状态'
        )
        
        # 2. 每天凌晨2点清理临时文件
        self.scheduler.add_job(
            self.cleanup_temp_files,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_temp_files',
            name='清理临时文件'
        )
        
        # 3. 每小时检查存储空间
        self.scheduler.add_job(
            self.check_storage_space,
            trigger=IntervalTrigger(hours=1),
            id='check_storage_space',
            name='检查存储空间'
        )
        
        # 4. 每天早上8点生成统计报告
        self.scheduler.add_job(
            self.generate_daily_report,
            trigger=CronTrigger(hour=8, minute=0),
            id='generate_daily_report',
            name='生成每日报告'
        )
        
        self.scheduler.start()
        logger.info("任务调度器已启动")
    
    async def check_download_tasks(self):
        """检查下载任务状态（类似115Bot的离线任务轮询）"""
        async for db in get_db():
            # 查找长时间未完成的任务
            stale_tasks = await db.execute(
                select(DownloadTask).where(
                    DownloadTask.status == 'downloading',
                    DownloadTask.started_at < datetime.now() - timedelta(hours=2)
                )
            )
            
            for task in stale_tasks.scalars():
                logger.warning(f"发现卡住的任务: {task.file_name}")
                # 重置状态，重新下载
                task.status = 'pending'
                task.retry_count += 1
            
            await db.commit()
            break
    
    async def cleanup_temp_files(self):
        """清理临时文件（借鉴115Bot）"""
        async for db in get_db():
            settings = await db.execute(select(MediaSettings))
            settings = settings.scalar_one_or_none()
            
            if not settings or not settings.auto_cleanup_enabled:
                return
            
            # 查找过期的临时文件
            cutoff_date = datetime.now() - timedelta(days=settings.auto_cleanup_days)
            
            old_files = await db.execute(
                select(MediaFile).where(
                    MediaFile.temp_path.isnot(None),
                    MediaFile.downloaded_at < cutoff_date
                )
            )
            
            for media_file in old_files.scalars():
                # 只清理已归档的文件
                if settings.cleanup_only_organized and not media_file.is_organized:
                    continue
                
                # 删除临时文件
                if os.path.exists(media_file.temp_path):
                    os.remove(media_file.temp_path)
                    logger.info(f"清理临时文件: {media_file.temp_path}")
                
                media_file.temp_path = None
            
            await db.commit()
            break
```

**优势：**
- ✅ 自动化运维，减少人工干预
- ✅ 及时发现和处理异常任务
- ✅ 自动清理，节省存储空间
- ✅ 定期统计，了解系统状态

**工作量：** 2-3天

---

#### 8.1.2 智能文件过滤 ⭐⭐⭐⭐

**115Bot的实现：**
- 广告文件识别（www.、.url、广告、sample等）
- 文件大小过滤（视频至少1MB）
- 扩展名过滤

**TMC可借鉴：**

```python
# 文件：app/backend/utils/media_filters.py (新建)

class AdvancedMediaFilter:
    """高级媒体过滤器 - 借鉴115Bot"""
    
    # 广告文件特征库
    AD_PATTERNS = [
        r'www\.',
        r'\.url$',
        r'\.txt$',
        r'\.nfo$',
        r'广告',
        r'推广',
        r'sample',
        r'预览',
        r'@',  # 常见于广告文件名
        r'点击',
        r'访问',
    ]
    
    # 最小文件大小（MB）
    MIN_VIDEO_SIZE = 1    # 视频至少1MB
    MIN_AUDIO_SIZE = 0.1  # 音频至少100KB
    MIN_IMAGE_SIZE = 0.01 # 图片至少10KB
    
    @classmethod
    def is_ad_file(cls, filename: str) -> bool:
        """判断是否为广告文件"""
        filename_lower = filename.lower()
        for pattern in cls.AD_PATTERNS:
            if re.search(pattern, filename_lower):
                logger.info(f"检测到广告文件: {filename}")
                return True
        return False
    
    @classmethod
    def is_valid_media(cls, file_type: str, file_size_mb: float) -> bool:
        """判断是否为有效媒体文件"""
        if file_type == 'video' and file_size_mb < cls.MIN_VIDEO_SIZE:
            logger.info(f"视频文件过小: {file_size_mb}MB")
            return False
        if file_type == 'audio' and file_size_mb < cls.MIN_AUDIO_SIZE:
            logger.info(f"音频文件过小: {file_size_mb}MB")
            return False
        if file_type == 'image' and file_size_mb < cls.MIN_IMAGE_SIZE:
            logger.info(f"图片文件过小: {file_size_mb}MB")
            return False
        return True
    
    @classmethod
    def extract_video_info(cls, filename: str) -> Dict[str, str]:
        """从文件名提取视频信息（借鉴115Bot）"""
        info = {}
        
        # 提取分辨率
        resolution_patterns = [
            r'(\d{3,4}[xX×]\d{3,4})',  # 1920x1080
            r'(4K|2K|1080[pP]|720[pP]|480[pP])',
        ]
        for pattern in resolution_patterns:
            match = re.search(pattern, filename)
            if match:
                info['resolution'] = match.group(1)
                break
        
        # 提取画质
        quality_patterns = [
            r'(BluRay|Blu-ray|REMUX|WEB-DL|WEBRip|HDRip|BDRip)',
        ]
        for pattern in quality_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                info['quality'] = match.group(1)
                break
        
        # 提取编码
        codec_patterns = [
            r'(H\.?264|H\.?265|HEVC|x264|x265|AVC)',
        ]
        for pattern in codec_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                info['codec'] = match.group(1)
                break
        
        return info
```

**集成到媒体监控：**

```python
# 修改：app/backend/services/media_monitor_service.py

async def _execute_download(self, task_data: Dict[str, Any]):
    """执行下载任务（增强过滤）"""
    # ... 现有下载逻辑 ...
    
    # 下载完成后，应用高级过滤
    from utils.media_filters import AdvancedMediaFilter
    
    # 1. 检查是否为广告文件
    if AdvancedMediaFilter.is_ad_file(task_data['file_name']):
        logger.info(f"过滤广告文件: {task_data['file_name']}")
        # 删除已下载的文件
        if file_path.exists():
            os.remove(file_path)
        # 更新任务状态为"已忽略"
        task.status = 'ignored'
        task.error_message = '广告文件已过滤'
        await db.commit()
        return
    
    # 2. 检查文件大小
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    if not AdvancedMediaFilter.is_valid_media(task_data['file_type'], file_size_mb):
        logger.info(f"文件大小不符合要求: {file_size_mb}MB")
        os.remove(file_path)
        task.status = 'ignored'
        task.error_message = '文件大小不符合要求'
        await db.commit()
        return
    
    # 3. 提取视频信息
    video_info = AdvancedMediaFilter.extract_video_info(task_data['file_name'])
    metadata_dict.update(video_info)
    
    # ... 继续后续处理 ...
```

**优势：**
- ✅ 自动过滤无用文件，节省存储和带宽
- ✅ 提取文件名中的元数据，丰富文件信息
- ✅ 提升用户体验，避免下载垃圾文件

**工作量：** 1-2天

---

#### 8.1.3 115秒传优化 ⭐⭐⭐⭐⭐

**问题：** TMC目前没有在上传前检查115网盘是否已有相同文件

**115Bot的做法：**
```python
# 上传前检查秒传
file_hash = calculate_sha1(file_path)
quick_result = await pan115_client.check_quick_upload(file_hash)

if quick_result['exists']:
    logger.info("文件已存在，秒传成功")
    return quick_result['pickcode']
else:
    # 正常上传
    await pan115_client.upload_file(file_path)
```

**TMC优化方案：**

```python
# 文件：app/backend/services/p115_service.py (修改)

async def upload_file_with_quick_check(
    self, 
    cookies: str,
    file_path: str,
    target_dir: str = "/",
    file_name: Optional[str] = None
) -> Dict[str, Any]:
    """上传文件（支持秒传检测）- 借鉴115Bot"""
    
    # 1. 计算文件SHA1
    file_sha1 = await self._calculate_sha1_async(file_path)
    logger.info(f"文件SHA1: {file_sha1}")
    
    # 2. 检查秒传
    loop = asyncio.get_event_loop()
    
    def _check_quick():
        client = P115Client(cookies)
        # 使用115的秒传检查API
        # 只读取前128KB进行检查，节省时间
        result = client.upload_file_sample(
            file_path,
            read_range=slice(0, 128 * 1024)
        )
        return result
    
    quick_result = await loop.run_in_executor(None, _check_quick)
    
    # 3. 如果可以秒传
    if quick_result.get('status') == 2:
        logger.info(f"⚡ 秒传成功: {file_name}")
        return {
            "success": True,
            "pickcode": quick_result.get('pickcode'),
            "file_name": file_name,
            "is_quick": True,
            "message": "秒传成功，节省上传时间"
        }
    
    # 4. 正常上传
    logger.info(f"秒传不可用，开始正常上传: {file_name}")
    return await self.upload_file(cookies, file_path, target_dir, file_name)

@staticmethod
async def _calculate_sha1_async(file_path: str) -> str:
    """异步计算文件SHA1"""
    import hashlib
    
    def _calc():
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha1.update(chunk)
        return sha1.hexdigest()
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _calc)
```

**收益对比：**

| 场景 | 普通上传 | 秒传 | 节省时间 |
|------|---------|------|---------|
| 100MB文件 | 2-3分钟 | 3-5秒 | **95%** |
| 1GB文件 | 15-20分钟 | 3-5秒 | **98%** |
| 10GB文件 | 2-3小时 | 3-5秒 | **99%** |

**工作量：** 1-2天

---

#### 8.1.4 优先级队列 ⭐⭐⭐

**115Bot的实现：**
- 支持任务优先级
- 高优先级任务优先处理
- 用户可手动调整优先级

**TMC优化方案：**

```python
# 文件：app/backend/services/media_monitor_service.py (修改)

import heapq
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class PriorityTask:
    """优先级任务"""
    priority: int  # 数字越小优先级越高
    task_data: Any = field(compare=False)

class EnhancedMediaMonitorService(MediaMonitorService):
    """增强的媒体监控服务 - 支持优先级队列"""
    
    def __init__(self):
        super().__init__()
        self.priority_queue = []  # 优先级队列
        self.queue_lock = asyncio.Lock()
    
    async def add_download_task_with_priority(
        self, 
        task_data: Dict, 
        priority: int = 5  # 默认优先级5（0最高，9最低）
    ):
        """添加带优先级的下载任务"""
        async with self.queue_lock:
            heapq.heappush(
                self.priority_queue,
                PriorityTask(priority=priority, task_data=task_data)
            )
            logger.info(f"添加优先级任务: priority={priority}, file={task_data['file_name']}")
    
    async def _download_worker(self, worker_id: int):
        """下载工作线程（支持优先级）"""
        logger.info(f"👷 下载工作线程 #{worker_id+1} 已启动")
        
        while self.is_running:
            try:
                # 优先从优先级队列获取
                task = None
                async with self.queue_lock:
                    if self.priority_queue:
                        priority_task = heapq.heappop(self.priority_queue)
                        task = priority_task.task_data
                        logger.info(f"[Worker #{worker_id+1}] 处理优先级任务: priority={priority_task.priority}")
                
                # 如果优先级队列为空，从普通队列获取
                if not task:
                    task = await asyncio.wait_for(
                        self.download_queue.get(),
                        timeout=1.0
                    )
                
                logger.info(f"[Worker #{worker_id+1}] 开始下载: {task['file_name']}")
                
                # 执行下载
                await self._execute_download(task)
                
                # 标记任务完成
                if not task.get('from_priority_queue'):
                    self.download_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[Worker #{worker_id+1}] 下载任务失败: {e}")
```

**前端支持：**

```typescript
// 文件：app/frontend/src/pages/MediaMonitor/RecordList.tsx (修改)

// 添加优先级调整功能
const handleSetPriority = async (taskId: number, priority: number) => {
  try {
    await mediaMonitorApi.setTaskPriority(taskId, priority);
    message.success('优先级已更新');
    fetchTasks();
  } catch (error) {
    message.error('优先级更新失败');
  }
};

// 在表格中添加优先级列
{
  title: '优先级',
  dataIndex: 'priority',
  key: 'priority',
  render: (priority: number, record: DownloadTask) => (
    <Select
      value={priority}
      onChange={(value) => handleSetPriority(record.id, value)}
      style={{ width: 80 }}
    >
      <Option value={0}>🔴 紧急</Option>
      <Option value={3}>🟡 高</Option>
      <Option value={5}>🟢 普通</Option>
      <Option value={7}>🔵 低</Option>
    </Select>
  ),
}
```

**优势：**
- ✅ 重要任务优先处理
- ✅ 用户可手动调整
- ✅ 提升用户体验

**工作量：** 2-3天

---

#### 8.1.5 批量操作 ⭐⭐⭐⭐

**115Bot的实现：**
- 批量添加离线任务
- 批量解压文件
- 批量生成STRM

**TMC优化方案：**

```python
# 文件：app/backend/api/routes/media_monitor.py (新增)

@router.post("/batch-operations")
async def batch_operations(
    operation: str,  # download/organize/upload/retry
    task_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """批量操作（借鉴115Bot）"""
    
    if operation == 'download':
        # 批量重新下载
        for task_id in task_ids:
            task = await db.get(DownloadTask, task_id)
            if task:
                task.status = 'pending'
                task.retry_count = 0
                task.error_message = None
        await db.commit()
        return {"success": True, "message": f"已重新启动{len(task_ids)}个下载任务"}
    
    elif operation == 'organize':
        # 批量重新归档
        for task_id in task_ids:
            media_file = await db.execute(
                select(MediaFile).where(MediaFile.download_task_id == task_id)
            )
            media_file = media_file.scalar_one_or_none()
            if media_file and media_file.temp_path:
                # 重新归档
                from services.media_monitor_service import FileOrganizer
                await FileOrganizer.organize_file(
                    rule, 
                    media_file.temp_path, 
                    metadata
                )
        await db.commit()
        return {"success": True, "message": f"已重新归档{len(task_ids)}个文件"}
    
    elif operation == 'upload':
        # 批量上传到115
        from services.p115_service import Pan115Service
        p115_service = Pan115Service(db)
        
        success_count = 0
        for task_id in task_ids:
            media_file = await db.execute(
                select(MediaFile).where(MediaFile.download_task_id == task_id)
            )
            media_file = media_file.scalar_one_or_none()
            if media_file and (media_file.temp_path or media_file.final_path):
                try:
                    source_file = media_file.final_path or media_file.temp_path
                    await p115_service.upload_file_with_quick_check(
                        cookies, 
                        source_file, 
                        target_dir
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"上传失败: {e}")
        
        await db.commit()
        return {
            "success": True, 
            "message": f"成功上传{success_count}/{len(task_ids)}个文件到115网盘"
        }
    
    elif operation == 'retry':
        # 批量重试失败任务
        for task_id in task_ids:
            task = await db.get(DownloadTask, task_id)
            if task and task.status == 'failed':
                task.status = 'pending'
                task.retry_count = 0
        await db.commit()
        return {"success": True, "message": f"已重试{len(task_ids)}个失败任务"}
```

**工作量：** 1-2天

---

### 8.2 TMC独特优势保持

| 功能 | TMC独有 | 说明 |
|------|---------|------|
| Web管理界面 | ✅ | 115Bot只有Telegram交互 |
| 多客户端管理 | ✅ | 支持多个Telegram账号 |
| 消息转发 | ✅ | 115Bot不支持 |
| 用户权限系统 | ✅ | 更完善的权限管理 |
| 元数据提取 | ✅ | 更详细的视频元数据 |
| 数据库管理 | ✅ | 完整的关系型数据库 |
| API接口 | ✅ | RESTful API |
| 实时进度跟踪 | ✅ | 115Bot无实时进度 |
| 完整的任务管理 | ✅ | 数据库记录所有任务 |

---

### 8.3 优化实施路线图

```
阶段5（第3周）：115Bot借鉴功能
├─ Day 1-2: 115秒传优化（最高ROI）
├─ Day 3: 智能文件过滤
├─ Day 4: 任务调度系统
└─ Day 5: 优先级队列 + 批量操作

阶段6（第4周）：高级功能
├─ Day 1-2: 进度通知优化
├─ Day 3: 批量上传优化
└─ Day 4-5: 完整测试和文档

预期收益：
├─ 上传速度提升: 50-70%（秒传）
├─ 存储节省: 30-50%（过滤）
├─ 自动化程度: +70%（调度）
└─ 用户体验: +40%（优先级+批量）
```

---

### 8.4 关键优化对比

| 优化项 | 优先级 | 工作量 | 预期收益 | 实施建议 |
|--------|--------|--------|---------|---------|
| **115秒传检测** | ⭐⭐⭐⭐⭐ | 1-2天 | 节省90%上传时间 | 立即实施 |
| **任务调度系统** | ⭐⭐⭐⭐ | 2-3天 | 自动化+70% | 第二批 |
| **智能文件过滤** | ⭐⭐⭐⭐ | 1-2天 | 节省30%存储 | 第二批 |
| **批量上传** | ⭐⭐⭐⭐ | 2-3天 | 提升60%效率 | 第二批 |
| **优先级队列** | ⭐⭐⭐ | 2-3天 | 用户体验+40% | 第三批 |
| **批量操作** | ⭐⭐⭐ | 1-2天 | 操作效率+50% | 第三批 |

---

## 9. 附录

### 9.1 文件清单

#### 新建文件（混合架构核心）

```
app/backend/
├── services/
│   ├── message_context.py              (新建，200行) - 消息上下文
│   ├── message_dispatcher.py           (新建，300行) - 消息分发器
│   ├── resource_monitor_service.py     (新建，800行) - 资源监控服务
│   ├── task_scheduler.py               (新建，400行) - 任务调度器 [115Bot借鉴]
│   ├── notification_service.py         (新建，400行) - 推送通知服务 ⭐ 新增
│   ├── notification_templates.py       (新建，200行) - 通知模板引擎 ⭐ 新增
│   └── common/
│       ├── __init__.py                 (新建)
│       ├── message_cache.py            (新建，300行) - 消息缓存
│       ├── filter_engine.py            (新建，200行) - 共享过滤引擎
│       ├── retry_queue.py              (新建，400行) - 智能重试队列
│       └── batch_writer.py             (新建，300行) - 批量数据库写入
├── utils/
│   └── media_filters.py                (新建，300行) - 高级媒体过滤器 [115Bot借鉴]
├── api/routes/
│   ├── resource_monitor.py             (新建，400行) - 资源监控API
│   └── notifications.py                (新建，300行) - 通知管理API ⭐ 新增
└── alembic/versions/
    ├── 20250112_add_resource_monitor.py (新建，100行) - 数据库迁移
    └── 20250112_add_notifications.py    (新建，80行) - 通知表迁移 ⭐ 新增

app/frontend/src/
├── pages/ResourceMonitor/
│   ├── index.tsx                       (新建，100行) - 主页面
│   ├── RuleList.tsx                    (新建，400行) - 规则列表
│   ├── RuleForm.tsx                    (新建，600行) - 规则表单
│   ├── RecordList.tsx                  (新建，800行) - 记录列表
│   └── QuickWizard.tsx                 (新建，300行) - 快捷向导
├── components/
│   ├── NotificationCenter.tsx          (新建，500行) - 通知中心 ⭐ 新增
│   └── NotificationSettings.tsx        (新建，400行) - 通知设置 ⭐ 新增
├── services/
│   ├── resourceMonitor.ts              (新建，200行) - API服务
│   └── notifications.ts                (新建，150行) - 通知API服务 ⭐ 新增
└── types/
    ├── resourceMonitor.ts              (新建，100行) - 类型定义
    └── notifications.ts                (新建，80行) - 通知类型定义 ⭐ 新增

docs/
├── HYBRID_ARCHITECTURE_DEVELOPMENT.md  (本文档)
├── 115BOT_ANALYSIS.md                  (参考文档)
└── VIDEO_TRANSFER_COMPARISON.md        (参考文档)

总计：约 8,010 行新代码（含115Bot借鉴 + 推送通知）
```

#### 修改文件

```
app/backend/
├── models.py                           (新增 2个模型，约100行)
├── telegram_client_manager.py          (修改 _process_message，约50行)
├── services/media_monitor_service.py   (新增过滤和优先级，约150行) [115Bot借鉴]
├── services/p115_service.py            (新增秒传检测，约100行) [115Bot借鉴]
├── api/routes/media_monitor.py         (新增批量操作，约80行) [115Bot借鉴]
└── api/routes/__init__.py              (新增 1个路由导入，1行)

app/frontend/src/
├── routes.tsx                          (新增路由配置，约10行)
└── pages/MediaMonitor/RecordList.tsx   (新增优先级列，约30行) [115Bot借鉴]

总计：约 520 行修改（含115Bot借鉴优化）
```

### 9.2 依赖清单

**Python依赖（已有）：**
- telethon >= 1.24.0
- sqlalchemy >= 2.0.0
- fastapi >= 0.100.0
- alembic >= 1.11.0

**Python依赖（新增）：**
- apscheduler >= 3.10.0  # 任务调度器 [115Bot借鉴]

**前端依赖（已有）：**
- react >= 18.0.0
- antd >= 5.0.0
- axios >= 1.0.0

**无需其他新增依赖**

### 9.3 配置清单

**环境变量（无需新增）：**
- 使用现有的数据库配置
- 使用现有的115配置

**数据库迁移：**
- 1个新迁移文件
- 2个新表（resource_monitor_rules, resource_records）
- 3个新索引

**任务调度配置（新增）：** [115Bot借鉴]
```python
# config/scheduler.py
SCHEDULER_CONFIG = {
    'check_download_tasks': {
        'interval': 5,  # 分钟
        'enabled': True
    },
    'cleanup_temp_files': {
        'cron': '0 2 * * *',  # 每天凌晨2点
        'enabled': True
    },
    'check_storage_space': {
        'interval': 60,  # 分钟
        'enabled': True
    },
    'generate_daily_report': {
        'cron': '0 8 * * *',  # 每天早上8点
        'enabled': False  # 默认关闭
    }
}
```

### 9.4 性能指标

**预期性能提升（混合架构）：**

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 消息处理延迟 | 200ms | 70ms | 2.9x |
| 数据库写入 | 100次/秒 | 20次/秒 | 5x |
| 缓存命中率 | 0% | 85% | ∞ |
| 重试成功率 | 40% | 90% | 2.25x |

**预期性能提升（115Bot借鉴）：**

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 115上传速度（秒传） | 100% | 5% | **95%节省** |
| 存储空间占用（过滤） | 100% | 70% | **30%节省** |
| 任务处理效率（优先级） | 100% | 160% | **60%提升** |
| 操作效率（批量） | 100% | 200% | **100%提升** |
| 自动化程度（调度） | 30% | 100% | **70%提升** |

**资源占用：**

| 资源 | 增加量 | 说明 |
|------|--------|------|
| 内存 | +70MB | 消息缓存 + 任务调度器 |
| 磁盘 | +100MB/万条记录 | 资源记录 |
| CPU | +8% | 链接提取、过滤、SHA1计算 |

---

## 10. 总结

### 10.1 核心优势

#### 混合架构优势
1. **最小化改动**：保留现有代码，只新增功能
2. **性能提升**：通过缓存和批量处理提升3-5倍性能
3. **易于扩展**：统一的处理器接口，易于添加新功能
4. **向后兼容**：不破坏现有功能
5. **可观测性**：完善的监控和日志

#### 115Bot借鉴优势
1. **秒传优化**：节省90%以上上传时间
2. **智能过滤**：节省30%存储空间，避免垃圾文件
3. **任务调度**：自动化程度提升70%
4. **优先级队列**：重要任务优先处理
5. **批量操作**：操作效率提升100%

### 10.2 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 事件循环问题 | 高 | MessageContext封装，自动处理 |
| 数据库迁移失败 | 中 | 完整的回滚方案 |
| 性能下降 | 中 | 缓存和批量处理 |
| 115限流 | 中 | 智能重试队列 + 秒传优化 |
| SHA1计算耗时 | 低 | 异步计算，不阻塞主流程 |

### 10.3 完整开发路线图

```
第1-2周：混合架构核心（阶段1-4）
├─ 数据模型和消息分发器
├─ 资源监控服务
├─ 性能优化（缓存、批量、重试）
└─ 前端界面和监控面板

第3周：推送通知 + 测试（阶段5）⭐ 新增
├─ 推送通知服务核心
├─ 通知模板引擎
├─ 多渠道支持（Telegram/Web/Email/Webhook）
├─ 前端通知中心
└─ 完整测试和优化

第4周：115Bot借鉴功能（阶段6）
├─ 115秒传优化（最高优先级）
├─ 智能文件过滤
├─ 任务调度系统
└─ 优先级队列 + 批量操作

第5周：高级功能和部署（阶段7）
├─ 进度通知优化
├─ 批量上传优化
├─ 完整测试
└─ 文档完善和部署

预期总收益：
├─ 开发时间：4-5周
├─ 新增代码：约8,010行（含推送通知）
├─ 修改代码：约520行
├─ 性能提升：3-5倍（混合架构）+ 50-95%（115Bot优化）
├─ 自动化程度：+70%
├─ 用户体验：+50%（含推送通知）
└─ 通知及时性：实时推送
```

### 10.4 关键里程碑

| 里程碑 | 时间 | 交付内容 | 验收标准 |
|--------|------|---------|---------|
| **M1：核心架构** | Week 1 | 消息分发器 + 资源监控MVP | 能创建规则并捕获链接 |
| **M2：性能优化** | Week 2 | 缓存 + 批量 + 重试 + 前端 | 性能提升3倍以上 |
| **M3：推送通知** ⭐ | Week 3 | 通知服务 + 多渠道 + 前端 | 实时推送正常工作 |
| **M4：115优化** | Week 4 | 秒传 + 过滤 + 调度 + 批量 | 上传速度提升50%以上 |
| **M5：完整交付** | Week 5 | 测试 + 文档 + 部署 | 所有功能测试通过 |

---

**文档版本：** v2.1 ⭐ 新增推送通知系统  
**创建日期：** 2025-01-12  
**最后更新：** 2025-01-14  
**作者：** AI Assistant  
**审核状态：** 待审核  
**参考文档：** 115BOT_ANALYSIS.md, VIDEO_TRANSFER_COMPARISON.md

**v2.1 更新内容：**
- ✅ 新增阶段5：推送通知系统（P1，2-3天）
- ✅ 新增 NotificationService 和 NotificationTemplateEngine 设计
- ✅ 新增 notification_rules 和 notification_logs 数据表
- ✅ 新增通知中心和通知设置前端组件
- ✅ 支持多渠道推送（Telegram/Web/Email/Webhook）
- ✅ 支持8种通知类型（下载完成、资源捕获、115转存等）
- ✅ 更新开发路线图：4-5周完成
- ✅ 更新代码量：约8,010行（含推送通知）

---

## 11. 快速开始

### 11.1 阶段1：核心架构（第1周）

```bash
# 1. 创建分支
git checkout -b feature/hybrid-architecture

# 2. 创建数据模型
# 编辑 app/backend/models.py
# 添加 ResourceMonitorRule 和 ResourceRecord 模型

# 3. 创建数据库迁移
cd app/backend
alembic revision --autogenerate -m "add resource monitor tables"
alembic upgrade head

# 4. 创建核心服务
mkdir -p services/common
touch services/message_context.py
touch services/message_dispatcher.py
touch services/resource_monitor_service.py

# 5. 创建API路由
touch api/routes/resource_monitor.py

# 6. 测试
pytest tests/test_resource_monitor.py

# 7. 提交
git add .
git commit -m "feat: 实现混合架构核心 - 消息分发器和资源监控"
git push origin feature/hybrid-architecture
```

### 11.2 阶段5：115Bot借鉴（第3周）

```bash
# 1. 创建115优化分支
git checkout -b feature/115bot-optimizations

# 2. 安装新依赖
pip install apscheduler>=3.10.0

# 3. 创建115优化文件
touch services/task_scheduler.py
touch utils/media_filters.py

# 4. 修改现有服务
# 修改 services/p115_service.py - 添加秒传检测
# 修改 services/media_monitor_service.py - 添加过滤和优先级

# 5. 测试115优化
pytest tests/test_115_optimizations.py

# 6. 提交
git add .
git commit -m "feat: 集成115Bot优化 - 秒传/过滤/调度/批量"
git push origin feature/115bot-optimizations
```

### 11.3 完整部署

```bash
# 1. 合并所有功能分支
git checkout main
git merge feature/hybrid-architecture
git merge feature/115bot-optimizations

# 2. 更新依赖
pip install -r app/backend/requirements.txt

# 3. 执行数据库迁移
cd app/backend
alembic upgrade head

# 4. 重新构建Docker镜像
docker-compose build --no-cache

# 5. 启动服务
docker-compose up -d

# 6. 验证功能
curl http://localhost:9393/api/health
curl http://localhost:9393/api/resources/rules

# 7. 查看日志
docker-compose logs -f backend
```

### 11.4 验证清单

- [ ] 混合架构核心功能
  - [ ] 消息分发器正常工作
  - [ ] 资源监控规则可以创建和管理
  - [ ] 链接提取功能正常
  - [ ] 自动转存115功能正常

- [ ] 性能优化功能
  - [ ] 消息缓存命中率 > 80%
  - [ ] 批量数据库写入正常
  - [ ] 智能重试队列正常

- [ ] 推送通知功能 ⭐ 新增
  - [ ] Telegram通知正常发送
  - [ ] Web推送通知正常（如已实现）
  - [ ] Webhook通知正常发送
  - [ ] 通知规则管理正常
  - [ ] 通知历史记录正常
  - [ ] 通知模板渲染正常
  - [ ] 下载完成通知正常
  - [ ] 资源捕获通知正常
  - [ ] 115转存通知正常
  - [ ] 任务异常通知正常

- [ ] 115Bot借鉴功能
  - [ ] 秒传检测功能正常（节省90%上传时间）
  - [ ] 智能文件过滤正常（过滤广告文件）
  - [ ] 任务调度器正常运行
  - [ ] 优先级队列正常工作
  - [ ] 批量操作功能正常

- [ ] 前端界面
  - [ ] 资源监控页面可访问
  - [ ] 规则列表和表单正常
  - [ ] 记录列表和详情正常
  - [ ] 优先级调整功能正常
  - [ ] 通知中心可访问 ⭐ 新增
  - [ ] 通知设置页面正常 ⭐ 新增

---

## 12. 相关文档

- [115Bot深度分析](./115BOT_ANALYSIS.md) - 115Bot项目的详细分析和借鉴点
- [视频转存方案对比](./VIDEO_TRANSFER_COMPARISON.md) - TMC与115Bot的技术对比
- [资源监控用户指南](./RESOURCE_MONITOR_USER_GUIDE.md) - 用户使用文档（待创建）
- [资源监控测试指南](./RESOURCE_MONITOR_TESTING.md) - 测试文档（待创建）

---

**🎉 祝开发顺利！**

如有任何问题或需要调整，请随时反馈。我们的目标是构建一个高性能、易扩展、用户友好的混合架构系统！🚀


