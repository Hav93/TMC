/**
 * CloudDrive2 配置 API 服务
 */
import { apiClient } from './api';

const API_BASE = '/api/settings/clouddrive2';

export interface CloudDrive2Config {
  enabled: boolean;
  host: string;
  port: number;
  username: string;
  password: string;
  mount_point: string;
}

export const clouddrive2SettingsApi = {
  /**
   * 获取CloudDrive2配置
   */
  getConfig: async (): Promise<CloudDrive2Config> => {
    const response = await apiClient.get(`${API_BASE}/`);
    return response.data;
  },

  /**
   * 更新CloudDrive2配置
   */
  updateConfig: async (data: CloudDrive2Config): Promise<{ message: string; note: string }> => {
    const response = await apiClient.put(`${API_BASE}/`, data);
    return response.data;
  },

  /**
   * 测试CloudDrive2连接
   */
  testConnection: async (data: CloudDrive2Config): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${API_BASE}/test`, data);
    return response.data;
  },

  /**
   * 浏览目录（仅返回文件夹）
   */
  browse: async (payload: { host: string; port: number; username?: string; password?: string; path: string }): Promise<{ success: boolean; path: string; items: { name: string; path: string }[] }> => {
    const response = await apiClient.post(`${API_BASE}/browse`, payload);
    return response.data;
  },
};

