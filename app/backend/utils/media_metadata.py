"""
媒体元数据提取工具
支持图片、视频、音频文件的元数据提取
"""
import asyncio
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
from core.logger import logger

# 线程池用于执行阻塞的元数据提取操作
_executor = ThreadPoolExecutor(max_workers=2)


class MediaMetadataExtractor:
    """媒体元数据提取器（性能优化版）"""
    
    @staticmethod
    async def extract_metadata_async(
        file_path: str,
        mode: str = 'lightweight',
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        异步提取元数据
        
        Args:
            file_path: 文件路径
            mode: 提取模式 (disabled/lightweight/full)
            timeout: 超时时间（秒）
            
        Returns:
            元数据字典
        """
        if mode == 'disabled':
            return MediaMetadataExtractor._extract_basic_metadata(file_path)
        
        try:
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    _executor,
                    MediaMetadataExtractor._extract_metadata_sync,
                    file_path,
                    mode
                ),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(f"元数据提取超时: {file_path}")
            return {
                'error': '元数据提取超时（文件过大）',
                'type': 'unknown',
                'lightweight_mode': True
            }
        except Exception as e:
            logger.error(f"元数据提取失败: {file_path}, {e}")
            return {
                'error': str(e),
                'type': 'unknown'
            }
    
    @staticmethod
    def _extract_metadata_sync(file_path: str, mode: str) -> Dict[str, Any]:
        """同步提取元数据（在线程池中执行）"""
        file_ext = Path(file_path).suffix.lower()
        
        if mode == 'lightweight':
            # 轻量级模式：快速提取基础信息
            return MediaMetadataExtractor._extract_lightweight_metadata(file_path, file_ext)
        else:
            # 完整模式：提取详细元数据
            return MediaMetadataExtractor._extract_full_metadata(file_path, file_ext)
    
    @staticmethod
    def _extract_basic_metadata(file_path: str) -> Dict[str, Any]:
        """提取基础文件信息（最快，无需第三方库）"""
        try:
            stat = Path(file_path).stat()
            file_ext = Path(file_path).suffix.lower()
            
            return {
                'type': 'document',
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_ext,
                'filename': Path(file_path).name,
                'mode': 'basic'
            }
        except Exception as e:
            logger.error(f"基础元数据提取失败: {e}")
            return {'type': 'document', 'error': str(e)}
    
    @staticmethod
    def _extract_lightweight_metadata(file_path: str, file_ext: str) -> Dict[str, Any]:
        """
        轻量级元数据提取（推荐）
        - 图片：使用 Pillow 读取尺寸
        - 视频/音频：使用 mediainfo 快速获取基础信息
        - 低性能消耗，适合大多数场景
        """
        try:
            stat = Path(file_path).stat()
            
            metadata = {
                'type': 'document',
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_ext,
                'filename': Path(file_path).name,
                'mode': 'lightweight'
            }
            
            # 图片：只读取尺寸（不加载完整图片）
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        metadata.update({
                            'type': 'image',
                            'width': img.width,
                            'height': img.height,
                            'resolution': f"{img.width}x{img.height}",
                            'format': img.format,
                            'mode': img.mode  # RGB, RGBA, etc.
                        })
                except ImportError:
                    logger.warning("Pillow 未安装，跳过图片元数据提取")
                    metadata['type'] = 'image'
                except Exception as e:
                    logger.warning(f"图片元数据提取失败: {e}")
                    metadata['type'] = 'image'
            
            # 视频
            elif file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm']:
                metadata['type'] = 'video'
                # 尝试使用 mediainfo（比 ffprobe 更快）
                try:
                    import subprocess
                    cmd = ['mediainfo', '--Output=JSON', file_path]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        tracks = data.get('media', {}).get('track', [])
                        
                        # 提取视频轨道信息
                        video_track = next((t for t in tracks if t.get('@type') == 'Video'), {})
                        if video_track:
                            metadata.update({
                                'width': int(video_track.get('Width', 0)),
                                'height': int(video_track.get('Height', 0)),
                                'resolution': f"{video_track.get('Width', 0)}x{video_track.get('Height', 0)}",
                                'duration_seconds': float(video_track.get('Duration', 0)),
                                'codec': video_track.get('Format', 'unknown'),
                                'fps': float(video_track.get('FrameRate', 0))
                            })
                        
                        # 提取通用信息
                        general_track = next((t for t in tracks if t.get('@type') == 'General'), {})
                        if general_track:
                            duration = float(general_track.get('Duration', 0))
                            metadata['duration_seconds'] = duration
                            metadata['duration_formatted'] = MediaMetadataExtractor._format_duration(duration)
                            
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.debug(f"mediainfo 不可用或超时，跳过视频元数据")
                except Exception as e:
                    logger.warning(f"视频元数据提取失败: {e}")
            
            # 音频
            elif file_ext in ['.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg', '.wma']:
                metadata['type'] = 'audio'
                try:
                    import subprocess
                    cmd = ['mediainfo', '--Output=JSON', file_path]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        tracks = data.get('media', {}).get('track', [])
                        
                        # 提取音频轨道信息
                        audio_track = next((t for t in tracks if t.get('@type') == 'Audio'), {})
                        if audio_track:
                            metadata.update({
                                'duration_seconds': float(audio_track.get('Duration', 0)),
                                'codec': audio_track.get('Format', 'unknown'),
                                'channels': int(audio_track.get('Channels', 0)),
                                'sample_rate': int(audio_track.get('SamplingRate', 0))
                            })
                        
                        # 提取通用信息
                        general_track = next((t for t in tracks if t.get('@type') == 'General'), {})
                        if general_track:
                            duration = float(general_track.get('Duration', 0))
                            metadata['duration_seconds'] = duration
                            metadata['duration_formatted'] = MediaMetadataExtractor._format_duration(duration)
                            
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.debug(f"mediainfo 不可用或超时，跳过音频元数据")
                except Exception as e:
                    logger.warning(f"音频元数据提取失败: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"轻量级元数据提取失败: {e}")
            return {
                'type': 'document',
                'error': str(e),
                'mode': 'lightweight'
            }
    
    @staticmethod
    def _extract_full_metadata(file_path: str, file_ext: str) -> Dict[str, Any]:
        """
        完整元数据提取（详细模式）
        - 使用 ffprobe 提取详细的视频/音频信息
        - 性能消耗较高，适合专业归档需求
        """
        try:
            stat = Path(file_path).stat()
            
            metadata = {
                'type': 'document',
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_ext,
                'filename': Path(file_path).name,
                'mode': 'full'
            }
            
            # 图片：使用 Pillow 提取详细信息
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        metadata.update({
                            'type': 'image',
                            'width': img.width,
                            'height': img.height,
                            'resolution': f"{img.width}x{img.height}",
                            'format': img.format,
                            'mode': img.mode,
                            'aspect_ratio': round(img.width / img.height, 2) if img.height > 0 else 0
                        })
                        
                        # 提取 EXIF 信息（如果有）
                        if hasattr(img, '_getexif') and img._getexif():
                            exif = img._getexif()
                            metadata['has_exif'] = True
                        else:
                            metadata['has_exif'] = False
                            
                except ImportError:
                    logger.warning("Pillow 未安装")
                    metadata['type'] = 'image'
                except Exception as e:
                    logger.warning(f"图片完整元数据提取失败: {e}")
                    metadata['type'] = 'image'
            
            # 视频/音频：使用 ffprobe
            elif file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm', 
                              '.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg', '.wma']:
                
                is_video = file_ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm']
                metadata['type'] = 'video' if is_video else 'audio'
                
                try:
                    import subprocess
                    cmd = [
                        'ffprobe',
                        '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format',
                        '-show_streams',
                        file_path
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        
                        # 解析视频流
                        if is_video:
                            video_stream = next(
                                (s for s in data.get('streams', []) if s['codec_type'] == 'video'),
                                {}
                            )
                            
                            if video_stream:
                                metadata.update({
                                    'width': video_stream.get('width', 0),
                                    'height': video_stream.get('height', 0),
                                    'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                                    'codec': video_stream.get('codec_name', 'unknown'),
                                    'profile': video_stream.get('profile', 'unknown'),
                                    'pixel_format': video_stream.get('pix_fmt', 'unknown'),
                                    'bitrate_kbps': int(video_stream.get('bit_rate', 0)) // 1000 if video_stream.get('bit_rate') else 0
                                })
                                
                                # 计算帧率
                                if 'r_frame_rate' in video_stream:
                                    fps_str = video_stream['r_frame_rate']
                                    if '/' in fps_str:
                                        num, den = fps_str.split('/')
                                        metadata['fps'] = round(int(num) / int(den), 2) if int(den) > 0 else 0
                        
                        # 解析音频流
                        audio_stream = next(
                            (s for s in data.get('streams', []) if s['codec_type'] == 'audio'),
                            {}
                        )
                        
                        if audio_stream:
                            metadata.update({
                                'audio_codec': audio_stream.get('codec_name', 'unknown'),
                                'audio_channels': audio_stream.get('channels', 0),
                                'audio_sample_rate': audio_stream.get('sample_rate', 0),
                                'audio_bitrate_kbps': int(audio_stream.get('bit_rate', 0)) // 1000 if audio_stream.get('bit_rate') else 0
                            })
                        
                        # 解析容器格式信息
                        format_info = data.get('format', {})
                        if format_info:
                            duration = float(format_info.get('duration', 0))
                            metadata.update({
                                'duration_seconds': duration,
                                'duration_formatted': MediaMetadataExtractor._format_duration(duration),
                                'format': format_info.get('format_name', 'unknown'),
                                'bitrate_kbps': int(format_info.get('bit_rate', 0)) // 1000 if format_info.get('bit_rate') else 0
                            })
                            
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    logger.warning(f"ffprobe 不可用或超时")
                except Exception as e:
                    logger.warning(f"完整元数据提取失败: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"完整元数据提取失败: {e}")
            return {
                'type': 'document',
                'error': str(e),
                'mode': 'full'
            }
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if not seconds or seconds <= 0:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# 测试函数
async def test_metadata_extraction():
    """测试元数据提取"""
    test_files = [
        '/path/to/test.jpg',
        '/path/to/test.mp4',
        '/path/to/test.mp3'
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n测试文件: {file_path}")
            
            # 测试轻量级模式
            metadata = await MediaMetadataExtractor.extract_metadata_async(
                file_path,
                mode='lightweight',
                timeout=10
            )
            print(f"轻量级模式: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
            
            # 测试完整模式
            metadata = await MediaMetadataExtractor.extract_metadata_async(
                file_path,
                mode='full',
                timeout=30
            )
            print(f"完整模式: {json.dumps(metadata, indent=2, ensure_ascii=False)}")


if __name__ == '__main__':
    # 运行测试
    asyncio.run(test_metadata_extraction())

