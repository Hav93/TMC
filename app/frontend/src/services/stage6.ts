/**
 * 阶段6功能API服务
 * 包括：广告过滤、秒传检测、智能重命名、STRM生成
 */
import api from './api';

// ==================== 类型定义 ====================

// 广告过滤
export interface AdFilterRule {
  pattern: string;
  min_size?: number;
  max_size?: number;
  action: 'skip' | 'delete' | 'quarantine' | 'allow';
  description: string;
  priority: number;
}

export interface FileCheckResult {
  filename: string;
  is_ad: boolean;
  action: string;
  reason: string;
}

export interface BatchCheckResult {
  total: number;
  allowed: number;
  filtered: number;
  allowed_files: any[];
  filtered_files: any[];
}

export interface AdFilterStats {
  total_rules: number;
  whitelist_patterns: number;
  rules_by_priority: {
    high: number;
    medium: number;
    low: number;
  };
}

// 秒传检测
export interface SHA1Result {
  file_path: string;
  sha1: string;
}

export interface QuickUploadResult {
  file_path: string;
  file_size: number;
  sha1: string;
  is_quick: boolean;
  check_time: number;
  error?: string;
}

export interface QuickUploadStats {
  total_checks: number;
  quick_success: number;
  quick_failed: number;
  success_rate: string;
  total_time_saved: string;
  total_bandwidth_saved: string;
  avg_check_time: string;
}

// 智能重命名
export interface MediaMetadata {
  media_type: string;
  title: string;
  year?: number;
  season?: number;
  episode?: number;
  resolution?: string;
  codec?: string;
  audio?: string;
  source?: string;
  extension: string;
}

export interface RenameResult {
  original: string;
  renamed: string;
}

export interface BatchRenameResult {
  total: number;
  renamed: Record<string, string>;
}

export interface RenameTemplates {
  movie: string;
  tv: string;
  simple: string;
  detailed: string;
}

// STRM生成
export interface StrmConfig {
  media_url: string;
  output_dir: string;
  filename: string;
  title?: string;
  year?: number;
  plot?: string;
  genre?: string;
  rating?: number;
  include_nfo?: boolean;
  nfo_type?: 'movie' | 'tvshow';
}

export interface StrmResult {
  strm?: string;
  nfo?: string;
}

// ==================== API服务类 ====================

class Stage6Service {
  // ========== 广告过滤 ==========
  
  async checkFile(filename: string, file_size?: number): Promise<FileCheckResult> {
    const response = await api.post<{ success: boolean; data: FileCheckResult }>(
      '/api/ad-filter/check',
      { filename, file_size }
    );
    return response.data;
  }

  async batchCheckFiles(files: any[]): Promise<BatchCheckResult> {
    const response = await api.post<{ success: boolean; data: BatchCheckResult }>(
      '/api/ad-filter/batch-check',
      { files }
    );
    return response.data;
  }

  async getAdFilterRules(): Promise<AdFilterRule[]> {
    const response = await api.get<{ success: boolean; data: AdFilterRule[] }>(
      '/api/ad-filter/rules'
    );
    return response.data;
  }

  async addAdFilterRule(rule: Omit<AdFilterRule, 'priority'>): Promise<void> {
    await api.post('/api/ad-filter/rules', rule);
  }

  async getAdFilterWhitelist(): Promise<string[]> {
    const response = await api.get<{ success: boolean; data: string[] }>(
      '/api/ad-filter/whitelist'
    );
    return response.data;
  }

  async addAdFilterWhitelist(pattern: string): Promise<void> {
    await api.post(`/api/ad-filter/whitelist?pattern=${encodeURIComponent(pattern)}`);
  }

  async getAdFilterStats(): Promise<AdFilterStats> {
    const response = await api.get<{ success: boolean; data: AdFilterStats }>(
      '/api/ad-filter/stats'
    );
    return response.data;
  }

  // ========== 秒传检测 ==========

  async calculateSHA1(file_path: string): Promise<SHA1Result> {
    const response = await api.post<{ success: boolean; data: SHA1Result }>(
      '/api/quick-upload/sha1',
      { file_path }
    );
    return response.data;
  }

  async checkQuickUpload(file_path: string): Promise<QuickUploadResult> {
    const response = await api.post<{ success: boolean; data: QuickUploadResult }>(
      '/api/quick-upload/check',
      { file_path }
    );
    return response.data;
  }

  async getQuickUploadStats(): Promise<QuickUploadStats> {
    const response = await api.get<{ success: boolean; data: QuickUploadStats }>(
      '/api/quick-upload/stats'
    );
    return response.data;
  }

  // ========== 智能重命名 ==========

  async parseFilename(filename: string): Promise<MediaMetadata> {
    const response = await api.post<{ success: boolean; data: MediaMetadata }>(
      '/api/smart-rename/parse',
      { filename }
    );
    return response.data;
  }

  async renameFile(filename: string, template?: string): Promise<RenameResult> {
    const response = await api.post<{ success: boolean; data: RenameResult }>(
      '/api/smart-rename/rename',
      { filename, template }
    );
    return response.data;
  }

  async batchRenameFiles(filenames: string[], template?: string): Promise<BatchRenameResult> {
    const response = await api.post<{ success: boolean; data: BatchRenameResult }>(
      '/api/smart-rename/batch-rename',
      { filenames, template }
    );
    return response.data;
  }

  async getRenameTemplates(): Promise<RenameTemplates> {
    const response = await api.get<{ success: boolean; data: RenameTemplates }>(
      '/api/smart-rename/templates'
    );
    return response.data;
  }

  // ========== STRM生成 ==========

  async generateStrm(config: StrmConfig): Promise<StrmResult> {
    const response = await api.post<{ success: boolean; data: StrmResult }>(
      '/api/strm/generate',
      config
    );
    return response.data;
  }

  async generateStrmSimple(
    media_url: string,
    output_dir: string,
    filename: string
  ): Promise<StrmResult> {
    const params = new URLSearchParams({
      media_url,
      output_dir,
      filename,
    });
    const response = await api.post<{ success: boolean; data: StrmResult }>(
      `/api/strm/generate-simple?${params.toString()}`
    );
    return response.data;
  }
}

export const stage6Service = new Stage6Service();
export default stage6Service;

