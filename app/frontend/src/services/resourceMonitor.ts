/**
 * 资源监控API服务
 */
import { apiClient } from './api';

export interface ResourceMonitorRule {
  id: number;
  name: string;
  source_chats: number[];
  include_keywords: string[];
  exclude_keywords: string[];
  monitor_pan115: boolean;
  monitor_magnet: boolean;
  monitor_ed2k: boolean;
  target_path: string;
  auto_save: boolean;
  is_active: boolean;
  total_captured: number;
  total_saved: number;
  created_at: string;
  updated_at: string;
}

export interface ResourceRecord {
  id: number;
  rule_id: number;
  rule_name: string;
  message_text: string;
  message_snapshot?: any;
  chat_id: string;
  chat_title: string;
  message_id: number;
  sender_name: string;
  pan115_links: string[];
  magnet_links: string[];
  ed2k_links: string[];
  tags: string[];
  status: 'pending' | 'saved' | 'failed' | 'ignored';
  target_path: string;
  error_message?: string;
  detected_at: string;
  saved_at?: string;
}

export interface ResourceRecordListResponse {
  success: boolean;
  records: ResourceRecord[];
  total: number;
  page: number;
  page_size: number;
}

export const resourceMonitorApi = {
  // ==================== 规则管理 ====================
  
  /**
   * 获取所有监控规则
   */
  getRules: () => {
    return apiClient.get<{ success: boolean; rules: ResourceMonitorRule[] }>('/api/resources/rules');
  },

  /**
   * 创建监控规则
   */
  createRule: (data: {
    name: string;
    source_chats: number[];
    include_keywords?: string[];
    exclude_keywords?: string[];
    monitor_pan115?: boolean;
    monitor_magnet?: boolean;
    monitor_ed2k?: boolean;
    target_path: string;
    auto_save?: boolean;
  }) => {
    return apiClient.post<{ success: boolean; message: string; rule_id: number }>('/api/resources/rules', data);
  },

  /**
   * 更新监控规则
   */
  updateRule: (ruleId: number, data: Partial<ResourceMonitorRule>) => {
    return apiClient.put<{ success: boolean; message: string }>(`/api/resources/rules/${ruleId}`, data);
  },

  /**
   * 删除监控规则
   */
  deleteRule: (ruleId: number) => {
    return apiClient.delete<{ success: boolean; message: string }>(`/api/resources/rules/${ruleId}`);
  },

  // ==================== 资源记录管理 ====================

  /**
   * 获取资源记录列表
   */
  getRecords: (params?: {
    rule_id?: number;
    status?: string;
    tags?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    return apiClient.get<ResourceRecordListResponse>('/api/resources/records', { params });
  },

  /**
   * 获取资源记录详情
   */
  getRecordDetail: (recordId: number) => {
    return apiClient.get<{ success: boolean; record: ResourceRecord }>(`/api/resources/records/${recordId}`);
  },

  // ==================== 标签管理 ====================

  /**
   * 添加标签
   */
  addTag: (recordId: number, tag: string) => {
    return apiClient.post<{ success: boolean; message: string; tags: string[] }>(
      `/api/resources/records/${recordId}/tags`,
      { tag }
    );
  },

  /**
   * 删除标签
   */
  removeTag: (recordId: number, tag: string) => {
    return apiClient.delete<{ success: boolean; message: string; tags: string[] }>(
      `/api/resources/records/${recordId}/tags/${tag}`
    );
  },

  // ==================== 批量操作 ====================

  /**
   * 批量操作
   */
  batchOperation: (data: {
    record_ids: number[];
    action: 'save' | 'delete' | 'ignore';
  }) => {
    return apiClient.post<{ success: boolean; message: string }>('/api/resources/records/batch', data);
  },
};

