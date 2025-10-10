/**
 * 媒体管理相关的类型定义
 */

export interface MediaMonitorRule {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  client_id: string;
  
  // 监听源
  source_chats?: string; // JSON 格式
  
  // 媒体过滤
  media_types?: string; // JSON 格式
  min_size_mb?: number;
  max_size_mb?: number;
  filename_include?: string;
  filename_exclude?: string;
  file_extensions?: string; // JSON 格式
  
  // 发送者过滤
  enable_sender_filter?: boolean;
  sender_filter_mode?: 'whitelist' | 'blacklist';
  sender_whitelist?: string;
  sender_blacklist?: string;
  
  // 下载设置
  temp_folder?: string;
  concurrent_downloads?: number;
  retry_on_failure?: boolean;
  max_retries?: number;
  
  // 元数据提取
  extract_metadata?: boolean;
  metadata_mode?: 'disabled' | 'lightweight' | 'full';
  metadata_timeout?: number;
  async_metadata_extraction?: boolean;
  
  // 归档配置
  organize_enabled?: boolean;
  organize_target_type?: 'local' | 'clouddrive_mount' | 'clouddrive_api';
  organize_local_path?: string;
  organize_clouddrive_mount?: string;
  organize_mode?: 'copy' | 'move';
  keep_temp_file?: boolean;
  
  // CloudDrive API
  clouddrive_enabled?: boolean;
  clouddrive_url?: string;
  clouddrive_username?: string;
  clouddrive_password?: string;
  clouddrive_remote_path?: string;
  
  // 文件夹结构
  folder_structure?: 'flat' | 'date' | 'type' | 'source' | 'sender' | 'custom';
  custom_folder_template?: string;
  rename_files?: boolean;
  filename_template?: string;
  
  // 清理设置
  auto_cleanup_enabled?: boolean;
  auto_cleanup_days?: number;
  cleanup_only_organized?: boolean;
  
  // 存储容量限制
  max_storage_gb?: number;
  
  // 统计数据
  total_downloaded?: number;
  total_size_mb?: number;
  last_download_at?: string;
  failed_downloads?: number;
  
  // 时间戳
  created_at?: string;
  updated_at?: string;
}

export interface DownloadTask {
  id: number;
  monitor_rule_id: number;
  message_id?: number;
  chat_id?: string;
  file_name?: string;
  file_type?: string;
  file_size_mb?: number;
  status: 'pending' | 'downloading' | 'success' | 'failed';
  priority?: number;
  downloaded_bytes?: number;
  total_bytes?: number;
  progress_percent?: number;
  download_speed_mbps?: number;
  retry_count?: number;
  max_retries?: number;
  last_error?: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
}

export interface MediaFile {
  id: number;
  monitor_rule_id: number;
  download_task_id?: number;
  message_id?: number;
  temp_path?: string;
  final_path?: string;
  clouddrive_path?: string;
  file_hash?: string;
  file_name?: string;
  file_type?: string;
  file_size_mb?: number;
  extension?: string;
  original_name?: string;
  metadata?: Record<string, any>;
  width?: number;
  height?: number;
  duration_seconds?: number;
  resolution?: string;
  codec?: string;
  bitrate_kbps?: number;
  source_chat?: string;
  sender_id?: string;
  sender_username?: string;
  is_organized?: boolean;
  is_uploaded_to_cloud?: boolean;
  is_starred?: boolean;
  organize_failed?: boolean;
  organize_error?: string;
  downloaded_at?: string;
  organized_at?: string;
  uploaded_at?: string;
}

export interface StorageUsage {
  success: boolean;
  rule_id?: number;
  rule_name?: string;
  temp_size_gb?: number;
  organized_size_gb?: number;
  total_size_gb?: number;
  max_size_gb?: number;
  usage_percent?: number;
  total_downloaded?: number;
  total_size_mb?: number;
  rules?: Array<{
    rule_id: number;
    rule_name: string;
    temp_size_gb: number;
    organized_size_gb: number;
    total_size_gb: number;
  }>;
}
