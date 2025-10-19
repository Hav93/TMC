/**
 * 统一API路由配置
 * 集中管理所有API端点，与后端路由保持同步
 * 
 * 对应后端: app/backend/main.py
 */

// API版本管理
export const API_VERSION = {
  V1: 'v1',
  CURRENT: 'v1', // 当前使用的版本
} as const;

// API基础路径
export const API_BASE = '/api';

// 支持版本化的API基础路径
export function getVersionedApiBase(version: string = API_VERSION.CURRENT): string {
  return `${API_BASE}/${version}`;
}

/**
 * API路由配置对象
 * 结构与后端路由保持一致
 */
export const API_ROUTES = {
  // ==================== 系统管理 (System) ====================
  // 后端: app/backend/api/routes/system.py
  system: {
    base: `${API_BASE}/system`,
    status: `${API_BASE}/system/status`,
    enhancedStatus: `${API_BASE}/system/enhanced-status`,
    containerLogs: `${API_BASE}/system/container-logs/stream`,
    logs: `${API_BASE}/system/logs`,
    stats: `${API_BASE}/stats`,
    telegram: {
      status: `${API_BASE}/telegram/status`,
      restart: `${API_BASE}/telegram/restart`,
      testCredentials: `${API_BASE}/telegram/test-credentials`,
      login: `${API_BASE}/telegram/login`,
      submitPassword: `${API_BASE}/telegram/submit-password`,
    },
    config: {
      current: `${API_BASE}/config/current`,
      forceReload: `${API_BASE}/config/force-reload`,
      syncStatus: `${API_BASE}/config/sync-status`,
    },
  },

  // ==================== 转发规则 (Rules) ====================
  // 后端: app/backend/api/routes/rules.py
  rules: {
    base: `${API_BASE}/rules`,
    list: `${API_BASE}/rules`,
    get: (id: number) => `${API_BASE}/rules/${id}`,
    create: `${API_BASE}/rules`,
    update: (id: number) => `${API_BASE}/rules/${id}`,
    delete: (id: number) => `${API_BASE}/rules/${id}`,
    toggle: (id: number) => `${API_BASE}/rules/${id}/toggle`,
    
    // 关键词管理
    keywords: {
      list: (ruleId: number) => `${API_BASE}/rules/${ruleId}/keywords`,
      create: (ruleId: number) => `${API_BASE}/rules/${ruleId}/keywords`,
      update: (keywordId: number) => `${API_BASE}/rules/keywords/${keywordId}`,
      delete: (keywordId: number) => `${API_BASE}/rules/keywords/${keywordId}`,
    },
    
    // 替换规则
    replacements: {
      list: (ruleId: number) => `${API_BASE}/rules/${ruleId}/replacements`,
      create: (ruleId: number) => `${API_BASE}/rules/${ruleId}/replacements`,
      update: (replacementId: number) => `${API_BASE}/rules/replacements/${replacementId}`,
      delete: (replacementId: number) => `${API_BASE}/rules/replacements/${replacementId}`,
    },
  },

  // ==================== 日志管理 (Logs) ====================
  // 后端: app/backend/api/routes/logs.py
  logs: {
    base: `${API_BASE}/logs`,
    list: `${API_BASE}/logs`,
    export: `${API_BASE}/logs/export`,
    clear: `${API_BASE}/logs/clear`,
    stats: `${API_BASE}/logs/stats`,
    messageTypeStats: `${API_BASE}/logs/message-type-stats`,
    ruleStats: `${API_BASE}/logs/rule-stats`,
  },

  // ==================== 聊天管理 (Chats) ====================
  // 后端: app/backend/api/routes/chats.py
  chats: {
    base: `${API_BASE}/chats`,
    list: `${API_BASE}/chats`,
    refresh: `${API_BASE}/chats/refresh`,
    export: `${API_BASE}/chats/export`,
    import: `${API_BASE}/chats/import`,
  },

  // ==================== 客户端管理 (Clients) ====================
  // 后端: app/backend/api/routes/clients.py
  clients: {
    base: `${API_BASE}/clients`,
    list: `${API_BASE}/clients`,
    create: `${API_BASE}/clients`,
    get: (clientId: string) => `${API_BASE}/clients/${clientId}`,
    delete: (clientId: string) => `${API_BASE}/clients/${clientId}`,
    status: (clientId: string) => `${API_BASE}/clients/${clientId}/status`,
    
    // 登录流程
    login: {
      sendCode: (clientId: string) => `${API_BASE}/clients/${clientId}/send-code`,
      verifyCode: (clientId: string) => `${API_BASE}/clients/${clientId}/verify-code`,
      verifyPassword: (clientId: string) => `${API_BASE}/clients/${clientId}/verify-password`,
    },
    
    logout: (clientId: string) => `${API_BASE}/clients/${clientId}/logout`,
  },

  // ==================== 系统设置 (Settings) ====================
  // 后端: app/backend/api/routes/settings.py
  settings: {
    base: `${API_BASE}/settings`,
    get: `${API_BASE}/settings`,
    save: `${API_BASE}/settings`,
    testProxy: `${API_BASE}/settings/test-proxy`,
    telegram: {
      login: `${API_BASE}/telegram/login`,
      logout: `${API_BASE}/telegram/logout`,
      status: `${API_BASE}/telegram/status`,
      testCredentials: `${API_BASE}/telegram/test-credentials`,
      restartClient: `${API_BASE}/telegram/restart-client`,
      restart: `${API_BASE}/telegram/restart`,
    },
    config: {
      forceReload: `${API_BASE}/config/force-reload`,
      syncStatus: `${API_BASE}/config/sync-status`,
    },
    logs: {
      testCleanup: `${API_BASE}/test-log-cleanup`,
    },
  },

  // ==================== 仪表板 (Dashboard) ====================
  // 后端: app/backend/api/routes/dashboard.py
  dashboard: {
    base: `${API_BASE}/dashboard`,
    stats: `${API_BASE}/dashboard/stats`,
    recentLogs: `${API_BASE}/dashboard/recent-logs`,
    messageStats: `${API_BASE}/dashboard/message-stats`,
  },

  // ==================== 资源监控 (Resources) ====================
  // 后端: app/backend/api/routes/resource_monitor.py
  resources: {
    base: `${API_BASE}/resources`,
    rules: {
      list: `${API_BASE}/resources/rules`,
      create: `${API_BASE}/resources/rules`,
      detail: (id: number) => `${API_BASE}/resources/rules/${id}`,
      update: (id: number) => `${API_BASE}/resources/rules/${id}`,
      delete: (id: number) => `${API_BASE}/resources/rules/${id}`,
    },
    records: {
      list: `${API_BASE}/resources/records`,
      detail: (id: number) => `${API_BASE}/resources/records/${id}`,
    },
    stats: `${API_BASE}/resources/stats`,
  },

  // ==================== 性能监控 (Performance) ====================
  // 后端: app/backend/api/routes/performance.py
  performance: {
    base: `${API_BASE}/performance`,
    stats: `${API_BASE}/performance/stats`,
    cache: {
      stats: `${API_BASE}/performance/cache/stats`,
      clear: `${API_BASE}/performance/cache/clear`,
    },
    retryQueue: {
      stats: `${API_BASE}/performance/retry-queue/stats`,
    },
    batchWriter: {
      stats: `${API_BASE}/performance/batch-writer/stats`,
      flush: `${API_BASE}/performance/batch-writer/flush`,
    },
    filterEngine: {
      stats: `${API_BASE}/performance/filter-engine/stats`,
      clearCache: `${API_BASE}/performance/filter-engine/clear-cache`,
    },
  },

  // ==================== 推送通知 (Notifications) ====================
  // 后端: app/backend/api/routes/notifications.py
  notifications: {
    base: `${API_BASE}/notifications`,
    rules: {
      list: `${API_BASE}/notifications/rules`,
      create: `${API_BASE}/notifications/rules`,
      detail: (id: number) => `${API_BASE}/notifications/rules/${id}`,
      update: (id: number) => `${API_BASE}/notifications/rules/${id}`,
      delete: (id: number) => `${API_BASE}/notifications/rules/${id}`,
      toggle: (id: number) => `${API_BASE}/notifications/rules/${id}/toggle`,
    },
    logs: {
      list: `${API_BASE}/notifications/logs`,
      detail: (id: number) => `${API_BASE}/notifications/logs/${id}`,
    },
    test: `${API_BASE}/notifications/test`,
    stats: `${API_BASE}/notifications/stats`,
    types: `${API_BASE}/notifications/types`,
  },

  // ==================== 健康检查 ====================
  health: '/health',
} as const;

