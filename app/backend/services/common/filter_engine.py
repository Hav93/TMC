"""
共享过滤引擎

功能：
1. 统一的关键词过滤逻辑
2. 正则表达式缓存
3. 支持多种匹配模式（包含、正则、精确）
4. 性能优化（编译缓存、批量匹配）
"""
from typing import List, Dict, Any, Optional, Set
import re
from dataclasses import dataclass
from enum import Enum
import asyncio
from log_manager import get_logger

logger = get_logger("filter_engine", "enhanced_bot.log")


class MatchMode(str, Enum):
    """匹配模式"""
    CONTAINS = "contains"  # 包含匹配
    REGEX = "regex"  # 正则匹配
    EXACT = "exact"  # 精确匹配
    STARTS_WITH = "starts_with"  # 开头匹配
    ENDS_WITH = "ends_with"  # 结尾匹配


@dataclass
class FilterRule:
    """过滤规则"""
    keyword: str
    mode: MatchMode = MatchMode.CONTAINS
    case_sensitive: bool = False
    
    def __hash__(self):
        return hash((self.keyword, self.mode, self.case_sensitive))


class SharedFilterEngine:
    """
    共享过滤引擎
    
    特性：
    1. 正则表达式编译缓存
    2. 批量匹配优化
    3. 多种匹配模式
    4. 统计信息
    """
    
    def __init__(self, max_regex_cache: int = 500):
        self.max_regex_cache = max_regex_cache
        self._regex_cache: Dict[str, re.Pattern] = {}
        self._lock = asyncio.Lock()
        
        # 统计信息
        self.stats = {
            'total_matches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'regex_compilations': 0
        }
    
    def _get_compiled_regex(self, pattern: str, case_sensitive: bool = False) -> re.Pattern:
        """获取编译后的正则表达式（带缓存）"""
        cache_key = f"{pattern}|{case_sensitive}"
        
        if cache_key in self._regex_cache:
            self.stats['cache_hits'] += 1
            return self._regex_cache[cache_key]
        
        # 编译新的正则表达式
        self.stats['cache_misses'] += 1
        self.stats['regex_compilations'] += 1
        
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            logger.error(f"正则表达式编译失败: {pattern}, 错误: {e}")
            # 返回一个永远不匹配的正则
            compiled = re.compile(r'(?!.*)')
        
        # 缓存
        if len(self._regex_cache) >= self.max_regex_cache:
            # 移除最旧的一个（简单FIFO）
            first_key = next(iter(self._regex_cache))
            del self._regex_cache[first_key]
        
        self._regex_cache[cache_key] = compiled
        return compiled
    
    def match_single(
        self,
        text: str,
        rule: FilterRule
    ) -> bool:
        """单个规则匹配"""
        if not text:
            return False
        
        # 处理大小写
        if not rule.case_sensitive:
            text = text.lower()
            keyword = rule.keyword.lower()
        else:
            keyword = rule.keyword
        
        # 根据模式匹配
        if rule.mode == MatchMode.CONTAINS:
            return keyword in text
        
        elif rule.mode == MatchMode.EXACT:
            return text == keyword
        
        elif rule.mode == MatchMode.STARTS_WITH:
            return text.startswith(keyword)
        
        elif rule.mode == MatchMode.ENDS_WITH:
            return text.endswith(keyword)
        
        elif rule.mode == MatchMode.REGEX:
            pattern = self._get_compiled_regex(keyword, rule.case_sensitive)
            return bool(pattern.search(text))
        
        return False
    
    def match_any(
        self,
        text: str,
        rules: List[FilterRule]
    ) -> Optional[FilterRule]:
        """匹配任意一个规则（返回第一个匹配的规则）"""
        self.stats['total_matches'] += 1
        
        for rule in rules:
            if self.match_single(text, rule):
                return rule
        
        return None
    
    def match_all(
        self,
        text: str,
        rules: List[FilterRule]
    ) -> List[FilterRule]:
        """匹配所有规则（返回所有匹配的规则）"""
        self.stats['total_matches'] += 1
        
        matched = []
        for rule in rules:
            if self.match_single(text, rule):
                matched.append(rule)
        
        return matched
    
    def match_keywords(
        self,
        text: str,
        keywords: List[str],
        mode: MatchMode = MatchMode.CONTAINS,
        case_sensitive: bool = False
    ) -> List[str]:
        """
        匹配关键词列表（简化版）
        
        返回：匹配的关键词列表
        """
        rules = [
            FilterRule(keyword=kw, mode=mode, case_sensitive=case_sensitive)
            for kw in keywords
        ]
        
        matched_rules = self.match_all(text, rules)
        return [rule.keyword for rule in matched_rules]
    
    def batch_match(
        self,
        texts: List[str],
        rules: List[FilterRule]
    ) -> Dict[str, List[FilterRule]]:
        """
        批量匹配
        
        返回：{text: [matched_rules]}
        """
        results = {}
        for text in texts:
            matched = self.match_all(text, rules)
            if matched:
                results[text] = matched
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_cache_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (
            (self.stats['cache_hits'] / total_cache_requests * 100)
            if total_cache_requests > 0 else 0
        )
        
        return {
            'total_matches': self.stats['total_matches'],
            'regex_cache_size': len(self._regex_cache),
            'max_regex_cache': self.max_regex_cache,
            'cache_hit_rate': f"{cache_hit_rate:.2f}%",
            'regex_compilations': self.stats['regex_compilations']
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._regex_cache.clear()
        logger.info("正则表达式缓存已清空")


# ===== 便捷函数 =====

def parse_keyword_config(keyword_config: Dict[str, Any]) -> FilterRule:
    """
    解析关键词配置
    
    配置格式：
    {
        "keyword": "关键词",
        "mode": "contains",  # 可选
        "case_sensitive": false  # 可选
    }
    """
    keyword = keyword_config.get('keyword', '')
    mode_str = keyword_config.get('mode', 'contains')
    case_sensitive = keyword_config.get('case_sensitive', False)
    
    try:
        mode = MatchMode(mode_str)
    except ValueError:
        logger.warning(f"未知的匹配模式: {mode_str}, 使用默认值 'contains'")
        mode = MatchMode.CONTAINS
    
    return FilterRule(
        keyword=keyword,
        mode=mode,
        case_sensitive=case_sensitive
    )


def parse_keywords_list(keywords_config: List[Dict[str, Any]]) -> List[FilterRule]:
    """解析关键词配置列表"""
    return [parse_keyword_config(kw) for kw in keywords_config]


# 全局过滤引擎实例
_filter_engine: Optional[SharedFilterEngine] = None


def get_filter_engine() -> SharedFilterEngine:
    """获取全局过滤引擎实例"""
    global _filter_engine
    if _filter_engine is None:
        _filter_engine = SharedFilterEngine()
        logger.info("✅ 创建全局共享过滤引擎")
    return _filter_engine

