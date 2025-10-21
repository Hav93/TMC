/**
 * 推送通知系统 API 服务
 * 
 * 功能：
 * - 通知规则管理
 * - 通知历史查询
 * - 测试通知发送
 * - 统计信息获取
 */

import api from './api';

// ==================== 类型定义 ====================

/**
 * 通知类型枚举
 */
export type NotificationType = 
  | 'resource_captured'      // 资源捕获
  | 'save_115_success'       // 115转存成功
  | 'save_115_failed'        // 115转存失败
  | 'download_complete'      // 下载完成
  | 'download_failed'        // 下载失败
  | 'download_progress'      // 下载进度
  | 'forward_success'        // 转发成功
  | 'forward_failed'         // 转发失败
  | 'task_stale'             // 任务卡住
  | 'storage_warning'        // 存储警告
  | 'daily_report'           // 每日报告
  | 'system_error';          // 系统错误

/**
 * 通知渠道枚举
 */
export type NotificationChannel = 
  | 'telegram'
  | 'webhook'
  | 'email';

/**
 * 通知规则
 */
export interface NotificationRule {
  id?: number;
  user_id?: number;
  notification_type: NotificationType;
  notification_types?: NotificationType[] | string;
  is_active: boolean;
  
  // Telegram配置
  telegram_chat_id?: string;
  telegram_client_id?: string;
  telegram_client_type?: 'user' | 'bot';
  telegram_enabled: boolean;
  // Bot 通知
  bot_enabled?: boolean;
  bot_recipients?: string[] | string;
  
  // Webhook配置
  webhook_url?: string;
  webhook_enabled: boolean;
  
  // Email配置
  email_address?: string;
  email_enabled: boolean;
  
  // 频率控制
  min_interval: number;        // 最小间隔（秒）
  max_per_hour: number;        // 每小时最大数量
  last_sent_at?: string;       // 最后发送时间
  sent_count_hour: number;     // 当前小时已发送数量
  hour_reset_at?: string;      // 小时计数器重置时间
  
  // 模板
  custom_template?: string;
  include_details: boolean;
  
  // 时间戳
  created_at?: string;
  updated_at?: string;
}

/**
 * 通知历史
 */
export interface NotificationLog {
  id: number;
  notification_type: NotificationType;
  message: string;
  channels: string;            // 逗号分隔的渠道列表
  user_id?: number;
  status: 'pending' | 'sent' | 'failed';
  error_message?: string;
  related_type?: string;
  related_id?: number;
  sent_at: string;
}

/**
 * 通知统计
 */
export interface NotificationStats {
  total_rules: number;
  active_rules: number;
  total_sent_today: number;
  total_failed_today: number;
  by_type: Record<NotificationType, {
    total: number;
    success: number;
    failed: number;
  }>;
  by_channel: Record<NotificationChannel, {
    total: number;
    success: number;
    failed: number;
  }>;
}

/**
 * 通知类型信息
 */
export interface NotificationTypeInfo {
  type: NotificationType;
  name: string;
  description: string;
  default_template: string;
}

/**
 * 规则表单数据
 */
export interface RuleFormData {
  notification_type: NotificationType;
  notification_types?: NotificationType[];
  is_active: boolean;
  telegram_chat_id?: string;
  telegram_enabled: boolean;
  telegram_client_id?: string;
  telegram_client_type?: 'user' | 'bot';
  bot_enabled?: boolean;
  bot_recipients?: string[];
  webhook_url?: string;
  webhook_enabled: boolean;
  email_address?: string;
  email_enabled: boolean;
  min_interval: number;
  max_per_hour: number;
  custom_template?: string;
  include_details: boolean;
}

/**
 * 日志查询参数
 */
export interface LogQueryParams {
  notification_type?: NotificationType;
  status?: 'pending' | 'sent' | 'failed';
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// ==================== API 服务类 ====================

class NotificationService {
  private baseUrl = '/api/notifications';

  // ==================== 规则管理 ====================

  /**
   * 获取所有通知规则
   */
  async getRules(): Promise<NotificationRule[]> {
    const response = await api.get<{ success: boolean; data: any[] }>(`${this.baseUrl}/rules`);
    return (response.data || []).map((r: any) => ({
      ...r,
      notification_types: Array.isArray(r.notification_types)
        ? r.notification_types
        : (typeof r.notification_types === 'string' && r.notification_types.trim()
            ? safeParseArray(r.notification_types)
            : undefined),
    }));
  }

