/**
 * API版本管理
 * 支持多版本API并存和平滑迁移
 */

import { API_BASE, API_VERSION } from './api-config';

/**
 * API版本类型
 */
export type ApiVersion = 'v1' | 'v2';

/**
 * 版本化API配置
 */
interface VersionedApi {
  version: ApiVersion;
  base: string;
  deprecated?: boolean;
  sunset?: Date; // 停用日期
  description?: string;
}

/**
 * 所有API版本配置
 */
export const API_VERSIONS: Record<ApiVersion, VersionedApi> = {
  v1: {
    version: 'v1',
    base: API_BASE,
    description: 'TMC API v1.1 - 当前稳定版本',
  },
  v2: {
    version: 'v2',
    base: `${API_BASE}/v2`,
    deprecated: true,
    sunset: new Date('2026-01-01'),
    description: 'TMC API v2.0 - 预览版（未实现）',
  },
};

/**
 * 获取指定版本的API基础路径
 */
export function getApiBase(version: ApiVersion = API_VERSION.CURRENT as ApiVersion): string {
  const versionConfig = API_VERSIONS[version];
  
  if (!versionConfig) {
    console.warn(`API版本 ${version} 不存在，使用默认版本 ${API_VERSION.CURRENT}`);
    return API_VERSIONS[API_VERSION.CURRENT as ApiVersion].base;
  }
  
  if (versionConfig.deprecated) {
    console.warn(`⚠️ API版本 ${version} 已弃用，建议迁移到最新版本`);
    if (versionConfig.sunset) {
      console.warn(`   停用日期: ${versionConfig.sunset.toLocaleDateString('zh-CN')}`);
    }
  }
  
  return versionConfig.base;
}

/**
 * 构建版本化的API路径
 */
export function buildVersionedPath(
  path: string,
  version: ApiVersion = API_VERSION.CURRENT as ApiVersion
): string {
  const base = getApiBase(version);
  // 移除path中可能已经包含的/api前缀
  const cleanPath = path.replace(/^\/api/, '');
  return `${base}${cleanPath}`;
}

/**
 * API版本信息
 */
export interface ApiVersionInfo {
  current: ApiVersion;
  available: ApiVersion[];
  deprecated: ApiVersion[];
  sunset: Record<ApiVersion, Date | null>;
}

/**
 * 获取API版本信息
 */
export function getApiVersionInfo(): ApiVersionInfo {
  const available = Object.keys(API_VERSIONS) as ApiVersion[];
  const deprecated = available.filter(v => API_VERSIONS[v].deprecated);
  const sunset = available.reduce((acc, v) => {
    acc[v] = API_VERSIONS[v].sunset || null;
    return acc;
  }, {} as Record<ApiVersion, Date | null>);

  return {
    current: API_VERSION.CURRENT as ApiVersion,
    available,
    deprecated,
    sunset,
  };
}

/**
 * 检查版本兼容性
 */
export function checkVersionCompatibility(
  version: ApiVersion,
  requiredVersion: ApiVersion
): boolean {
  const versionOrder: ApiVersion[] = ['v1', 'v2'];
  const currentIndex = versionOrder.indexOf(version);
  const requiredIndex = versionOrder.indexOf(requiredVersion);
  
  return currentIndex >= requiredIndex;
}

/**
 * API版本迁移助手
 */
export class ApiVersionMigration {
  private readonly fromVersion: ApiVersion;
  private readonly toVersion: ApiVersion;
  
  constructor(fromVersion: ApiVersion, toVersion: ApiVersion) {
    this.fromVersion = fromVersion;
    this.toVersion = toVersion;
  }
  
  /**
   * 获取迁移指南
   */
  getMigrationGuide(): string[] {
    const guides: Record<string, string[]> = {
      'v1-to-v2': [
        '1. 更新API端点路径，添加/v2前缀',
        '2. 检查请求/响应数据结构变化',
        '3. 更新错误处理逻辑',
        '4. 测试所有API调用',
        '5. 逐步迁移，保持向后兼容',
      ],
    };
    
    const key = `${this.fromVersion}-to-${this.toVersion}`;
    return guides[key] || ['暂无迁移指南'];
  }
  
  /**
   * 检查是否需要迁移
   */
  needsMigration(): boolean {
    const fromConfig = API_VERSIONS[this.fromVersion];
    return fromConfig?.deprecated || false;
  }
}

export default {
  getApiBase,
  buildVersionedPath,
  getApiVersionInfo,
  checkVersionCompatibility,
  ApiVersionMigration,
};

