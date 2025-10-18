/**
 * 115网盘离线下载任务类型定义
 */

/**
 * 离线任务状态枚举
 */
export enum OfflineTaskStatus {
  /** 等待中 */
  WAITING = -1,
  /** 下载中 */
  DOWNLOADING = 0,
  /** 已完成 */
  COMPLETED = 1,
  /** 失败 */
  FAILED = 2,
  /** 已删除 */
  DELETED = 4,
}

/**
 * 离线任务信息
 */
export interface OfflineTask {
  /** 任务ID */
  task_id: string;
  /** 任务名称 */
  name: string;
  /** 状态码 */
  status: OfflineTaskStatus;
  /** 状态文本 */
  status_text: string;
  /** 文件大小（字节） */
  size: number;
  /** 完成百分比 (0-100) */
  percentDone: number;
  /** 添加时间戳 */
  add_time: number;
  /** 完成后的文件ID */
  file_id: string;
}

/**
 * 添加离线任务请求
 */
export interface AddOfflineTaskRequest {
  /** 下载链接（HTTP/磁力/BT） */
  url: string;
  /** 目标目录ID */
  target_dir_id?: string;
}

/**
 * 添加离线任务响应
 */
export interface AddOfflineTaskResponse {
  success: boolean;
  task_id?: string;
  message: string;
}

/**
 * 获取离线任务列表响应
 */
export interface GetOfflineTasksResponse {
  success: boolean;
  tasks: OfflineTask[];
  count: number;
  message: string;
}

/**
 * 删除离线任务请求
 */
export interface DeleteOfflineTasksRequest {
  task_ids: string[];
}

/**
 * 清空离线任务请求
 */
export interface ClearOfflineTasksRequest {
  /** 清空标志：0=所有，1=已完成，2=失败 */
  flag: 0 | 1 | 2;
}

/**
 * 通用操作响应
 */
export interface OfflineOperationResponse {
  success: boolean;
  message: string;
}

/**
 * 离线任务统计信息
 */
export interface OfflineTaskStats {
  total: number;
  waiting: number;
  downloading: number;
  completed: number;
  failed: number;
}

