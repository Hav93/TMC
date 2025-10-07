"""
日志解析与聚合工具

提供结构化的日志解析、分类和实体提取功能
"""
import re
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    """操作类型分类"""
    FORWARD = "forward"              # 转发消息
    CREATE = "create"                # 创建（规则、用户等）
    UPDATE = "update"                # 更新
    DELETE = "delete"                # 删除
    QUERY = "query"                  # 查询
    AUTH = "auth"                    # 认证
    ERROR = "error"                  # 错误
    STARTUP = "startup"              # 启动
    SHUTDOWN = "shutdown"            # 关闭
    CONNECT = "connect"              # 连接
    DISCONNECT = "disconnect"        # 断开
    FETCH = "fetch"                  # 获取
    PROCESS = "process"              # 处理
    UNKNOWN = "unknown"              # 未知


class LogParser:
    """日志解析器 - 将原始日志解析为结构化数据"""
    
    # 日志格式：2025-10-06 22:45:40 | INFO | api.logs:list_logs:115 - 📊 查询结果: 返回 2 条，总计 2 条
    LOG_PATTERN = re.compile(
        r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s*\|\s*'  # 时间戳
        r'(\w+)\s*\|\s*'                                                 # 级别
        r'([\w\.]+):([\w_]+):(\d+)\s*-\s*'                              # 模块:函数:行号
        r'(.+)$'                                                         # 消息
    )
    
    # Emoji 提取（扩展版，支持更多emoji）
    EMOJI_PATTERN = re.compile(
        r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]|'
        r'[\U0001FA70-\U0001FAFF]|[\u23E9-\u23FA]|[\u25AA-\u25FE]'
    )
    
    # JSON 检测
    JSON_PATTERN = re.compile(r'\{[^{}]*\}|\[[^\[\]]*\]')
    
    # 堆栈跟踪检测
    TRACEBACK_PATTERN = re.compile(r'Traceback \(most recent call last\):|File ".*", line \d+')
    
    # SQL 检测
    SQL_PATTERN = re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\b', re.IGNORECASE)
    
    # URL 检测
    URL_PATTERN = re.compile(r'https?://[^\s]+')
    
    # 文件路径检测
    PATH_PATTERN = re.compile(r'(?:/|\\)(?:[\w\-\.]+(?:/|\\))+[\w\-\.]+')
    
    # 实体提取模式
    ENTITY_PATTERNS = {
        'message_id': re.compile(r'消息ID[:：\s]+(\d+)|message_id[:=\s]+(\d+)', re.IGNORECASE),
        'rule_id': re.compile(r'规则ID[:：\s]+(\d+)|rule_id[:=\s]+(\d+)', re.IGNORECASE),
        'rule_name': re.compile(r'规则[:：]\s*([^\s,，]+)|规则名称[:：]\s*([^\s,，]+)'),
        'chat_id': re.compile(r'聊天ID[:：\s]+(-?\d+)|chat_id[:=\s]+(-?\d+)', re.IGNORECASE),
        'source_chat': re.compile(r'来源[:：]\s*([^\s→-]+)|from[:：]\s*([^\s→-]+)', re.IGNORECASE),
        'target_chat': re.compile(r'目标[:：]\s*([^\s,，]+)|to[:：]\s*([^\s,，]+)', re.IGNORECASE),
        'user_id': re.compile(r'用户ID[:：\s]+(\d+)|user_id[:=\s]+(\d+)', re.IGNORECASE),
        'username': re.compile(r'用户[:：]\s*([^\s,，]+)|username[:：]\s*([^\s,，]+)', re.IGNORECASE),
        'count': re.compile(r'(\d+)\s*条|返回\s*(\d+)|总计\s*(\d+)'),
        'duration': re.compile(r'耗时[:：]?\s*(\d+(?:\.\d+)?)\s*(ms|s|秒|毫秒)'),
    }
    
    # 操作类型关键词映射
    ACTION_KEYWORDS = {
        ActionType.FORWARD: ['转发', 'forward', '发送消息', 'send_message'],
        ActionType.CREATE: ['创建', 'create', '添加', 'add', '新增', 'new'],
        ActionType.UPDATE: ['更新', 'update', '修改', 'modify', 'edit'],
        ActionType.DELETE: ['删除', 'delete', '移除', 'remove'],
        ActionType.QUERY: ['查询', 'query', '获取', 'get', '列表', 'list'],
        ActionType.AUTH: ['登录', 'login', '认证', 'auth', '授权', 'authorize', '未授权', 'unauthorized'],
        ActionType.STARTUP: ['启动', 'startup', 'start', '初始化', 'init'],
        ActionType.SHUTDOWN: ['关闭', 'shutdown', 'stop', '停止'],
        ActionType.CONNECT: ['连接', 'connect', '已连接'],
        ActionType.DISCONNECT: ['断开', 'disconnect', '断线'],
        ActionType.FETCH: ['拉取', 'fetch', '同步', 'sync'],
        ActionType.PROCESS: ['处理', 'process', '执行', 'execute'],
        ActionType.ERROR: ['错误', 'error', '失败', 'failed', '异常', 'exception'],
    }
    
    @classmethod
    def detect_content_type(cls, message: str) -> List[str]:
        """
        检测消息中包含的特殊内容类型
        
        Returns:
            内容类型列表，如 ['json', 'url', 'traceback']
        """
        content_types = []
        
        if cls.JSON_PATTERN.search(message):
            content_types.append('json')
        
        if cls.TRACEBACK_PATTERN.search(message):
            content_types.append('traceback')
        
        if cls.SQL_PATTERN.search(message):
            content_types.append('sql')
        
        if cls.URL_PATTERN.search(message):
            content_types.append('url')
        
        if cls.PATH_PATTERN.search(message):
            content_types.append('path')
        
        return content_types
    
    @classmethod
    def extract_special_content(cls, message: str) -> Dict[str, List[str]]:
        """
        提取消息中的特殊内容
        
        Returns:
            包含各种特殊内容的字典
        """
        special_content = {}
        
        # 提取 JSON
        json_matches = cls.JSON_PATTERN.findall(message)
        if json_matches:
            special_content['json'] = json_matches
        
        # 提取 URL
        url_matches = cls.URL_PATTERN.findall(message)
        if url_matches:
            special_content['urls'] = url_matches
        
        # 提取文件路径
        path_matches = cls.PATH_PATTERN.findall(message)
        if path_matches:
            special_content['paths'] = path_matches
        
        return special_content
    
    @classmethod
    def parse(cls, raw_line: str) -> Dict[str, Any]:
        """
        解析单行日志，返回结构化数据
        
        Args:
            raw_line: 原始日志行
            
        Returns:
            结构化的日志数据
        """
        # 匹配日志格式
        match = cls.LOG_PATTERN.match(raw_line.strip())
        
        if not match:
            # 如果不匹配标准格式，返回简化结构
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': LogLevel.INFO,
                'module': 'unknown',
                'function': 'unknown',
                'line_number': 0,
                'message': raw_line.strip(),
                'emoji': None,
                'action_type': ActionType.UNKNOWN,
                'entities': {},
                'severity_score': 0,
                'raw': raw_line.strip()
            }
        
        timestamp, level, module, function, line_number, message = match.groups()
        
        # 标准化级别
        try:
            log_level = LogLevel(level.upper())
        except ValueError:
            log_level = LogLevel.INFO
        
        # 提取 emoji
        emoji = cls._extract_emoji(message)
        
        # 分类操作类型
        action_type = cls._classify_action(message, log_level)
        
        # 提取实体
        entities = cls._extract_entities(message)
        
        # 计算严重性分数
        severity_score = cls._calculate_severity(log_level, action_type, message)
        
        # 检测内容类型
        content_types = cls.detect_content_type(message)
        
        # 提取特殊内容
        special_content = cls.extract_special_content(message)
        
        # 智能格式化消息
        formatted_message = cls._format_message(message, content_types)
        
        return {
            'timestamp': timestamp,
            'level': log_level.value,
            'module': module,
            'function': function,
            'line_number': int(line_number),
            'message': message,
            'formatted_message': formatted_message,  # 格式化后的消息
            'emoji': emoji,
            'action_type': action_type.value,
            'entities': entities,
            'severity_score': severity_score,
            'content_types': content_types,  # 内容类型列表
            'special_content': special_content,  # 特殊内容
            'raw': raw_line.strip()
        }
    
    @classmethod
    def _extract_emoji(cls, message: str) -> Optional[str]:
        """提取消息中的第一个 emoji"""
        match = cls.EMOJI_PATTERN.search(message)
        return match.group(0) if match else None
    
    @classmethod
    def _classify_action(cls, message: str, level: LogLevel) -> ActionType:
        """根据消息内容和级别分类操作类型"""
        message_lower = message.lower()
        
        # 优先匹配错误
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return ActionType.ERROR
        
        # 匹配关键词
        for action_type, keywords in cls.ACTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return action_type
        
        return ActionType.UNKNOWN
    
    @classmethod
    def _extract_entities(cls, message: str) -> Dict[str, Any]:
        """从消息中提取实体信息"""
        entities = {}
        
        for entity_name, pattern in cls.ENTITY_PATTERNS.items():
            match = pattern.search(message)
            if match:
                # 获取第一个非None的捕获组
                value = next((g for g in match.groups() if g is not None), None)
                if value:
                    # 尝试转换为数字
                    try:
                        if entity_name in ['message_id', 'rule_id', 'chat_id', 'user_id', 'count', 'line_number']:
                            entities[entity_name] = int(value)
                        elif entity_name == 'duration':
                            # 统一转换为毫秒
                            duration_value = float(match.group(1))
                            duration_unit = match.group(2)
                            if duration_unit in ['s', '秒']:
                                entities[entity_name] = duration_value * 1000
                            else:
                                entities[entity_name] = duration_value
                        else:
                            entities[entity_name] = value.strip()
                    except (ValueError, IndexError):
                        entities[entity_name] = value.strip()
        
        return entities
    
    @classmethod
    def _format_message(cls, message: str, content_types: List[str]) -> str:
        """
        智能格式化消息，提升可读性
        
        Args:
            message: 原始消息
            content_types: 内容类型列表
            
        Returns:
            格式化后的消息
        """
        formatted = message
        
        # 如果包含JSON，尝试美化
        if 'json' in content_types:
            try:
                import json as json_lib
                # 查找JSON内容并格式化
                for json_str in cls.JSON_PATTERN.findall(message):
                    try:
                        parsed = json_lib.loads(json_str)
                        pretty = json_lib.dumps(parsed, indent=2, ensure_ascii=False)
                        formatted = formatted.replace(json_str, f'\n{pretty}\n')
                    except:
                        pass
            except:
                pass
        
        # 移除多余空格
        formatted = ' '.join(formatted.split())
        
        return formatted
    
    @classmethod
    def _calculate_severity(cls, level: LogLevel, action_type: ActionType, message: str) -> int:
        """
        计算日志严重性分数 (0-100)
        
        分数越高表示越重要/严重
        """
        score = 0
        
        # 基础分数 - 根据级别
        level_scores = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 50,
            LogLevel.ERROR: 80,
            LogLevel.CRITICAL: 100
        }
        score += level_scores.get(level, 20)
        
        # 操作类型调整
        if action_type == ActionType.ERROR:
            score += 20
        elif action_type == ActionType.DELETE:
            score += 10
        elif action_type == ActionType.AUTH:
            score += 15
        
        # 关键词检测
        critical_keywords = ['失败', 'failed', '错误', 'error', '异常', 'exception', '崩溃', 'crash']
        if any(keyword in message.lower() for keyword in critical_keywords):
            score += 15
        
        # 限制在 0-100 范围
        return min(max(score, 0), 100)


