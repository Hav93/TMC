/**
 * 媒体监控 API 服务
 */
import axios from 'axios';
import type { MediaMonitorRule } from '../types/media';

const API_BASE = '/api/media/monitor';

export const mediaMonitorApi = {
  /**
   * 获取监控规则列表
   */
  getRules: async (params?: { is_active?: boolean; client_id?: string; page?: number; page_size?: number }) => {
    const { data } = await axios.get(`${API_BASE}/rules`, { params });
    return data;
  },

  /**
   * 获取单个监控规则
   */
  getRule: async (id: number) => {
    const { data } = await axios.get(`${API_BASE}/rules/${id}`);
    return data;
  },

  /**
   * 创建监控规则
   */
  createRule: async (rule: Partial<MediaMonitorRule>) => {
    const { data } = await axios.post(`${API_BASE}/rules`, rule);
    return data;
  },

  /**
   * 更新监控规则
   */
  updateRule: async (id: number, rule: Partial<MediaMonitorRule>) => {
    const { data } = await axios.put(`${API_BASE}/rules/${id}`, rule);
    return data;
  },

  /**
   * 删除监控规则
   */
  deleteRule: async (id: number) => {
    const { data } = await axios.delete(`${API_BASE}/rules/${id}`);
    return data;
  },

  /**
   * 切换规则启用状态
   */
  toggleRule: async (id: number) => {
    const { data } = await axios.post(`${API_BASE}/rules/${id}/toggle`);
    return data;
  },

  /**
   * 获取规则统计
   */
  getRuleStats: async (id: number) => {
    const { data } = await axios.get(`${API_BASE}/rules/${id}/stats`);
    return data;
  },
};

