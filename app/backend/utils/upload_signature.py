"""
115网盘上传签名算法
基于 fake115uploader 的签名实现
"""
import hashlib
import time
from typing import Dict, Optional
from urllib.parse import urlencode


class UploadSignature:
    """115上传签名计算器"""
    
    # MD5盐值（用于token计算）
    MD5_SALT = "Qclm8MGWUv59TnrR0XPg"
    
    # 应用版本号
    APP_VERSION = "30.5.1"
    
    # 签名结束字符串
    END_STRING = "000000"
    
    def __init__(self, user_id: str, user_key: str):
        """
        初始化签名计算器
        
        Args:
            user_id: 用户ID
            user_key: 用户密钥（从 /app/uploadinfo 接口获取）
        """
        self.user_id = user_id
        self.user_key = user_key
    
    def calculate_sig(self, file_id: str, target: str) -> str:
        """
        计算sig签名
        
        算法: sig = SHA1(userKey + SHA1(userID + fileID + target + "0") + "000000")
        
        Args:
            file_id: 文件ID（文件SHA1大写）
            target: 目标目录（格式: "U_1_{cid}"）
            
        Returns:
            sig签名（大写）
        """
        # 第一次SHA1: userID + fileID + target + "0"
        hash1_str = f"{self.user_id}{file_id}{target}0"
        hash1 = hashlib.sha1(hash1_str.encode()).hexdigest()
        
        # 第二次SHA1: userKey + hash1 + "000000"
        sig_str = f"{self.user_key}{hash1}{self.END_STRING}"
        sig = hashlib.sha1(sig_str.encode()).hexdigest().upper()
        
        return sig
    
    def calculate_token(self, file_id: str, file_size: str, 
                       sign_key: str = "", sign_val: str = "",
                       timestamp: Optional[int] = None) -> str:
        """
        计算token签名
        
        算法: token = MD5(salt + fileID + fileSize + signKey + signVal + 
                         userID + timestamp + MD5(userID) + appVersion)
        
        Args:
            file_id: 文件ID（文件SHA1大写）
            file_size: 文件大小（字符串）
            sign_key: 二次验证key（可选）
            sign_val: 二次验证value（可选）
            timestamp: Unix时间戳（可选，默认使用当前时间）
            
        Returns:
            token签名（小写）
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # 计算userID的MD5
        user_id_md5 = hashlib.md5(self.user_id.encode()).hexdigest()
        
        # 构造token字符串
        token_str = (
            f"{self.MD5_SALT}"
            f"{file_id}"
            f"{file_size}"
            f"{sign_key}"
            f"{sign_val}"
            f"{self.user_id}"
            f"{timestamp}"
            f"{user_id_md5}"
            f"{self.APP_VERSION}"
        )
        
        # 计算MD5
        token = hashlib.md5(token_str.encode()).hexdigest()
        
        return token
    
    def build_upload_form(self, filename: str, file_size: int, 
                         file_id: str, target_cid: str,
                         sign_key: str = "", sign_val: str = "",
                         timestamp: Optional[int] = None) -> str:
        """
        构建上传表单数据（用于ECDH加密）
        
        Args:
            filename: 文件名
            file_size: 文件大小
            file_id: 文件ID（SHA1大写）
            target_cid: 目标目录ID
            sign_key: 二次验证key（可选）
            sign_val: 二次验证value（可选）
            timestamp: Unix时间戳（可选）
            
        Returns:
            URL编码的表单字符串
        """
        if timestamp is None:
            timestamp = int(time.time())
        
        # 构造target
        target = f"U_1_{target_cid}"
        
        # 计算sig
        sig = self.calculate_sig(file_id, target)
        
        # 计算token
        file_size_str = str(file_size)
        token = self.calculate_token(
            file_id, file_size_str, sign_key, sign_val, timestamp
        )
        
        # 构造表单数据
        form_data = {
            'userid': self.user_id,
            'filename': filename,
            'filesize': file_size_str,
            'fileid': file_id,
            'target': target,
            'sig': sig,
            't': str(timestamp),
            'token': token,
        }
        
        # 添加二次验证参数（如果有）
        if sign_key and sign_val:
            form_data['sign_key'] = sign_key
            form_data['sign_val'] = sign_val
        
        # URL编码
        return urlencode(form_data)


def create_signature_calculator(user_id: str, user_key: str) -> UploadSignature:
    """创建签名计算器实例"""
    return UploadSignature(user_id, user_key)

