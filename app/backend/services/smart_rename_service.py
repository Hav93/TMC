"""
智能重命名服务

功能：
1. 从文件名提取元数据
2. 标准化命名
3. 支持多种媒体类型
4. 自定义命名模板
"""
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

from log_manager import get_logger

logger = get_logger("smart_rename", "enhanced_bot.log")


class MediaType(Enum):
    """媒体类型"""
    MOVIE = "movie"        # 电影
    TV = "tv"              # 电视剧
    ANIME = "anime"        # 动漫
    MUSIC = "music"        # 音乐
    DOCUMENTARY = "documentary"  # 纪录片
    OTHER = "other"        # 其他


@dataclass
class MediaMetadata:
    """媒体元数据"""
    media_type: MediaType
    title: str                      # 标题
    year: Optional[int] = None      # 年份
    season: Optional[int] = None    # 季
    episode: Optional[int] = None   # 集
    resolution: Optional[str] = None  # 分辨率
    codec: Optional[str] = None     # 编码
    audio: Optional[str] = None     # 音频
    source: Optional[str] = None    # 来源
    group: Optional[str] = None     # 制作组
    language: Optional[str] = None  # 语言
    subtitle: Optional[str] = None  # 字幕
    extension: str = ""             # 文件扩展名


class SmartRenameService:
    """
    智能重命名服务
    
    功能：
    1. 解析文件名
    2. 提取元数据
    3. 生成标准化文件名
    """
    
    def __init__(self):
        """初始化智能重命名服务"""
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化匹配模式"""
        
        # 分辨率模式
        self.resolution_patterns = [
            r'(?i)(4K|2160p|UHD)',
            r'(?i)(1080p|FHD)',
            r'(?i)(720p|HD)',
            r'(?i)(480p|SD)',
            r'(?i)(360p)',
        ]
        
        # 编码模式
        self.codec_patterns = [
            r'(?i)(H\.?265|HEVC|x265)',
            r'(?i)(H\.?264|AVC|x264)',
            r'(?i)(VP9)',
            r'(?i)(AV1)',
        ]
        
        # 音频模式
        self.audio_patterns = [
            r'(?i)(DTS-HD|DTS\.?HD)',
            r'(?i)(TrueHD|Dolby\.?TrueHD)',
            r'(?i)(Atmos|Dolby\.?Atmos)',
            r'(?i)(DTS)',
            r'(?i)(AC3|DD)',
            r'(?i)(AAC)',
            r'(?i)(FLAC)',
        ]
        
        # 来源模式
        self.source_patterns = [
            r'(?i)(BluRay|Blu-Ray|BD)',
            r'(?i)(WEB-DL|WEBRip|WEB)',
            r'(?i)(HDTV)',
            r'(?i)(DVDRip|DVD)',
            r'(?i)(BDRip)',
        ]
        
        # 季集模式
        self.season_episode_patterns = [
            r'[Ss](\d{1,2})[Ee](\d{1,3})',  # S01E01
            r'(\d{1,2})x(\d{1,3})',          # 1x01
            r'第(\d{1,3})季.*?第(\d{1,3})集',  # 第1季第1集
        ]
        
        # 年份模式
        self.year_pattern = r'(19\d{2}|20\d{2})'
    
    def parse_filename(self, filename: str) -> MediaMetadata:
        """
        解析文件名，提取元数据
        
        Args:
            filename: 文件名
        
        Returns:
            MediaMetadata: 元数据
        """
        # 分离文件名和扩展名
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
        else:
            name, ext = filename, ''
        
        metadata = MediaMetadata(
            media_type=MediaType.OTHER,
            title=name,
            extension=ext
        )
        
        # 提取分辨率
        for pattern in self.resolution_patterns:
            match = re.search(pattern, name)
            if match:
                metadata.resolution = match.group(1).upper()
                break
        
        # 提取编码
        for pattern in self.codec_patterns:
            match = re.search(pattern, name)
            if match:
                codec = match.group(1)
                # 标准化编码名称
                if 'H.265' in codec.upper() or 'HEVC' in codec.upper() or 'X265' in codec.upper():
                    metadata.codec = 'H.265'
                elif 'H.264' in codec.upper() or 'AVC' in codec.upper() or 'X264' in codec.upper():
                    metadata.codec = 'H.264'
                else:
                    metadata.codec = codec.upper()
                break
        
        # 提取音频
        for pattern in self.audio_patterns:
            match = re.search(pattern, name)
            if match:
                metadata.audio = match.group(1).upper()
                break
        
        # 提取来源
        for pattern in self.source_patterns:
            match = re.search(pattern, name)
            if match:
                source = match.group(1)
                # 标准化来源名称
                if 'BLU' in source.upper() or 'BD' in source.upper():
                    metadata.source = 'BluRay'
                elif 'WEB' in source.upper():
                    metadata.source = 'WEB-DL'
                else:
                    metadata.source = source.upper()
                break
        
        # 提取季集信息
        for pattern in self.season_episode_patterns:
            match = re.search(pattern, name)
            if match:
                metadata.season = int(match.group(1))
                metadata.episode = int(match.group(2))
                metadata.media_type = MediaType.TV
                break
        
        # 提取年份
        match = re.search(self.year_pattern, name)
        if match:
            metadata.year = int(match.group(1))
        
        # 判断媒体类型
        if metadata.season is not None:
            metadata.media_type = MediaType.TV
        elif metadata.year and not metadata.season:
            metadata.media_type = MediaType.MOVIE
        
        # 提取标题（移除已识别的元数据）
        title = name
        # 移除分辨率、编码等信息
        for pattern in (self.resolution_patterns + self.codec_patterns + 
                       self.audio_patterns + self.source_patterns):
            title = re.sub(pattern, '', title)
        
        # 移除季集信息
        for pattern in self.season_episode_patterns:
            title = re.sub(pattern, '', title)
        
        # 移除年份
        title = re.sub(self.year_pattern, '', title)
        
        # 清理标题
        title = re.sub(r'[\[\](){}]', ' ', title)  # 移除括号
        title = re.sub(r'[._-]+', ' ', title)      # 替换分隔符
        title = re.sub(r'\s+', ' ', title)         # 合并空格
        title = title.strip()
        
        metadata.title = title if title else name
        
        logger.debug(f"✅ 解析文件名: {filename} -> {metadata.title}")
        return metadata
    
    def generate_filename(
        self,
        metadata: MediaMetadata,
        template: Optional[str] = None
    ) -> str:
        """
        生成标准化文件名
        
        Args:
            metadata: 元数据
            template: 自定义模板
        
        Returns:
            str: 标准化文件名
        """
        if template:
            # 使用自定义模板
            return self._apply_template(metadata, template)
        
        # 使用默认模板
        if metadata.media_type == MediaType.MOVIE:
            return self._generate_movie_filename(metadata)
        elif metadata.media_type == MediaType.TV:
            return self._generate_tv_filename(metadata)
        else:
            return self._generate_default_filename(metadata)
    
    def _generate_movie_filename(self, metadata: MediaMetadata) -> str:
        """生成电影文件名"""
        parts = [metadata.title]
        
        if metadata.year:
            parts.append(f"({metadata.year})")
        
        if metadata.resolution:
            parts.append(metadata.resolution)
        
        if metadata.source:
            parts.append(metadata.source)
        
        if metadata.codec:
            parts.append(metadata.codec)
        
        if metadata.audio:
            parts.append(metadata.audio)
        
        filename = '.'.join(parts)
        if metadata.extension:
            filename += f".{metadata.extension}"
        
        return filename
    
    def _generate_tv_filename(self, metadata: MediaMetadata) -> str:
        """生成电视剧文件名"""
        parts = [metadata.title]
        
        if metadata.season and metadata.episode:
            parts.append(f"S{metadata.season:02d}E{metadata.episode:02d}")
        
        if metadata.resolution:
            parts.append(metadata.resolution)
        
        if metadata.source:
            parts.append(metadata.source)
        
        if metadata.codec:
            parts.append(metadata.codec)
        
        filename = '.'.join(parts)
        if metadata.extension:
            filename += f".{metadata.extension}"
        
        return filename
    
    def _generate_default_filename(self, metadata: MediaMetadata) -> str:
        """生成默认文件名"""
        parts = [metadata.title]
        
        if metadata.resolution:
            parts.append(metadata.resolution)
        
        filename = '.'.join(parts)
        if metadata.extension:
            filename += f".{metadata.extension}"
        
        return filename
    
    def _apply_template(self, metadata: MediaMetadata, template: str) -> str:
        """应用自定义模板"""
        # 支持的占位符
        placeholders = {
            '{title}': metadata.title,
            '{year}': str(metadata.year) if metadata.year else '',
            '{season}': f"S{metadata.season:02d}" if metadata.season else '',
            '{episode}': f"E{metadata.episode:02d}" if metadata.episode else '',
            '{resolution}': metadata.resolution or '',
            '{codec}': metadata.codec or '',
            '{audio}': metadata.audio or '',
            '{source}': metadata.source or '',
            '{ext}': metadata.extension,
        }
        
        result = template
        for placeholder, value in placeholders.items():
            result = result.replace(placeholder, value)
        
        # 清理多余的点和空格
        result = re.sub(r'\.+', '.', result)
        result = re.sub(r'\s+', ' ', result)
        result = result.strip('. ')
        
        return result
    
    def rename_file(
        self,
        filename: str,
        template: Optional[str] = None
    ) -> str:
        """
        智能重命名文件
        
        Args:
            filename: 原文件名
            template: 自定义模板
        
        Returns:
            str: 新文件名
        """
        metadata = self.parse_filename(filename)
        new_filename = self.generate_filename(metadata, template)
        
        logger.info(f"✅ 重命名: {filename} -> {new_filename}")
        return new_filename
    
    def batch_rename(
        self,
        filenames: List[str],
        template: Optional[str] = None
    ) -> Dict[str, str]:
        """
        批量重命名
        
        Args:
            filenames: 文件名列表
            template: 自定义模板
        
        Returns:
            Dict[str, str]: 原文件名 -> 新文件名映射
        """
        result = {}
        for filename in filenames:
            try:
                new_filename = self.rename_file(filename, template)
                result[filename] = new_filename
            except Exception as e:
                logger.error(f"❌ 重命名失败: {filename}, 错误: {e}")
                result[filename] = filename  # 保持原文件名
        
        return result


# 全局单例
_smart_rename_service: Optional[SmartRenameService] = None


def get_smart_rename_service() -> SmartRenameService:
    """获取智能重命名服务单例"""
    global _smart_rename_service
    if _smart_rename_service is None:
        _smart_rename_service = SmartRenameService()
    return _smart_rename_service


# 便捷函数
def smart_rename(filename: str, template: Optional[str] = None) -> str:
    """
    智能重命名文件
    
    Args:
        filename: 原文件名
        template: 自定义模板
    
    Returns:
        str: 新文件名
    """
    service = get_smart_rename_service()
    return service.rename_file(filename, template)


def parse_media_filename(filename: str) -> MediaMetadata:
    """
    解析媒体文件名
    
    Args:
        filename: 文件名
    
    Returns:
        MediaMetadata: 元数据
    """
    service = get_smart_rename_service()
    return service.parse_filename(filename)

