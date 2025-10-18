/**
 * 115网盘离线下载 API 服务
 */

import { apiClient } from './api';
import type {
  AddOfflineTaskRequest,
  AddOfflineTaskResponse,
  GetOfflineTasksResponse,
  DeleteOfflineTasksRequest,
  ClearOfflineTasksRequest,
  OfflineOperationResponse,
} from '../types/offline';

const API_BASE_URL = '/api/pan115';

/**
 * 添加离线下载任务
 */
export async function addOfflineTask(
  params: AddOfflineTaskRequest
): Promise<AddOfflineTaskResponse> {
  const response = await apiClient.post(`${API_BASE_URL}/offline/add`, {
    url: params.url,
    target_dir_id: params.target_dir_id || '0',
  });
  return response.data;
}

/**
 * 获取离线任务列表
 */
export async function getOfflineTasks(
  page: number = 1
): Promise<GetOfflineTasksResponse> {
  const response = await apiClient.get(`${API_BASE_URL}/offline/tasks`, {
    params: { page },
  });
  return response.data;
}

/**
 * 删除离线任务
 */
export async function deleteOfflineTasks(
  params: DeleteOfflineTasksRequest
): Promise<OfflineOperationResponse> {
  const response = await apiClient.delete(`${API_BASE_URL}/offline/tasks`, {
    data: { task_ids: params.task_ids },
  });
  return response.data;
}

/**
 * 清空离线任务
 */
export async function clearOfflineTasks(
  params: ClearOfflineTasksRequest
): Promise<OfflineOperationResponse> {
  const response = await apiClient.post(`${API_BASE_URL}/offline/clear`, {
    flag: params.flag,
  });
  return response.data;
}

