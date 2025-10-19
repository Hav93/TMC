"""
广告文件过滤服务

功能：
1. 自动识别广告文件
2. 基于规则的过滤
3. 智能检测算法
4. 白名单机制
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from log_manager import get_logger

logger = get_logger("ad_filter", "enhanced_bot.log")


class FilterAction(Enum):
    """过滤动作"""
    SKIP = "skip"          # 跳过（不下载/保存）
    DELETE = "delete"      # 删除
    QUARANTINE = "quarantine"  # 隔离
    ALLOW = "allow"        # 允许


@dataclass
class AdFilterRule:
    """广告过滤规则"""
    pattern: str                    # 文件名模式（正则）
    min_size: Optional[int] = None  # 最小文件大小（字节）
    max_size: Optional[int] = None  # 最大文件大小（字节）
    action: FilterAction = FilterAction.SKIP
    description: str = ""           # 规则描述
    priority: int = 0               # 优先级（数字越大优先级越高）


class AdFilterService:
    """
    广告文件过滤服务
    
    功能：
    1. 基于文件名模式识别广告
    2. 基于文件大小识别广告
    3. 组合规则判断
    4. 白名单机制
    """
    
    def __init__(self):
        """初始化广告过滤服务"""
        self.rules: List[AdFilterRule] = []
        self.whitelist_patterns: List[str] = []
        self._load_default_rules()
        self._load_default_whitelist()
    
    def _load_default_rules(self):
        """加载默认广告过滤规则"""
        
        # 常见广告文件名模式
        ad_patterns = [
            # 常见广告文件
            (r'(?i).*广告.*', 0, 10 * 1024 * 1024, "包含'广告'关键词"),
            (r'(?i).*推广.*', 0, 10 * 1024 * 1024, "包含'推广'关键词"),
            (r'(?i).*宣传.*', 0, 10 * 1024 * 1024, "包含'宣传'关键词"),
            (r'(?i).*赞助.*', 0, 10 * 1024 * 1024, "包含'赞助'关键词"),
            
            # 常见广告文件名
            (r'(?i)^ad[_\-]?.*', 0, 10 * 1024 * 1024, "以'ad'开头"),
            (r'(?i)^ads[_\-]?.*', 0, 10 * 1024 * 1024, "以'ads'开头"),
            (r'(?i).*[_\-]ad[_\-].*', 0, 10 * 1024 * 1024, "包含'_ad_'或'-ad-'"),
            (r'(?i).*[_\-]ads[_\-].*', 0, 10 * 1024 * 1024, "包含'_ads_'或'-ads-'"),
            
            # 推广链接文件
            (r'(?i).*推广链接.*\.txt', 0, 100 * 1024, "推广链接文本文件"),
            (r'(?i).*下载必看.*\.txt', 0, 100 * 1024, "下载必看文本文件"),
            (r'(?i).*免责声明.*\.txt', 0, 100 * 1024, "免责声明文本文件"),
            (r'(?i).*更多资源.*\.txt', 0, 100 * 1024, "更多资源文本文件"),
            (r'(?i).*最新地址.*\.txt', 0, 100 * 1024, "最新地址文本文件"),
            
            # 小图片广告
            (r'(?i).*\.(jpg|jpeg|png|gif|bmp|webp)$', 0, 500 * 1024, "小于500KB的图片"),
            
            # 小视频广告
            (r'(?i).*预告.*\.(mp4|avi|mkv|flv)$', 0, 10 * 1024 * 1024, "小于10MB的预告视频"),
            (r'(?i).*trailer.*\.(mp4|avi|mkv|flv)$', 0, 10 * 1024 * 1024, "小于10MB的trailer视频"),
            
            # 网站推广文件
            (r'(?i).*www\..*\.txt', 0, 100 * 1024, "包含网址的文本文件"),
            (r'(?i).*http.*\.txt', 0, 100 * 1024, "包含http的文本文件"),
            (r'(?i).*\.com.*\.txt', 0, 100 * 1024, "包含.com的文本文件"),
            
            # 种子站推广
            (r'(?i).*种子.*\.txt', 0, 100 * 1024, "种子站推广文本"),
            (r'(?i).*torrent.*\.txt', 0, 100 * 1024, "torrent推广文本"),
            (r'(?i).*磁力.*\.txt', 0, 100 * 1024, "磁力推广文本"),
            
            # 二维码图片
            (r'(?i).*二维码.*\.(jpg|jpeg|png|gif)$', 0, 500 * 1024, "二维码图片"),
            (r'(?i).*qrcode.*\.(jpg|jpeg|png|gif)$', 0, 500 * 1024, "QR码图片"),
            (r'(?i).*扫码.*\.(jpg|jpeg|png|gif)$', 0, 500 * 1024, "扫码图片"),
            
            # 会员推广
            (r'(?i).*会员.*\.txt', 0, 100 * 1024, "会员推广文本"),
            (r'(?i).*vip.*\.txt', 0, 100 * 1024, "VIP推广文本"),
            (r'(?i).*优惠.*\.txt', 0, 100 * 1024, "优惠推广文本"),
            
            # 联系方式文件
            (r'(?i).*联系.*\.txt', 0, 100 * 1024, "联系方式文本"),
            (r'(?i).*contact.*\.txt', 0, 100 * 1024, "contact文本"),
            (r'(?i).*qq.*\.txt', 0, 100 * 1024, "QQ联系文本"),
            (r'(?i).*微信.*\.txt', 0, 100 * 1024, "微信联系文本"),
        ]
        
        for pattern, min_size, max_size, desc in ad_patterns:
            self.rules.append(AdFilterRule(
                pattern=pattern,
                min_size=min_size,
                max_size=max_size,
                action=FilterAction.SKIP,
                description=desc,
                priority=1
            ))
        
        logger.info(f"✅ 已加载 {len(self.rules)} 条默认广告过滤规则")
    
    def _load_default_whitelist(self):
        """加载默认白名单"""
        
        # 白名单模式（这些文件即使匹配广告规则也不过滤）
        whitelist = [
            r'(?i)^readme.*',           # README文件
            r'(?i)^license.*',          # LICENSE文件
            r'(?i)^changelog.*',        # CHANGELOG文件
            r'(?i).*说明.*\.txt',       # 说明文件
            r'(?i).*使用.*\.txt',       # 使用说明
            r'(?i).*安装.*\.txt',       # 安装说明
        ]
        
        self.whitelist_patterns.extend(whitelist)
        logger.info(f"✅ 已加载 {len(self.whitelist_patterns)} 条白名单规则")
    
    def add_rule(self, rule: AdFilterRule):
        """添加自定义规则"""
        self.rules.append(rule)
        # 按优先级排序（优先级高的在前）
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"✅ 添加广告过滤规则: {rule.description}")
    
    def add_whitelist(self, pattern: str):
        """添加白名单模式"""
        self.whitelist_patterns.append(pattern)
        logger.info(f"✅ 添加白名单规则: {pattern}")
    
    def is_whitelisted(self, filename: str) -> bool:
        """检查文件是否在白名单中"""
        for pattern in self.whitelist_patterns:
            if re.match(pattern, filename):
                logger.debug(f"✅ 文件在白名单中: {filename} (匹配规则: {pattern})")
                return True
        return False
    
    def check_file(self, filename: str, file_size: Optional[int] = None) -> Tuple[FilterAction, Optional[str]]:
        """
        检查文件是否为广告
        
        Args:
            filename: 文件名
            file_size: 文件大小（字节），可选
        
        Returns:
            (FilterAction, reason): 过滤动作和原因
        """
        # 1. 检查白名单
        if self.is_whitelisted(filename):
            return FilterAction.ALLOW, "文件在白名单中"
        
        # 2. 检查规则（按优先级）
        for rule in self.rules:
            # 检查文件名模式
            if not re.match(rule.pattern, filename):
                continue
            
            # 检查文件大小（如果提供）
            if file_size is not None:
                if rule.min_size is not None and file_size < rule.min_size:
                    continue
                if rule.max_size is not None and file_size > rule.max_size:
                    continue
            
            # 匹配成功
            reason = f"匹配规则: {rule.description}"
            logger.info(f"🚫 检测到广告文件: {filename} ({reason})")
            return rule.action, reason
        
        # 3. 未匹配任何规则，允许
        return FilterAction.ALLOW, "未匹配任何广告规则"
    
    def filter_files(self, files: List[Dict[str, any]]) -> Tuple[List[Dict[str, any]], List[Dict[str, any]]]:
        """
        批量过滤文件列表
        
        Args:
            files: 文件列表，每个文件包含 'name' 和可选的 'size' 字段
        
        Returns:
            (allowed_files, filtered_files): 允许的文件列表和被过滤的文件列表
        """
        allowed = []
        filtered = []
        
        for file in files:
            filename = file.get('name', '')
            file_size = file.get('size')
            
            action, reason = self.check_file(filename, file_size)
            
            if action == FilterAction.ALLOW:
                allowed.append(file)
            else:
                file['filter_reason'] = reason
                file['filter_action'] = action.value
                filtered.append(file)
        
        logger.info(f"📊 过滤结果: 允许 {len(allowed)} 个文件, 过滤 {len(filtered)} 个文件")
        return allowed, filtered
    
    def get_stats(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            "total_rules": len(self.rules),
            "whitelist_patterns": len(self.whitelist_patterns),
            "rules_by_priority": {
                "high": len([r for r in self.rules if r.priority >= 5]),
                "medium": len([r for r in self.rules if 1 <= r.priority < 5]),
                "low": len([r for r in self.rules if r.priority < 1]),
            }
        }


# 全局单例
_ad_filter_service: Optional[AdFilterService] = None


def get_ad_filter_service() -> AdFilterService:
    """获取广告过滤服务单例"""
    global _ad_filter_service
    if _ad_filter_service is None:
        _ad_filter_service = AdFilterService()
    return _ad_filter_service


# 便捷函数
def is_ad_file(filename: str, file_size: Optional[int] = None) -> bool:
    """
    快速检查文件是否为广告
    
    Args:
        filename: 文件名
        file_size: 文件大小（字节），可选
    
    Returns:
        bool: True表示是广告文件
    """
    service = get_ad_filter_service()
    action, _ = service.check_file(filename, file_size)
    return action != FilterAction.ALLOW


def filter_ad_files(files: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    过滤广告文件，返回干净的文件列表
    
    Args:
        files: 文件列表
    
    Returns:
        List[Dict]: 过滤后的文件列表
    """
    service = get_ad_filter_service()
    allowed, _ = service.filter_files(files)
    return allowed

