#!/usr/bin/env python3
"""
生成 gRPC Python 代码的脚本
"""
import subprocess
import sys
from pathlib import Path

def main():
    # 确保在正确的目录
    backend_dir = Path(__file__).parent
    proto_file = backend_dir / "protos" / "clouddrive2.proto"
    
    if not proto_file.exists():
        print(f"[ERROR] Proto file not found: {proto_file}")
        return 1
    
    print(f"[INFO] Proto file: {proto_file}")
    print(f"[INFO] Output dir: {backend_dir}")
    
    # 生成 Python 代码
    cmd = [
        sys.executable,
        "-m", "grpc_tools.protoc",
        f"-I{backend_dir}",
        f"--python_out={backend_dir}",
        f"--grpc_python_out={backend_dir}",
        str(proto_file)
    ]
    
    print(f"[RUN] Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("[SUCCESS] gRPC code generated!")
        print("\nGenerated files:")
        print(f"  - {backend_dir / 'protos' / 'clouddrive2_pb2.py'}")
        print(f"  - {backend_dir / 'protos' / 'clouddrive2_pb2_grpc.py'}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Generation failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return 1
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

