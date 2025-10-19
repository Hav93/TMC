"""
STRM文件生成服务

功能：
1. 生成STRM流媒体文件
2. 生成NFO元数据文件
3. 支持Emby/Jellyfin/Plex
4. 目录结构组织
"""
import os
from typing import Optional, Dict
from dataclasses import dataclass

from log_manager import get_logger

logger = get_logger("strm_generator", "enhanced_bot.log")


@dataclass
class StrmConfig:
    """STRM配置"""
    media_url: str                  # 媒体URL
    output_dir: str                 # 输出目录
    filename: str                   # 文件名（不含扩展名）
    title: Optional[str] = None     # 标题
    year: Optional[int] = None      # 年份
    plot: Optional[str] = None      # 简介
    genre: Optional[str] = None     # 类型
    rating: Optional[float] = None  # 评分


class StrmGenerator:
    """
    STRM文件生成器
    
    功能：
    1. 生成STRM文件（包含媒体URL）
    2. 生成NFO元数据文件
    3. 组织目录结构
    """
    
    def __init__(self):
        """初始化STRM生成器"""
        pass
    
    def generate_strm(self, config: StrmConfig) -> str:
        """
        生成STRM文件
        
        Args:
            config: STRM配置
        
        Returns:
            str: STRM文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(config.output_dir, exist_ok=True)
            
            # STRM文件路径
            strm_path = os.path.join(config.output_dir, f"{config.filename}.strm")
            
            # 写入媒体URL
            with open(strm_path, 'w', encoding='utf-8') as f:
                f.write(config.media_url)
            
            logger.info(f"✅ 生成STRM文件: {strm_path}")
            return strm_path
            
        except Exception as e:
            logger.error(f"❌ 生成STRM文件失败: {e}", exc_info=True)
            raise
    
    def generate_nfo(self, config: StrmConfig, nfo_type: str = "movie") -> str:
        """
        生成NFO元数据文件
        
        Args:
            config: STRM配置
            nfo_type: NFO类型（movie/tvshow/episode）
        
        Returns:
            str: NFO文件路径
        """
        try:
            # 确保输出目录存在
            os.makedirs(config.output_dir, exist_ok=True)
            
            # NFO文件路径
            nfo_path = os.path.join(config.output_dir, f"{config.filename}.nfo")
            
            # 生成NFO内容
            if nfo_type == "movie":
                nfo_content = self._generate_movie_nfo(config)
            elif nfo_type == "tvshow":
                nfo_content = self._generate_tvshow_nfo(config)
            else:
                nfo_content = self._generate_movie_nfo(config)
            
            # 写入NFO文件
            with open(nfo_path, 'w', encoding='utf-8') as f:
                f.write(nfo_content)
            
            logger.info(f"✅ 生成NFO文件: {nfo_path}")
            return nfo_path
            
        except Exception as e:
            logger.error(f"❌ 生成NFO文件失败: {e}", exc_info=True)
            raise
    
    def _generate_movie_nfo(self, config: StrmConfig) -> str:
        """生成电影NFO"""
        title = config.title or config.filename
        year = config.year or ""
        plot = config.plot or ""
        genre = config.genre or ""
        rating = config.rating or 0.0
        
        nfo = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{title}</title>
    <originaltitle>{title}</originaltitle>
    <year>{year}</year>
    <plot>{plot}</plot>
    <genre>{genre}</genre>
    <rating>{rating}</rating>
</movie>"""
        
        return nfo
    
    def _generate_tvshow_nfo(self, config: StrmConfig) -> str:
        """生成电视剧NFO"""
        title = config.title or config.filename
        year = config.year or ""
        plot = config.plot or ""
        genre = config.genre or ""
        rating = config.rating or 0.0
        
        nfo = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
    <title>{title}</title>
    <originaltitle>{title}</originaltitle>
    <year>{year}</year>
    <plot>{plot}</plot>
    <genre>{genre}</genre>
    <rating>{rating}</rating>
</tvshow>"""
        
        return nfo
    
    def generate_complete(
        self,
        config: StrmConfig,
        include_nfo: bool = True,
        nfo_type: str = "movie"
    ) -> Dict[str, str]:
        """
        生成完整的STRM和NFO文件
        
        Args:
            config: STRM配置
            include_nfo: 是否生成NFO
            nfo_type: NFO类型
        
        Returns:
            Dict: 生成的文件路径
        """
        result = {}
        
        # 生成STRM
        strm_path = self.generate_strm(config)
        result['strm'] = strm_path
        
        # 生成NFO
        if include_nfo:
            nfo_path = self.generate_nfo(config, nfo_type)
            result['nfo'] = nfo_path
        
        return result


# 全局单例
_strm_generator: Optional[StrmGenerator] = None


def get_strm_generator() -> StrmGenerator:
    """获取STRM生成器单例"""
    global _strm_generator
    if _strm_generator is None:
        _strm_generator = StrmGenerator()
    return _strm_generator


# 便捷函数
def generate_strm_file(
    media_url: str,
    output_dir: str,
    filename: str,
    **kwargs
) -> Dict[str, str]:
    """
    生成STRM文件
    
    Args:
        media_url: 媒体URL
        output_dir: 输出目录
        filename: 文件名
        **kwargs: 其他配置
    
    Returns:
        Dict: 生成的文件路径
    """
    config = StrmConfig(
        media_url=media_url,
        output_dir=output_dir,
        filename=filename,
        **kwargs
    )
    
    generator = get_strm_generator()
    return generator.generate_complete(config)

