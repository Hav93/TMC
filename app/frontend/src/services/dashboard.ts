import { api } from './api';

export interface DashboardStats {
  total_rules: number;
  active_rules: number;
  today_messages: number;
  success_rate: number;
  success_messages: number;
}

export interface RecentRule {
  id: number;
  name: string;
  source_chat_name?: string;
  source_chat_id: string;
  target_chat_name?: string;
  target_chat_id: string;
  is_active: boolean;
  created_at: string;
}

export interface RecentLog {
  id: number;
  rule_id?: number;
  source_chat_name?: string;
  source_chat_id: string;
  target_chat_name?: string;
  target_chat_id: string;
  status: 'success' | 'failed' | 'pending' | 'processing' | 'skipped';
  processed_text?: string;
  original_text?: string;
  created_at: string;
}

export interface SystemStatus {
  bot_running: boolean;
  proxy_enabled: boolean;
  proxy_type?: string;
}

export interface TelegramStatus {
  logged_in: boolean;
  user?: {
    first_name: string;
    last_name?: string;
    username?: string;
    phone?: string;
  };
  error?: string;
}

// 新增：仪表盘总览数据类型
export interface DashboardOverview {
  system_overview: {
    total_rules: number;
    active_rules: number;
    today_downloads: number;
    total_storage_gb: number;
    system_status: 'normal' | 'warning' | 'busy';
  };
  forward_module: {
    today_count: number;
    active_rules: number;
    total_rules: number;
    success_rate: number;
    processing_count: number;
    trend: Array<{ date: string; count: number }>;
  };
  media_module: {
    today_count: number;
    active_rules: number;
    total_rules: number;
    success_rate: number;
    downloading_count: number;
    storage_gb: number;
    trend: Array<{ date: string; count: number }>;
  };
  file_type_distribution: {
    [key: string]: {
      count: number;
      size_gb: number;
    };
  };
  storage_distribution: {
    local: {
      organized: {
        count: number;
        size_gb: number;
      };
      temp: {
        count: number;
        size_gb: number;
      };
      total_count: number;
      total_size_gb: number;
    };
    cloud: {
      uploaded: {
        count: number;
        size_gb: number;
      };
      pan115_space: {
        total_gb: number;
        used_gb: number;
        available_gb: number;
        usage_percentage: number;
      };
    };
    total_gb: number;
    cloud_percentage: number;
  };
  other_stats: {
    starred_count: number;
    total_files: number;
  };
}

// 新增：智能洞察数据类型
export interface DashboardInsights {
  peak_hour: string | null;
  peak_count: number;
  most_active_rule: string | null;
  most_active_count: number;
  storage_warning: {
    should_warn: boolean;
    days_until_80_percent: number;
    current_usage_gb: number;
    total_capacity_gb: number;
    usage_percentage: number;
  };
}

export const dashboardApi = {
  // 获取统计数据（原有）
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/api/stats');
    return response;
  },

  // 新增：获取仪表盘总览数据
  getOverview: async (): Promise<DashboardOverview> => {
    const response = await api.get<{ success: boolean; data: DashboardOverview }>('/api/dashboard/overview');
    return response.data;
  },

  // 新增：获取智能洞察
  getInsights: async (): Promise<DashboardInsights> => {
    const response = await api.get<{ success: boolean; insights: DashboardInsights }>('/api/dashboard/insights');
    return response.insights;
  },

  // 获取Telegram状态
  getTelegramStatus: async (): Promise<TelegramStatus> => {
    const response = await api.get<TelegramStatus>('/api/telegram/status');
    return response;
  },

  // 获取最近规则 (使用现有规则API的前几条)
  getRecentRules: async (_limit = 5): Promise<RecentRule[]> => {
    try {
      // 注意：这里可能需要后端恢复 GET /rules 接口
      console.warn('获取最近规则: 后端GET /rules接口被注释，返回空数据');
      return [];
    } catch (error) {
      console.error('获取最近规则失败:', error);
      return [];
    }
  },

  // 获取最近日志 (使用现有日志API的前几条)
  getRecentLogs: async (_limit = 10): Promise<RecentLog[]> => {
    try {
      // 注意：这里可能需要后端恢复 GET /logs 接口或者添加 GET /api/logs
      console.warn('获取最近日志: 后端GET /logs接口被注释，返回空数据');
      return [];
    } catch (error) {
      console.error('获取最近日志失败:', error);
      return [];
    }
  },

  // 刷新统计数据
  refreshStats: async (): Promise<DashboardStats> => {
    return dashboardApi.getStats();
  }
};
