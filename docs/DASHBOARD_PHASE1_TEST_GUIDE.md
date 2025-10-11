# 📊 Dashboard Phase 1 测试指南

## ✅ 已完成功能

### 后端 API
- ✅ `GET /api/dashboard/overview` - 完整的仪表盘数据
- ✅ `GET /api/dashboard/insights` - 智能洞察数据

### 前端组件
- ✅ 系统总览卡片
- ✅ 双栏模块卡片（消息转发 + 媒体监控）
- ✅ 近7日趋势图表
- ✅ 文件类型分布饼图
- ✅ 存储分布环形图
- ✅ 快速洞察面板

---

## 🧪 数据准确性测试清单

### 1. 系统总览数据验证

#### 测试步骤：
1. 访问 `http://localhost:9393/dashboard`
2. 查看顶部系统总览卡片

#### 验证项：
- [ ] **总规则数** = 消息转发规则数 + 媒体监控规则数
  - 手动验证：访问 `/rules` 和 `/media-monitor` 页面，统计规则总数
  - 预期：数字应该一致

- [ ] **活跃规则数** = 已启用的规则数量
  - 手动验证：在规则页面查看"已启用"状态的规则数量
  - 预期：数字应该一致

- [ ] **今日下载数** = 今天成功下载的媒体文件数量
  - 手动验证：访问 `/download-tasks`，筛选今日 + 成功状态
  - 预期：数字应该一致

- [ ] **总存储** = 所有媒体文件的大小总和
  - 手动验证：访问 `/media-library`，查看文件统计
  - 预期：数字应该一致（允许小数点误差）

- [ ] **系统状态**
  - 正常：成功率 ≥ 90%，下载中 < 10，处理中 < 50
  - 警告：成功率 < 90%
  - 繁忙：下载中 ≥ 10 或 处理中 ≥ 50

---

### 2. 消息转发模块验证

#### 测试步骤：
1. 查看左侧"📨 消息转发"卡片

#### 验证项：
- [ ] **今日转发** = 今天转发的消息数量
  - SQL验证：
    ```sql
    SELECT COUNT(*) FROM message_logs 
    WHERE DATE(created_at) = CURRENT_DATE;
    ```
  - 手动验证：访问 `/system-logs`，筛选今日日志
  - 预期：数字应该一致

- [ ] **活跃规则** = 已启用的转发规则数 / 总转发规则数
  - SQL验证：
    ```sql
    SELECT 
      COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
      COUNT(*) as total
    FROM forward_rules;
    ```
  - 预期：格式为 "X / Y"

- [ ] **成功率** = (成功消息数 / 总消息数) × 100
  - SQL验证：
    ```sql
    SELECT 
      COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as rate
    FROM message_logs;
    ```
  - 预期：百分比应该一致（允许小数点误差）

- [ ] **处理中** = 状态为 'pending' 的消息数
  - SQL验证：
    ```sql
    SELECT COUNT(*) FROM message_logs WHERE status = 'pending';
    ```
  - 预期：数字应该一致

- [ ] **近7日趋势图**
  - 验证：图表显示最近7天的数据点
  - 预期：每天一个数据点，日期连续

---

### 3. 媒体监控模块验证

#### 测试步骤：
1. 查看右侧"📥 媒体监控"卡片

#### 验证项：
- [ ] **今日下载** = 今天成功下载的任务数
  - SQL验证：
    ```sql
    SELECT COUNT(*) FROM download_tasks 
    WHERE DATE(created_at) = CURRENT_DATE 
    AND status = 'success';
    ```
  - 手动验证：访问 `/download-tasks`，筛选今日 + 成功
  - 预期：数字应该一致

- [ ] **活跃监控** = 已启用的监控规则数 / 总监控规则数
  - SQL验证：
    ```sql
    SELECT 
      COUNT(CASE WHEN is_active = 1 THEN 1 END) as active,
      COUNT(*) as total
    FROM media_monitor_rules;
    ```
  - 预期：格式为 "X / Y"

- [ ] **成功率** = (成功任务数 / 总任务数) × 100
  - SQL验证：
    ```sql
    SELECT 
      COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as rate
    FROM download_tasks;
    ```
  - 预期：百分比应该一致

