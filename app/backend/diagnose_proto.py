#!/usr/bin/env python3
"""
诊断 proto 导入问题
"""
import sys
import os
from pathlib import Path

print("=" * 80)
print("CloudDrive2 Proto 导入诊断")
print("=" * 80)

# 1. 打印环境信息
print("\n📍 环境信息:")
print(f"   Python 版本: {sys.version}")
print(f"   当前工作目录: {os.getcwd()}")
print(f"   当前脚本路径: {Path(__file__).parent}")
print(f"   Python 路径 (sys.path):")
for i, p in enumerate(sys.path[:5], 1):
    print(f"      {i}. {p}")

# 2. 检查文件是否存在
print("\n📁 Proto 文件检查:")
backend_dir = Path(__file__).parent
protos_dir = backend_dir / "protos"

files_to_check = [
    protos_dir / "clouddrive.proto",
    protos_dir / "clouddrive_pb2.py",
    protos_dir / "clouddrive_pb2_grpc.py",
    protos_dir / "__init__.py",
]

for file in files_to_check:
    exists = "✅" if file.exists() else "❌"
    print(f"   {exists} {file}")
    if file.exists():
        print(f"      大小: {file.stat().st_size} bytes")

# 3. 尝试各种导入方式
print("\n🔍 尝试导入:")

# 方式 1: 直接导入
print("\n   方式 1: from protos import clouddrive_pb2")
try:
    from protos import clouddrive_pb2
    print("   ✅ 成功!")
except ImportError as e:
    print(f"   ❌ 失败: {e}")
    
    # 方式 2: 添加 backend 到 sys.path
    print("\n   方式 2: 添加 backend 到 sys.path 后导入")
    try:
        backend_path = str(backend_dir)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
            print(f"   ℹ️  已添加到 sys.path: {backend_path}")
        
        from protos import clouddrive_pb2
        print("   ✅ 成功!")
    except ImportError as e2:
        print(f"   ❌ 仍然失败: {e2}")
        
        # 方式 3: 使用 importlib
        print("\n   方式 3: 使用 importlib")
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "clouddrive_pb2",
                protos_dir / "clouddrive_pb2.py"
            )
            if spec and spec.loader:
                clouddrive_pb2 = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(clouddrive_pb2)
                print("   ✅ 成功!")
            else:
                print("   ❌ 无法创建 module spec")
        except Exception as e3:
            print(f"   ❌ 失败: {e3}")

# 4. 检查 proto 文件内容
print("\n📄 检查生成的 proto 文件:")
pb2_file = protos_dir / "clouddrive_pb2.py"
if pb2_file.exists():
    with open(pb2_file, 'r', encoding='utf-8') as f:
        first_lines = [f.readline() for _ in range(10)]
    print("   前10行:")
    for i, line in enumerate(first_lines, 1):
        print(f"      {i}. {line.rstrip()}")
else:
    print("   ❌ 文件不存在")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)

