/**
 * 媒体管理全局配置 API 服务
 */
import { apiClient } from './api';
import type { MediaSettings } from '../types/settings';

const API_BASE = '/api/settings/media';

export interface CloudDriveDirectory {
  name: string;
  path: string;
  size: number;
  modified?: string;
}

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
   * 测试 CloudDrive 连接
   */
  testCloudDrive: async (data: MediaSettings): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${API_BASE}/test-clouddrive`, data);
    return response.data;
  },

  /**
   * 浏览 CloudDrive 目录
   */
  browseCloudDrive: async (
    url: string,
    username: string | null,
    password: string | null,
    path: string = '/'
  ): Promise<{ success: boolean; directories: CloudDriveDirectory[]; current_path: string; message?: string }> => {
    const response = await apiClient.post(`${API_BASE}/clouddrive/browse`, {
      clouddrive_url: url,
      clouddrive_username: username,
      clouddrive_password: password,
      path,
    });
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

