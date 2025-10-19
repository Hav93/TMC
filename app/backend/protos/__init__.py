"""
CloudDrive2 Protocol Buffers

官方 proto 生成的 Python 代码
"""

try:
    from . import clouddrive_pb2
    from . import clouddrive_pb2_grpc
    
    __all__ = ['clouddrive_pb2', 'clouddrive_pb2_grpc']
except ImportError:
    # proto 文件尚未生成
    pass

