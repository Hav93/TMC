#!/usr/bin/env python3
"""
生成 CloudDrive 官方 proto 的 Python gRPC 代码

使用官方 proto 文件: clouddrive.proto
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # 设置路径
    backend_dir = Path(__file__).parent
    proto_file = backend_dir / "protos" / "clouddrive.proto"
    protos_dir = backend_dir / "protos"
    
    if not proto_file.exists():
        print(f"[ERROR] Proto file not found: {proto_file}")
        return 1
    
    print(f"[INFO] Proto file: {proto_file}")
    print(f"[INFO] Output dir: {backend_dir}")
    
    # 先尝试安装 grpcio-tools
    print("[INFO] Checking grpcio-tools...")
    install_cmd = [sys.executable, "-m", "pip", "install", "grpcio-tools", "protobuf"]
    try:
        subprocess.run(install_cmd, check=True, capture_output=True)
        print("[SUCCESS] grpcio-tools installed")
    except Exception as e:
        print(f"[WARNING] Failed to install grpcio-tools: {e}")
    
    # 生成 Python 代码
    cmd = [
        sys.executable,
        "-m", "grpc_tools.protoc",
        f"--proto_path={protos_dir}",
        f"--python_out={backend_dir}",
        f"--grpc_python_out={backend_dir}",
        f"--pyi_out={backend_dir}",  # 生成类型提示文件
        str(proto_file)
    ]
    
    print(f"[RUN] Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[SUCCESS] gRPC code generated!")
        print("\nGenerated files:")
        print(f"  - {protos_dir / 'clouddrive_pb2.py'}")
        print(f"  - {protos_dir / 'clouddrive_pb2_grpc.py'}")
        print(f"  - {protos_dir / 'clouddrive_pb2.pyi'} (type hints)")
        
        # 修复import路径
        fix_imports(backend_dir)
        
        return 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Generation failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return 1
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return 1

def fix_imports(backend_dir):
    """修复生成文件中的 import 路径"""
    print("\n[INFO] Fixing import paths...")
    
    pb2_file = backend_dir / "protos" / "clouddrive_pb2.py"
    grpc_file = backend_dir / "protos" / "clouddrive_pb2_grpc.py"
    
    # 修复 clouddrive_pb2_grpc.py 中的 import
    if grpc_file.exists():
        content = grpc_file.read_text(encoding='utf-8')
        # 修改: import clouddrive_pb2 -> from . import clouddrive_pb2
        content = content.replace(
            'import clouddrive_pb2 as clouddrive__pb2',
            'from . import clouddrive_pb2 as clouddrive__pb2'
        )
        grpc_file.write_text(content, encoding='utf-8')
        print(f"[SUCCESS] Fixed imports in {grpc_file.name}")

if __name__ == "__main__":
    sys.exit(main())

