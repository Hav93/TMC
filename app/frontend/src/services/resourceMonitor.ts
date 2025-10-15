/**
 * 资源监控API服务
 * 
 * 功能：
 * - 资源监控规则管理
 * - 资源记录查询
 * - 统计信息获取
 */

import api from './api';

// ==================== 类型定义 ====================

/**
 * 关键词配置
 */
export interface KeywordConfig {
  keyword: string;
  mode?: 'contains' | 'regex' | 'exact' | 'starts_with' | 'ends_with';
  case_sensitive?: boolean;
  is_exclude?: boolean;
}

/**
 * 资源监控规则
 */
export interface ResourceMonitorRule {
  id?: number;
  name: string;
  source_chats: string[];
  is_active: boolean;
  link_types?: string[];
  keywords?: KeywordConfig[];
  auto_save_to_115: boolean;
  target_path?: string;
  pan115_user_key?: string;
  default_tags?: string[];
  enable_deduplication: boolean;
  dedup_time_window: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * 资源记录
 */
export interface ResourceRecord {
  id: number;
  rule_id: number;
  rule_name?: string;
  source_chat_id?: string;
  source_chat_name?: string;
  message_id?: number;
  message_text?: string;
  message_date?: string;
  link_type: string;
  link_url: string;
  link_hash?: string;
  save_status: 'pending' | 'saving' | 'success' | 'failed';
  save_path?: string;
  save_error?: string;
  save_time?: string;
  retry_count: number;
  tags?: string[];
  message_snapshot?: any;
  created_at: string;
  updated_at?: string;
}

/**
 * 资源监控统计
 */
export interface ResourceMonitorStats {
  total_rules: number;
  active_rules: number;
  total_records: number;
  saved_records: number;
  failed_records: number;
}

/**
 * 规则创建/更新参数
 */
export interface RuleFormData {
  name: string;
  source_chats: string[];
  is_active?: boolean;
  link_types?: string[];
  keywords?: KeywordConfig[];
  auto_save_to_115?: boolean;
  target_path?: string;
  pan115_user_key?: string;
  default_tags?: string[];
  enable_deduplication?: boolean;
  dedup_time_window?: number;
}

/**
 * 记录查询参数
 */
export interface RecordQueryParams {
  skip?: number;
  limit?: number;
  rule_id?: number;
  link_type?: string;
  save_status?: string;
  start_date?: string;
  end_date?: string;
}

// ==================== API方法 ====================

/**
 * 资源监控API服务类
 */
class ResourceMonitorService {
  private baseUrl = '/api/resources';

  // ==================== 规则管理 ====================

  /**
   * 获取所有规则
   */
  async getRules(): Promise<ResourceMonitorRule[]> {
    const response = await api.get<{ success: boolean; data: ResourceMonitorRule[] }>(`${this.baseUrl}/rules`);
    return response.data;
  }

  /**
   * 获取指定规则
   */
  async getRule(ruleId: number): Promise<ResourceMonitorRule> {
    const response = await api.get<{ success: boolean; data: ResourceMonitorRule }>(`${this.baseUrl}/rules/${ruleId}`);
    return response.data;
  }

  /**
   * 创建规则
   */
  async createRule(data: RuleFormData): Promise<ResourceMonitorRule> {
    const response = await api.post<{ success: boolean; data: ResourceMonitorRule }>(`${this.baseUrl}/rules`, data);
    return response.data;
  }

  /**
   * 更新规则
   */
  async updateRule(ruleId: number, data: RuleFormData): Promise<ResourceMonitorRule> {
    const response = await api.put<{ success: boolean; data: ResourceMonitorRule }>(`${this.baseUrl}/rules/${ruleId}`, data);
    return response.data;
  }

  /**
   * 删除规则
   */
  async deleteRule(ruleId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/rules/${ruleId}`);
  }

  /**
   * 切换规则启用状态
   */
  async toggleRule(ruleId: number, isActive: boolean): Promise<ResourceMonitorRule> {
    const rule = await this.getRule(ruleId);
    return await this.updateRule(ruleId, {
      ...rule,
      is_active: isActive
    });
  }

  // ==================== 记录管理 ====================

  /**
   * 获取所有记录
   */
  async getRecords(params?: RecordQueryParams): Promise<ResourceRecord[]> {
    const response = await api.get<{ 
      success: boolean; 
      data: { 
        records: ResourceRecord[]; 
        pagination?: any;
      } 
    }>(`${this.baseUrl}/records`, { params });
    // API返回的是 { success, data: { records, pagination } }
    return response.data.records || [];
  }

  /**
   * 获取指定记录
   */
  async getRecord(recordId: number): Promise<ResourceRecord> {
    const response = await api.get<{ success: boolean; data: ResourceRecord }>(`${this.baseUrl}/records/${recordId}`);
    return response.data;
  }

  /**
   * 重试失败的转存任务
   */
  async retryRecord(recordId: number): Promise<void> {
    // TODO: 实现重试接口
    await api.post(`${this.baseUrl}/records/${recordId}/retry`);
  }

  // ==================== 统计信息 ====================

  /**
   * 获取统计信息
   */
  async getStats(): Promise<ResourceMonitorStats> {
    const response = await api.get<{ success: boolean; data: ResourceMonitorStats }>(`${this.baseUrl}/stats`);
    return response.data;
  }

  // ==================== 批量操作 ====================

  /**
   * 批量删除规则
   */
  async batchDeleteRules(ruleIds: number[]): Promise<void> {
    await Promise.all(ruleIds.map(id => this.deleteRule(id)));
  }

  /**
   * 批量启用/禁用规则
   */
  async batchToggleRules(ruleIds: number[], isActive: boolean): Promise<void> {
    await Promise.all(ruleIds.map(id => this.toggleRule(id, isActive)));
  }
}

// 导出单例
export const resourceMonitorService = new ResourceMonitorService();

// 导出便捷方法
export const {
  getRules,
  getRule,
  createRule,
  updateRule,
  deleteRule,
  toggleRule,
  getRecords,
  getRecord,
  retryRecord,
  getStats,
  batchDeleteRules,
  batchToggleRules
} = resourceMonitorService;

export default resourceMonitorService;