/**
 * API方法类型定义
 */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/**
 * API端点元数据
 * 用于生成类型安全的API调用
 */
export interface ApiEndpoint {
  method: HttpMethod;
  path: string;
  description?: string;
}

/**
 * API端点映射表（用于文档生成和类型检查）
 */
export const API_ENDPOINTS: Record<string, Record<string, ApiEndpoint>> = {
  system: {
    status: { method: 'GET', path: API_ROUTES.system.status, description: '获取系统状态' },
    enhancedStatus: { method: 'GET', path: API_ROUTES.system.enhancedStatus, description: '获取增强模式状态' },
  },
  
  rules: {
    list: { method: 'GET', path: API_ROUTES.rules.list, description: '获取规则列表' },
    create: { method: 'POST', path: API_ROUTES.rules.create, description: '创建规则' },
    // ... 其他端点
  },

  settings: {
    get: { method: 'GET', path: API_ROUTES.settings.get, description: '获取系统配置' },
    save: { method: 'POST', path: API_ROUTES.settings.save, description: '保存系统配置' },
  },
  
  // ... 其他模块
};

/**
 * 构建完整的API URL
 * @param path API路径
 * @returns 完整URL
 */
export function buildApiUrl(path: string): string {
  const meta: any = (import.meta as any) || {};
  const base = meta?.env?.VITE_API_URL || (meta?.env?.PROD ? '' : 'http://localhost:9393');
  return `${base}${path}`;
}

/**
 * 验证API路径是否有效
 * @param path API路径
 * @returns 是否有效
 */
export function isValidApiPath(path: string): boolean {
  // 递归检查API_ROUTES中是否存在该路径
  const checkPath = (obj: any): boolean => {
    for (const key in obj) {
      const value = obj[key];
      if (typeof value === 'string' && value === path) {
        return true;
      }
      if (typeof value === 'object' && checkPath(value)) {
        return true;
      }
    }
    return false;
  };
  
  return checkPath(API_ROUTES);
}

export default API_ROUTES;

