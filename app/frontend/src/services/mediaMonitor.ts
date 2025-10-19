/**
 * 媒体监控 API 服务
 */
import { apiClient } from './api';
import type { MediaMonitorRule } from '../types/media';

const API_BASE = '/api/media/monitor';

export const mediaMonitorApi = {
  /**
   * 获取监控规则列表
   */
  getRules: async (params?: { is_active?: boolean; client_id?: string; page?: number; page_size?: number }) => {
    const { data } = await apiClient.get(`${API_BASE}/rules`, { params });
    return data;
  },

  /**
   * 获取单个监控规则
   */
  getRule: async (id: number) => {
    const { data } = await apiClient.get(`${API_BASE}/rules/${id}`);
    return data;
  },

  /**
   * 创建监控规则
   */
  createRule: async (rule: Partial<MediaMonitorRule>) => {
    const { data } = await apiClient.post(`${API_BASE}/rules`, rule);
    return data;
  },

  /**
   * 更新监控规则
   */
  updateRule: async (id: number, rule: Partial<MediaMonitorRule>) => {
    const { data } = await apiClient.put(`${API_BASE}/rules/${id}`, rule);
    return data;
  },

  /**
   * 删除监控规则
   */
  deleteRule: async (id: number) => {
    const { data } = await apiClient.delete(`${API_BASE}/rules/${id}`);
    return data;
  },

  /**
   * 切换规则启用状态
   */
  toggleRule: async (id: number) => {
    const { data } = await apiClient.post(`${API_BASE}/rules/${id}/toggle`);
    return data;
  },

  /**
   * 获取全局监控统计（用于仪表盘）
   */
  getGlobalStats: async () => {
    const { data } = await apiClient.get(`${API_BASE}/stats`);
    return data;
  },

  /**
   * 获取单个规则统计
   */
  getRuleStats: async (id: number) => {
    const { data } = await apiClient.get(`${API_BASE}/rules/${id}/stats`);
    return data;
  },
};

