/**
 * 类型安全的API客户端
 * 基于自动生成的OpenAPI类型
 */

import { api } from './api';
import type { paths } from '../types/api-schema';
import type { PathParams, QueryParams, RequestBody, ResponseBody } from '../types/api-helpers';

/**
 * 类型安全的GET请求
 */
export async function typedGet<
  Path extends keyof paths,
  Method extends 'get' = 'get'
>(
  path: Path,
  params?: {
    path?: PathParams<Path>;
    query?: QueryParams<Path>;
  }
): Promise<ResponseBody<Path, Method>> {
  let url = path as string;
  
  // 替换路径参数
  if (params?.path) {
    Object.entries(params.path).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, String(value));
    });
  }
  
  return api.get(url, params?.query);
}

/**
 * 类型安全的POST请求
 */
export async function typedPost<
  Path extends keyof paths,
  Method extends 'post' = 'post'
>(
  path: Path,
  data?: RequestBody<Path, Method>,
  params?: {
    path?: PathParams<Path>;
    query?: QueryParams<Path>;
  }
): Promise<ResponseBody<Path, Method>> {
  let url = path as string;
  
  // 替换路径参数
  if (params?.path) {
    Object.entries(params.path).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, String(value));
    });
  }
  
  return api.post(url, data);
}

/**
 * 类型安全的PUT请求
 */
export async function typedPut<
  Path extends keyof paths,
  Method extends 'put' = 'put'
>(
  path: Path,
  data?: RequestBody<Path, Method>,
  params?: {
    path?: PathParams<Path>;
  }
): Promise<ResponseBody<Path, Method>> {
  let url = path as string;
  
  if (params?.path) {
    Object.entries(params.path).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, String(value));
    });
  }
  
  return api.put(url, data);
}

/**
 * 类型安全的DELETE请求
 */
export async function typedDelete<
  Path extends keyof paths,
  Method extends 'delete' = 'delete'
>(
  path: Path,
  params?: {
    path?: PathParams<Path>;
  }
): Promise<ResponseBody<Path, Method>> {
  let url = path as string;
  
  if (params?.path) {
    Object.entries(params.path).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, String(value));
    });
  }
  
  return api.delete(url);
}

/**
 * 类型安全的API客户端
 */
export const typedApi = {
  get: typedGet,
  post: typedPost,
  put: typedPut,
  delete: typedDelete,
};

export default typedApi;

