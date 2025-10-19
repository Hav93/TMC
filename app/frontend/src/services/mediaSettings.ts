/**
 * 媒体管理全局配置 API 服务
 */
import { apiClient } from './api';
import type { MediaSettings } from '../types/settings';

const API_BASE = '/api/settings/media';

export interface LocalDirectory {
  name: string;
  path: string;
  size: number;
  modified: number;
}

export const mediaSettingsApi = {
  /**
   * 获取媒体配置
   */
  getSettings: async (): Promise<MediaSettings> => {
    const response = await apiClient.get(`${API_BASE}/`);
    return response.data;
  },

  /**
   * 更新媒体配置
   */
  updateSettings: async (data: MediaSettings): Promise<{ message: string; id: number }> => {
    const response = await apiClient.put(`${API_BASE}/`, data);
    return response.data;
  },

  /**
   * 获取本地目录列表
   */
  getLocalDirectories: async (
    path: string = '/app'
  ): Promise<{ success: boolean; directories: LocalDirectory[]; current_path: string; parent_path: string | null }> => {
    const response = await apiClient.get(`${API_BASE}/local-directories`, {
      params: { path },
    });
    return response.data;
  },

  /**
   * 创建本地目录
   */
  createLocalDirectory: async (
    path: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${API_BASE}/local-directory/create`, { path });
    return response.data;
  },

  /**
   * 重命名本地目录
   */
  renameLocalDirectory: async (
    old_path: string,
    new_path: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${API_BASE}/local-directory/rename`, {
      old_path,
      new_path,
    });
    return response.data;
  },

  /**
   * 删除本地目录
   */
  deleteLocalDirectory: async (
    path: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${API_BASE}/local-directory/delete`, { path });
    return response.data;
  },
};

