"""
通知模板引擎

功能：
1. 预定义通知模板
2. 模板渲染
3. 支持自定义模板
4. 多语言支持（可扩展）
"""
from typing import Dict, Any
from datetime import datetime
from services.notification_service import NotificationType


class NotificationTemplateEngine:
    """
    通知模板引擎
    
    功能：
    1. 预定义通知模板
    2. 模板渲染
    3. 支持自定义模板
    """
    
    # 预定义模板
    TEMPLATES = {
        # 资源监控相关
        NotificationType.RESOURCE_CAPTURED: """
🔗 资源捕获通知

📋 规则：{rule_name}
🔗 链接类型：{link_type}
📝 链接：{link_url}
💬 来源：{source_chat_name}
🕐 时间：{capture_time}

{keywords_matched}
""".strip(),
        
        NotificationType.SAVE_115_SUCCESS: """
✅ 115转存成功

📋 规则：{rule_name}
🔗 链接：{link_url}
📁 保存路径：{save_path}
🕐 时间：{save_time}

{file_info}
""".strip(),
        
        NotificationType.SAVE_115_FAILED: """
❌ 115转存失败

📋 规则：{rule_name}
🔗 链接：{link_url}
❌ 错误：{error_message}
🔄 重试次数：{retry_count}
🕐 时间：{fail_time}

请检查115账号状态或链接有效性。
""".strip(),
        
        # 媒体监控相关
        NotificationType.DOWNLOAD_COMPLETE: """
✅ 下载完成

📋 规则：{rule_name}
📁 文件：{file_name}
📊 大小：{file_size}
💾 保存路径：{save_path}
⏱ 耗时：{duration}
🕐 完成时间：{complete_time}
""".strip(),
        
        NotificationType.DOWNLOAD_FAILED: """
❌ 下载失败

📋 规则：{rule_name}
📁 文件：{file_name}
❌ 错误：{error_message}
🔄 重试次数：{retry_count}
🕐 时间：{fail_time}

请检查网络连接或存储空间。
""".strip(),
        
        NotificationType.DOWNLOAD_PROGRESS: """
⏬ 下载进度

📋 规则：{rule_name}
📁 文件：{file_name}
📊 进度：{progress}%
⚡ 速度：{speed}
⏱ 剩余时间：{eta}
""".strip(),
        
        # 消息转发相关
        NotificationType.FORWARD_SUCCESS: """
✅ 消息转发成功

📋 规则：{rule_name}
📤 来源：{source_chat_name}
📥 目标：{target_chat_name}
💬 消息数：{message_count}
🕐 时间：{forward_time}
""".strip(),
        
        NotificationType.FORWARD_FAILED: """
❌ 消息转发失败

📋 规则：{rule_name}
📤 来源：{source_chat_name}
📥 目标：{target_chat_name}
❌ 错误：{error_message}
🕐 时间：{fail_time}
""".strip(),
        
        # 系统相关
        NotificationType.TASK_STALE: """
⚠️ 任务卡住警告

📋 任务类型：{task_type}
🆔 任务ID：{task_id}
⏱ 卡住时长：{stale_duration}
📊 状态：{task_status}
🕐 时间：{check_time}

建议：检查任务状态或重启服务。
""".strip(),
        
        NotificationType.STORAGE_WARNING: """
⚠️ 存储空间警告

💾 总空间：{total_space}
📊 已使用：{used_space} ({used_percent}%)
📉 剩余：{free_space}
🕐 时间：{check_time}

建议：清理不必要的文件或扩展存储空间。
""".strip(),
        
        NotificationType.DAILY_REPORT: """
📊 每日报告

📅 日期：{report_date}

📈 统计数据：
• 消息转发：{forward_count} 条
• 媒体下载：{download_count} 个
• 资源捕获：{resource_count} 个
• 115转存：{save_115_count} 个

✅ 成功率：
• 转发成功率：{forward_success_rate}%
• 下载成功率：{download_success_rate}%
• 转存成功率：{save_success_rate}%

💾 存储使用：{storage_used}

🕐 生成时间：{generate_time}
""".strip(),
        
        NotificationType.SYSTEM_ERROR: """
❌ 系统错误

🔴 错误类型：{error_type}
📝 错误信息：{error_message}
📍 发生位置：{error_location}
🕐 时间：{error_time}

{stack_trace}

建议：请检查日志文件获取详细信息。
""".strip(),
    }
    
    def render(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        custom_template: str = None
    ) -> str:
        """
        渲染通知消息
        
        Args:
            notification_type: 通知类型
            data: 数据字典
            custom_template: 自定义模板（可选）
            
        Returns:
            str: 渲染后的消息
        """
        try:
            # 使用自定义模板或预定义模板
            template = custom_template or self.TEMPLATES.get(notification_type)
            
            if not template:
                # 如果没有模板，返回简单格式
                return self._render_simple(notification_type, data)
            
            # 格式化数据
            formatted_data = self._format_data(data)
            
            # 渲染模板
            try:
                message = template.format(**formatted_data)
            except KeyError as e:
                # 如果缺少某些字段，使用默认值
                message = template.format_map(SafeDict(formatted_data))
            
            return message
            
        except Exception as e:
            # 如果渲染失败，返回简单格式
            return self._render_simple(notification_type, data)
    
    def _format_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """格式化数据为字符串"""
        formatted = {}
        
        for key, value in data.items():
            if value is None:
                formatted[key] = "N/A"
            elif isinstance(value, datetime):
                formatted[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (int, float)):
                # 特殊处理某些数值
                if key.endswith('_size') or key.endswith('_space'):
                    formatted[key] = self._format_size(value)
                elif key.endswith('_percent'):
                    formatted[key] = f"{value:.1f}"
                elif key.endswith('_rate'):
                    formatted[key] = f"{value:.1f}"
                elif key.endswith('_duration') or key.endswith('_time'):
                    formatted[key] = self._format_duration(value)
                else:
                    formatted[key] = str(value)
            elif isinstance(value, list):
                formatted[key] = ', '.join(str(v) for v in value)
            else:
                formatted[key] = str(value)
        
        return formatted
    
    def _format_size(self, size_bytes: float) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
        else:
            days = seconds / 86400
            return f"{days:.1f}天"
    
    def _render_simple(self, notification_type: NotificationType, data: Dict[str, Any]) -> str:
        """简单格式渲染（后备方案）"""
        lines = [f"📢 {notification_type.value}"]
        lines.append("")
        
        for key, value in data.items():
            if value is not None:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)


class SafeDict(dict):
    """安全字典，缺失的键返回占位符"""
    def __missing__(self, key):
        return f"{{{key}}}"

