import { api } from './api';
import type { User, CreateUserRequest, UpdateUserRequest, UsersListResponse } from '../types/user';

export const usersApi = {
  /**
   * 获取用户列表
   */
  list: async (skip: number = 0, limit: number = 100): Promise<UsersListResponse> => {
    return api.get<UsersListResponse>(`/api/users?skip=${skip}&limit=${limit}`);
  },

  /**
   * 获取用户详情
   */
  get: async (userId: number): Promise<User> => {
    return api.get<User>(`/api/users/${userId}`);
  },

  /**
   * 创建新用户
   */
  create: async (data: CreateUserRequest): Promise<User> => {
    return api.post<User>('/api/users', data);
  },

  /**
   * 更新用户信息
   */
  update: async (userId: number, data: UpdateUserRequest): Promise<User> => {
    return api.put<User>(`/api/users/${userId}`, data);
  },

  /**
   * 删除用户
   */
  delete: async (userId: number): Promise<{ success: boolean; message: string }> => {
    return api.delete(`/api/users/${userId}`);
  },

  /**
   * 重置用户密码
   */
  resetPassword: async (userId: number, newPassword: string): Promise<{ success: boolean; message: string }> => {
    return api.post(`/api/users/${userId}/reset-password?new_password=${encodeURIComponent(newPassword)}`);
  },
};