- [ ] **存储使用** = 所有媒体文件的大小总和
  - SQL验证：
    ```sql
    SELECT SUM(file_size_mb) / 1024 as storage_gb 
    FROM media_files;
    ```
  - 预期：数字应该一致（GB单位）

- [ ] **近7日趋势图**
  - 验证：图表显示最近7天的下载数据
  - 预期：每天一个数据点，只统计成功的任务

---

### 4. 文件类型分布验证

#### 测试步骤：
1. 查看"📁 文件类型分布"饼图

#### 验证项：
- [ ] **视频文件**
  - SQL验证：
    ```sql
    SELECT 
      COUNT(*) as count,
      SUM(file_size_mb) / 1024 as size_gb
    FROM media_files 
    WHERE file_type = 'video';
    ```
  - 预期：数量和大小都应该一致

- [ ] **图片文件**
  - SQL验证：同上，`file_type = 'image'`
  - 预期：数量和大小都应该一致

- [ ] **音频文件**
  - SQL验证：同上，`file_type = 'audio'`
  - 预期：数量和大小都应该一致

- [ ] **文档文件**
  - SQL验证：同上，`file_type = 'document'`
  - 预期：数量和大小都应该一致

- [ ] **饼图百分比**
  - 验证：所有扇区的百分比总和 = 100%
  - 预期：百分比计算正确

---

### 5. 存储分布验证

#### 测试步骤：
1. 查看"☁️ 存储分布"环形图

#### 验证项：
- [ ] **本地存储**
  - SQL验证：
    ```sql
    SELECT 
      COUNT(*) as count,
      SUM(file_size_mb) / 1024 as size_gb
    FROM media_files 
    WHERE is_organized = 1;
    ```
  - 预期：数量和大小都应该一致

- [ ] **云端存储**
  - SQL验证：
    ```sql
    SELECT 
      COUNT(*) as count,
      SUM(file_size_mb) / 1024 as size_gb
    FROM media_files 
    WHERE is_uploaded_to_cloud = 1;
    ```
  - 预期：数量和大小都应该一致

- [ ] **云端占比**
  - 计算：(云端存储 / 总存储) × 100
  - 预期：环形图中心显示的百分比应该正确

- [ ] **总存储**
  - SQL验证：
    ```sql
    SELECT SUM(file_size_mb) / 1024 as total_gb 
    FROM media_files;
    ```
  - 预期：应该等于本地存储 + 云端存储（注意：文件可能同时存在于本地和云端）

---

### 6. 智能洞察验证

#### 测试步骤：
1. 查看"🎯 快速洞察"面板

#### 验证项：
- [ ] **今日下载高峰**
  - SQL验证：
    ```sql
    SELECT 
      HOUR(created_at) as hour,
      COUNT(*) as count
    FROM download_tasks
    WHERE DATE(created_at) = CURRENT_DATE
    AND status = 'success'
    GROUP BY HOUR(created_at)
    ORDER BY count DESC
    LIMIT 1;
    ```
  - 预期：显示下载量最多的小时段

- [ ] **最活跃规则**
  - SQL验证：
    ```sql
    SELECT 
      r.name,
      COUNT(t.id) as count
    FROM media_monitor_rules r
    JOIN download_tasks t ON r.id = t.monitor_rule_id
    WHERE DATE(t.created_at) = CURRENT_DATE
    AND t.status = 'success'
    GROUP BY r.id
    ORDER BY count DESC
    LIMIT 1;
    ```
  - 预期：显示今日下载量最多的规则

- [ ] **存储预警**
  - 计算逻辑：
    1. 近7日平均增长 = 近7日新增存储 / 7
    2. 达到80%需要天数 = (500GB × 0.8 - 当前使用) / 日均增长
  - 预期：
    - 如果 < 30天，显示警告
    - 进度条显示当前使用百分比

- [ ] **收藏文件**
  - SQL验证：
    ```sql
    SELECT COUNT(*) FROM media_files WHERE is_starred = 1;
    ```
  - 预期：数字应该一致

---

## 🔄 实时刷新测试

### 测试步骤：
1. 保持仪表盘页面打开
2. 在另一个标签页执行操作（如：添加规则、下载文件）
3. 等待30秒（overview刷新间隔）或60秒（insights刷新间隔）
4. 观察仪表盘数据是否自动更新

