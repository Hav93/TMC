/**
 * 性能监控API服务
 * 
 * 功能：
 * - 获取性能统计信息
 * - 管理缓存
 * - 管理重试队列
 * - 管理批量写入器
 * - 管理过滤引擎
 */

import api from './api';

// ==================== 类型定义 ====================

/**
 * 消息缓存统计
 */
export interface MessageCacheStats {
  total_size: number;
  max_size: number;
  usage_percent: number;
  hits: number;
  misses: number;
  hit_rate: string;
  evictions: number;
  expirations: number;
}

/**
 * 过滤引擎统计
 */
export interface FilterEngineStats {
  total_matches: number;
  regex_cache_size: number;
  max_regex_cache: number;
  cache_hit_rate: string;
  regex_compilations: number;
}

/**
 * 重试队列统计
 */
export interface RetryQueueStats {
  current_queue_size: number;
  total_added: number;
  total_success: number;
  total_failed: number;
  last_persistence?: string;
  persistence_errors: number;
  success_rate: string;
}

/**
 * 批量写入器统计
 */
export interface BatchWriterStats {
  current_queue_size: number;
  total_operations: number;
  total_inserts: number;
  total_updates: number;
  total_flushes: number;
  total_errors: number;
}

/**
 * 消息分发器统计
 */
export interface MessageDispatcherStats {
  total_messages: number;
  avg_processing_time: number;
  processors: Record<string, {
    processed: number;
    success: number;
    failed: number;
    avg_time: number;
  }>;
}

/**
 * 综合性能统计
 */
export interface PerformanceStats {
  message_cache: MessageCacheStats;
  filter_engine: FilterEngineStats;
  retry_queue: RetryQueueStats;
  batch_writer: BatchWriterStats;
  message_dispatcher: MessageDispatcherStats;
}

// ==================== API方法 ====================

/**
 * 性能监控API服务类
 */
class PerformanceService {
  private baseUrl = '/api/performance';

  // ==================== 综合统计 ====================

  /**
   * 获取所有性能统计
   */
  async getStats(): Promise<PerformanceStats> {
    const response = await api.get<{ success: boolean; data: PerformanceStats }>(`${this.baseUrl}/stats`);
    return response.data;
  }

  // ==================== 缓存管理 ====================

  /**
   * 获取缓存统计
   */
  async getCacheStats(): Promise<MessageCacheStats> {
    const response = await api.get<{ success: boolean; data: MessageCacheStats }>(`${this.baseUrl}/cache/stats`);
    return response.data;
  }

  /**
   * 清空缓存
   */
  async clearCache(): Promise<void> {
    await api.post(`${this.baseUrl}/cache/clear`);
  }

  // ==================== 重试队列管理 ====================

  /**
   * 获取重试队列统计
   */
  async getRetryQueueStats(): Promise<RetryQueueStats> {
    const response = await api.get<{ success: boolean; data: RetryQueueStats }>(`${this.baseUrl}/retry-queue/stats`);
    return response.data;
  }

  // ==================== 批量写入器管理 ====================

  /**
   * 获取批量写入器统计
   */
  async getBatchWriterStats(): Promise<BatchWriterStats> {
    const response = await api.get<{ success: boolean; data: BatchWriterStats }>(`${this.baseUrl}/batch-writer/stats`);
    return response.data;
  }

  /**
   * 手动刷新批量写入器
   */
  async flushBatchWriter(): Promise<void> {
    await api.post(`${this.baseUrl}/batch-writer/flush`);
  }

  // ==================== 过滤引擎管理 ====================

  /**
   * 获取过滤引擎统计
   */
  async getFilterEngineStats(): Promise<FilterEngineStats> {
    const response = await api.get<{ success: boolean; data: FilterEngineStats }>(`${this.baseUrl}/filter-engine/stats`);
    return response.data;
  }

  /**
   * 清空过滤引擎缓存
   */
  async clearFilterEngineCache(): Promise<void> {
    await api.post(`${this.baseUrl}/filter-engine/clear-cache`);
  }
}

// 导出单例
export const performanceService = new PerformanceService();

// 导出便捷方法
export const {
  getStats,
  getCacheStats,
  clearCache,
  getRetryQueueStats,
  getBatchWriterStats,
  flushBatchWriter,
  getFilterEngineStats,
  clearFilterEngineCache
} = performanceService;

export default performanceService;