class LogAggregator:
    """日志聚合器 - 提供批量解析和统计功能"""
    
    @staticmethod
    def parse_batch(lines: List[str]) -> List[Dict[str, Any]]:
        """批量解析日志行"""
        return [LogParser.parse(line) for line in lines if line.strip()]
    
    @staticmethod
    def aggregate_stats(parsed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合日志统计信息
        
        Returns:
            包含各种统计指标的字典
        """
        if not parsed_logs:
            return {
                'total': 0,
                'by_level': {},
                'by_action': {},
                'by_module': {},
                'avg_severity': 0,
                'top_entities': {}
            }
        
        # 按级别统计
        by_level = {}
        for log in parsed_logs:
            level = log['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        # 按操作类型统计
        by_action = {}
        for log in parsed_logs:
            action = log['action_type']
            by_action[action] = by_action.get(action, 0) + 1
        
        # 按模块统计
        by_module = {}
        for log in parsed_logs:
            module = log['module']
            by_module[module] = by_module.get(module, 0) + 1
        
        # 平均严重性
        avg_severity = sum(log['severity_score'] for log in parsed_logs) / len(parsed_logs)
        
        # 提取高频实体
        entity_counts: Dict[str, Dict[Any, int]] = {}
        for log in parsed_logs:
            for entity_name, entity_value in log['entities'].items():
                if entity_name not in entity_counts:
                    entity_counts[entity_name] = {}
                entity_counts[entity_name][entity_value] = entity_counts[entity_name].get(entity_value, 0) + 1
        
        # 获取每种实体的 Top 5
        top_entities = {}
        for entity_name, counts in entity_counts.items():
            top_entities[entity_name] = sorted(
                counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        
        return {
            'total': len(parsed_logs),
            'by_level': by_level,
            'by_action': by_action,
            'by_module': by_module,
            'avg_severity': round(avg_severity, 2),
            'top_entities': top_entities
        }
    
    @staticmethod
    def find_related_logs(
        parsed_logs: List[Dict[str, Any]], 
        target_log: Dict[str, Any],
        context_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找与目标日志相关的日志
        
        Args:
            parsed_logs: 所有已解析的日志
            target_log: 目标日志
            context_size: 上下文大小（前后各N条）
            
        Returns:
            相关日志列表
        """
        related = []
        
        # 1. 时间相关（前后N条）
        try:
            target_idx = parsed_logs.index(target_log)
            start_idx = max(0, target_idx - context_size)
            end_idx = min(len(parsed_logs), target_idx + context_size + 1)
            related.extend(parsed_logs[start_idx:end_idx])
        except ValueError:
            pass
        
        # 2. 实体相关（相同的 message_id, rule_id 等）
        target_entities = target_log.get('entities', {})
        if target_entities:
            for log in parsed_logs:
                if log == target_log:
                    continue
                    
                log_entities = log.get('entities', {})
                # 检查是否有共同的实体
                common_entities = set(target_entities.items()) & set(log_entities.items())
                if common_entities and log not in related:
                    related.append(log)
        
        # 去重并按时间排序
        unique_related = {log['raw']: log for log in related}.values()
        return sorted(unique_related, key=lambda x: x['timestamp'])


# 便捷函数
def parse_log_line(line: str) -> Dict[str, Any]:
    """解析单行日志的便捷函数"""
    return LogParser.parse(line)


def parse_log_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """批量解析日志的便捷函数"""
    return LogAggregator.parse_batch(lines)