  /**
   * 获取指定通知规则
   */
  async getRule(ruleId: number): Promise<NotificationRule> {
    const response = await api.get<{ success: boolean; data: any }>(`${this.baseUrl}/rules/${ruleId}`);
    const r = response.data;
    return {
      ...r,
      notification_types: Array.isArray(r.notification_types)
        ? r.notification_types
        : (typeof r.notification_types === 'string' && r.notification_types.trim()
            ? safeParseArray(r.notification_types)
            : undefined),
    } as NotificationRule;
  }

  /**
   * 创建通知规则
   */
  async createRule(data: RuleFormData): Promise<NotificationRule> {
    const response = await api.post<{ success: boolean; data: any }>(`${this.baseUrl}/rules`, data);
    const r = response.data;
    return {
      ...r,
      notification_types: Array.isArray(r.notification_types)
        ? r.notification_types
        : (typeof r.notification_types === 'string' && r.notification_types.trim()
            ? safeParseArray(r.notification_types)
            : undefined),
    } as NotificationRule;
  }

  /**
   * 更新通知规则
   */
  async updateRule(ruleId: number, data: Partial<RuleFormData>): Promise<NotificationRule> {
    const response = await api.put<{ success: boolean; data: any }>(`${this.baseUrl}/rules/${ruleId}`, data);
    const r = response.data;
    return {
      ...r,
      notification_types: Array.isArray(r.notification_types)
        ? r.notification_types
        : (typeof r.notification_types === 'string' && r.notification_types.trim()
            ? safeParseArray(r.notification_types)
            : undefined),
    } as NotificationRule;
  }

  /**
   * 删除通知规则
   */
  async deleteRule(ruleId: number): Promise<void> {
    await api.delete(`${this.baseUrl}/rules/${ruleId}`);
  }

  /**
   * 切换规则状态
   */
  async toggleRule(ruleId: number, isActive: boolean): Promise<NotificationRule> {
    const response = await api.post<{ success: boolean; data: NotificationRule }>(
      `${this.baseUrl}/rules/${ruleId}/toggle`,
      { is_active: isActive }
    );
    return response.data;
  }

  // ==================== 历史查询 ====================

  /**
   * 获取通知历史
   */
  async getLogs(params?: LogQueryParams): Promise<NotificationLog[]> {
    const response = await api.get<{ success: boolean; data: NotificationLog[] }>(`${this.baseUrl}/logs`, { params });
    return response.data;
  }

  /**
   * 获取指定历史记录
   */
  async getLog(logId: number): Promise<NotificationLog> {
    const response = await api.get<{ success: boolean; data: NotificationLog }>(`${this.baseUrl}/logs/${logId}`);
    return response.data;
  }

  // ==================== 测试和统计 ====================

  /**
   * 测试通知发送
   */
  async testNotification(notificationType: NotificationType, channels: NotificationChannel[]): Promise<{ success: boolean; message: string }> {
    const response = await api.post<{ success: boolean; message: string }>(`${this.baseUrl}/test`, {
      notification_type: notificationType,
      channels
    });
    return response;
  }

  /**
   * 获取统计信息
   */
  async getStats(): Promise<NotificationStats> {
    const response = await api.get<{ success: boolean; data: NotificationStats }>(`${this.baseUrl}/stats`);
    return response.data;
  }

  /**
   * 获取通知类型列表
   */
  async getTypes(): Promise<NotificationTypeInfo[]> {
    const response = await api.get<{ success: boolean; data: NotificationTypeInfo[] }>(`${this.baseUrl}/types`);
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
   * 批量切换规则状态
   */
  async batchToggleRules(ruleIds: number[], isActive: boolean): Promise<void> {
    await Promise.all(ruleIds.map(id => this.toggleRule(id, isActive)));
  }
}

// 导出单例
export const notificationService = new NotificationService();
export default notificationService;

function safeParseArray(input: string): any[] | undefined {
  try {
    const v = JSON.parse(input);
    return Array.isArray(v) ? v : undefined;
  } catch {
    return undefined;
  }
}

