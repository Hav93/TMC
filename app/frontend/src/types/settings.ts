/**
 * 媒体管理全局配置类型定义
 */
export interface MediaSettings {
  id?: number;
  
  // CloudDrive 配置
  clouddrive_enabled: boolean;
  clouddrive_url?: string;
  clouddrive_username?: string;
  clouddrive_password?: string;
  clouddrive_remote_path: string;
  
  // 下载设置
  temp_folder: string;
  concurrent_downloads: number;
  retry_on_failure: boolean;
  max_retries: number;
  
  // 元数据提取
  extract_metadata: boolean;
  metadata_mode: 'disabled' | 'lightweight' | 'full';
  metadata_timeout: number;
  async_metadata_extraction: boolean;
  
  // 存储清理
  auto_cleanup_enabled: boolean;
  auto_cleanup_days: number;
  cleanup_only_organized: boolean;
  max_storage_gb: number;
  
  // 时间戳
  created_at?: string;
  updated_at?: string;
}

