"""
115网盘上传模块测试脚本
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from log_manager import get_logger
from upload115 import create_uploader

logger = get_logger('test_upload')


async def test_file_hash():
    """测试文件哈希计算"""
    from file_hash import calculate_sha1
    
    # 创建测试文件
    test_file = "test_file.txt"
    with open(test_file, 'w') as f:
        f.write("Hello, 115 Cloud!\n" * 1000)
    
    try:
        logger.info("测试文件哈希计算...")
        block_hash, total_hash = calculate_sha1(test_file)
        logger.info(f"✅ Block SHA1: {block_hash}")
        logger.info(f"✅ Total SHA1: {total_hash}")
        
        assert len(block_hash) == 40, "Block hash长度应为40"
        assert len(total_hash) == 40, "Total hash长度应为40"
        
        logger.info("✅ 文件哈希测试通过")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


async def test_ecdh_cipher():
    """测试ECDH加密"""
    from ecdh_cipher import create_ecdh_cipher
    
    logger.info("测试ECDH加密...")
    
    cipher = create_ecdh_cipher()
    
    # 测试加密解密
    plaintext = b"Hello, 115 Cloud! This is a test message."
    logger.info(f"明文: {plaintext}")
    
    # 加密
    ciphertext = cipher.encrypt(plaintext)
    logger.info(f"密文长度: {len(ciphertext)}")
    assert len(ciphertext) > 0, "密文不能为空"
    
    # 测试Token编码
    import time
    timestamp = int(time.time())
    k_ec = cipher.encode_token(timestamp)
    logger.info(f"k_ec: {k_ec}")
    assert len(k_ec) > 0, "k_ec不能为空"
    
    # 验证Base64编码
    import base64
    decoded = base64.b64decode(k_ec)
    assert len(decoded) == 48, "k_ec解码后应为48字节"
    
    logger.info("✅ ECDH加密测试通过")


async def test_upload_signature():
    """测试上传签名"""
    from upload_signature import create_signature_calculator
    
    logger.info("测试上传签名...")
    
    # 使用测试数据
    user_id = "123456"
    user_key = "test_user_key"
    
    signature = create_signature_calculator(user_id, user_key)
    
    # 测试sig计算
    file_id = "A" * 40  # 假设的SHA1
    target = "U_1_0"
    sig = signature.calculate_sig(file_id, target)
    logger.info(f"sig: {sig}")
    assert len(sig) == 40, "sig长度应为40"
    
    # 测试token计算
    file_size = "1024"
    token = signature.calculate_token(file_id, file_size)
    logger.info(f"token: {token}")
    assert len(token) == 32, "token长度应为32"
    
    # 测试表单构建
    form = signature.build_upload_form(
        "test.txt", 1024, file_id, "0"
    )
    logger.info(f"表单: {form[:100]}...")
    assert "userid=" in form, "表单应包含userid"
    assert "sig=" in form, "表单应包含sig"
    assert "token=" in form, "表单应包含token"
    
    logger.info("✅ 上传签名测试通过")


async def test_upload_real_file():
    """测试真实文件上传（需要配置）"""
    logger.info("=" * 60)
    logger.info("真实上传测试（需要配置用户信息）")
    logger.info("=" * 60)
    
    # 从环境变量读取配置
    user_id = os.getenv("TEST_115_USER_ID")
    user_key = os.getenv("TEST_115_USER_KEY")
    cookies = os.getenv("TEST_115_COOKIES")
    
    if not all([user_id, user_key, cookies]):
        logger.warning("⚠️  未配置测试账号，跳过真实上传测试")
        logger.info("提示：设置以下环境变量以启用真实上传测试：")
        logger.info("  TEST_115_USER_ID - 用户ID")
        logger.info("  TEST_115_USER_KEY - 用户密钥")
        logger.info("  TEST_115_COOKIES - Cookie字符串")
        return
    
    # 创建小测试文件
    test_file = "upload_test.txt"
    with open(test_file, 'w') as f:
        f.write("115 Upload Test\n" * 100)
    
    try:
        logger.info(f"创建上传器...")
        uploader = create_uploader(user_id, user_key, cookies, use_proxy=False)
        
        logger.info(f"开始上传测试文件: {test_file}")
        result = await uploader.upload_file(test_file, target_cid="0")
        
        logger.info(f"上传结果: {result}")
        
        if result['success']:
            logger.info("✅ 真实上传测试通过")
        else:
            logger.error(f"❌ 上传失败: {result['message']}")
    
    except Exception as e:
        logger.error(f"❌ 真实上传测试异常: {e}", exc_info=True)
    
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("115网盘上传模块测试")
    logger.info("=" * 60)
    
    try:
        # 基础功能测试
        await test_file_hash()
        logger.info("")
        
        await test_ecdh_cipher()
        logger.info("")
        
        await test_upload_signature()
        logger.info("")
        
        # 真实上传测试（可选）
        await test_upload_real_file()
        
        logger.info("=" * 60)
        logger.info("✅ 所有测试完成")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

