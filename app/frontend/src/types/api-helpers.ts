/**
 * API类型辅助工具
 * 提供类型安全的API调用封装
 */

import type { paths, components } from './api-schema';

// 导出所有组件定义
export type Schemas = components['schemas'];

// 提取请求参数类型
export type PathParams<T extends keyof paths> = paths[T] extends {
  parameters: { path: infer P };
}
  ? P
  : never;

// 提取查询参数类型
export type QueryParams<T extends keyof paths> = paths[T] extends {
  parameters: { query: infer Q };
}
  ? Q
  : never;

// 提取请求体类型
export type RequestBody<
  T extends keyof paths,
  M extends keyof paths[T]
> = paths[T][M] extends {
  requestBody: { content: { 'application/json': infer B } };
}
  ? B
  : never;

// 提取响应类型
export type ResponseBody<
  T extends keyof paths,
  M extends keyof paths[T],
  S extends number = 200
> = paths[T][M] extends {
  responses: {
    [K in S]: { content: { 'application/json': infer R } };
  };
}
  ? paths[T][M]['responses'][S]['content']['application/json']
  : never;

// 类型安全的API调用包装器
export interface TypedApiCall<Path extends keyof paths, Method extends keyof paths[Path]> {
  path: Path;
  method: Method;
  params?: PathParams<Path>;
  query?: QueryParams<Path>;
  body?: RequestBody<Path, Method>;
}

/**
 * 创建类型安全的API调用
 * 
 * @example
 * const call = createApiCall({
 *   path: '/api/rules/{id}',
 *   method: 'get',
 *   params: { id: 1 }
 * });
 */
export function createApiCall<Path extends keyof paths, Method extends keyof paths[Path]>(
  config: TypedApiCall<Path, Method>
): TypedApiCall<Path, Method> {
  return config;
}

/**
 * 构建完整URL（替换路径参数）
 */
export function buildUrl<Path extends keyof paths>(
  path: Path,
  params?: PathParams<Path>
): string {
  let url = path as string;
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, String(value));
    });
  }
  
  return url;
}

// 常用类型别名
export type ForwardRule = Schemas['ForwardRule'];
export type Chat = Schemas['Chat'];
export type LogEntry = Schemas['LogEntry'];
export type BotSettings = Schemas['BotSettings'];
export type SystemStatus = Schemas['SystemStatus'];

/**
 * API响应包装类型
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

/**
 * 分页响应类型
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