### 验证项：
- [ ] 系统总览数据自动刷新（30秒）
- [ ] 模块统计数据自动刷新（30秒）
- [ ] 趋势图表自动刷新（30秒）
- [ ] 智能洞察自动刷新（60秒）
- [ ] 手动点击"刷新"按钮立即更新

---

## 🎨 UI/UX 测试

### 响应式布局
- [ ] 桌面端（>1200px）：双栏布局正常显示
- [ ] 平板端（768px-1200px）：卡片自适应排列
- [ ] 移动端（<768px）：单栏垂直布局

### 加载状态
- [ ] 首次加载显示 Spin 组件
- [ ] 数据加载失败显示错误提示
- [ ] 图表加载中显示 loading 状态

### 空状态
- [ ] 无趋势数据时显示"暂无数据"
- [ ] 无文件时显示"暂无文件"
- [ ] 无洞察数据时显示"暂无洞察数据"

### 交互
- [ ] 点击"管理规则"跳转到规则页面
- [ ] 点击"管理监控"跳转到监控页面
- [ ] 点击"刷新"按钮触发数据重新加载
- [ ] 鼠标悬停图表显示 Tooltip

---

## 🐛 已知问题和限制

### 数据精度
- 存储大小计算可能有小数点误差（±0.01 GB）
- 百分比计算四舍五入到小数点后2位

### 性能
- 首次加载需要查询多个数据库表，可能需要1-2秒
- 大量数据（>10000条记录）时，趋势图渲染可能较慢

### 功能限制
- 趋势图只显示近7日数据
- 存储预警假设总容量为500GB（可配置）
- 高峰时段只统计今日数据

---

## 📝 测试报告模板

```markdown
## Dashboard Phase 1 测试报告

**测试日期**: YYYY-MM-DD
**测试人员**: [姓名]
**环境**: test 分支

### 测试结果汇总
- [ ] 系统总览：通过 / 失败
- [ ] 消息转发模块：通过 / 失败
- [ ] 媒体监控模块：通过 / 失败
- [ ] 文件类型分布：通过 / 失败
- [ ] 存储分布：通过 / 失败
- [ ] 智能洞察：通过 / 失败
- [ ] 实时刷新：通过 / 失败
- [ ] UI/UX：通过 / 失败

### 发现的问题
1. [问题描述]
   - 预期：[预期结果]
   - 实际：[实际结果]
   - 严重程度：高 / 中 / 低

### 数据准确性验证
- [ ] 所有统计数字与数据库查询结果一致
- [ ] 百分比计算正确
- [ ] 趋势图数据点正确
- [ ] 饼图/环形图比例正确

### 建议
- [改进建议]
```

---

## 🚀 快速验证命令

### Docker 环境
```bash
# 进入容器
docker exec -it tmc-test /bin/bash

# 连接数据库
sqlite3 /app/data/bot.db

# 执行验证查询
.mode column
.headers on

-- 验证系统总览
SELECT 
  (SELECT COUNT(*) FROM forward_rules) + 
  (SELECT COUNT(*) FROM media_monitor_rules) as total_rules,
  (SELECT COUNT(*) FROM forward_rules WHERE is_active = 1) + 
  (SELECT COUNT(*) FROM media_monitor_rules WHERE is_active = 1) as active_rules,
  (SELECT COUNT(*) FROM download_tasks 
   WHERE DATE(created_at) = DATE('now') AND status = 'success') as today_downloads,
  (SELECT SUM(file_size_mb) / 1024 FROM media_files) as total_storage_gb;
```

---

## ✅ 验证完成标准

Phase 1 被认为完成且数据准确，当且仅当：

1. ✅ 所有统计数字与数据库查询结果一致（误差 < 1%）
2. ✅ 所有百分比计算正确（误差 < 0.1%）
3. ✅ 趋势图显示正确的日期和数据点
4. ✅ 饼图/环形图比例正确
5. ✅ 实时刷新功能正常工作
6. ✅ 无明显的UI/UX问题
7. ✅ 空状态和错误状态处理正确
8. ✅ 响应式布局在各设备上正常显示

---

**测试完成后，请更新 TODO 状态并创建测试报告！** 🎉

