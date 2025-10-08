/**
 * 媒体文件和下载任务 API 服务
 */
import axios from 'axios';
import type { MediaFile, DownloadTask, StorageUsage } from '../types/media';

const API_BASE = '/api/media';

export const mediaFilesApi = {
  // ==================== 下载任务 ====================
  
  /**
   * 获取下载任务列表
   */
  getTasks: async (params?: {
    status?: string;
    monitor_rule?: string;
    page?: number;
    page_size?: number;
  }) => {
    const { data } = await axios.get(`${API_BASE}/tasks`, { params });
    return data;
  },

  /**
   * 重试下载任务
   */
  retryTask: async (taskId: number) => {
    const { data } = await axios.post(`${API_BASE}/tasks/${taskId}/retry`);
    return data;
  },

  /**
   * 删除下载任务
   */
  deleteTask: async (taskId: number) => {
    const { data } = await axios.delete(`${API_BASE}/tasks/${taskId}`);
    return data;
  },

  /**
   * 更新任务优先级
   */
  updateTaskPriority: async (taskId: number, priority: number) => {
    const { data } = await axios.post(`${API_BASE}/tasks/${taskId}/priority`, null, {
      params: { priority }
    });
    return data;
  },

  /**
   * 获取任务统计
   */
  getTaskStats: async () => {
    const { data } = await axios.get(`${API_BASE}/tasks/stats`);
    return data;
  },

  // ==================== 媒体文件 ====================
  
  /**
   * 获取媒体文件列表
   */
  getFiles: async (params?: {
    keyword?: string;
    file_type?: string;
    monitor_rule?: string;
    organized?: string;
    cloud_status?: string;
    starred?: boolean;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) => {
    const { data } = await axios.get(`${API_BASE}/files`, { params });
    return data;
  },

  /**
   * 获取文件详情
   */
  getFile: async (fileId: number) => {
    const { data } = await axios.get(`${API_BASE}/files/${fileId}`);
    return data;
  },

  /**
   * 下载文件
   */
  downloadFile: async (fileId: number) => {
    const response = await axios.get(`${API_BASE}/download/${fileId}`, {
      responseType: 'blob',
    });
    return response;
  },

  /**
   * 收藏/取消收藏文件
   */
  toggleStar: async (fileId: number) => {
    const { data } = await axios.post(`${API_BASE}/files/${fileId}/star`);
    return data;
  },

  /**
   * 删除文件
   */
  deleteFile: async (fileId: number) => {
    const { data } = await axios.delete(`${API_BASE}/files/${fileId}`);
    return data;
  },

  /**
   * 获取文件统计
   */
  getFileStats: async () => {
    const { data } = await axios.get(`${API_BASE}/files/stats`);
    return data;
  },

  // ==================== 存储管理 ====================
  
  /**
   * 获取存储使用情况
   */
  getStorageUsage: async (ruleId?: number): Promise<StorageUsage> => {
    const params = ruleId ? { rule_id: ruleId } : {};
    const { data } = await axios.get(`${API_BASE}/storage/usage`, { params });
    return data;
  },

  /**
   * 手动清理存储
   */
  manualCleanup: async (params: {
    rule_id: number;
    days?: number;
    only_organized?: boolean;
    delete_db_records?: boolean;
  }) => {
    const { data } = await axios.post(`${API_BASE}/storage/cleanup`, null, { params });
    return data;
  },

  /**
   * 检查存储并自动清理
   */
  checkStorage: async (ruleId: number) => {
    const { data } = await axios.post(`${API_BASE}/storage/check`, null, {
      params: { rule_id: ruleId },
    });
    return data;
  },
};

