/**
 * 认证相关API服务
 */
import api from './api';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}

export interface User {
  id: number;
  username: string;
  email: string | null;
  full_name: string | null;
  avatar: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UpdateProfileRequest {
  email?: string;
  full_name?: string;
  avatar?: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * 用户登录
 */
export const login = async (data: LoginRequest): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>('/api/auth/login', data);
  // 保存token到localStorage
  if (response.access_token) {
    localStorage.setItem('access_token', response.access_token);
    // 配置API请求头
    api.setAuthToken(response.access_token);
  }
  return response;
};

/**
 * 用户注册
 */
export const register = async (data: RegisterRequest): Promise<User> => {
  return api.post<User>('/api/auth/register', data);
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  return api.get<User>('/api/auth/me');
};

/**
 * 用户登出
 */
export const logout = async (): Promise<void> => {
  try {
    await api.post('/api/auth/logout');
  } finally {
    // 清除token
    localStorage.removeItem('access_token');
    api.setAuthToken(null);
  }
};

/**
 * 检查是否已登录
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

/**
 * 获取存储的token
 */
export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * 初始化认证状态（从localStorage恢复token）
 */
export const initAuth = (): void => {
  const token = getToken();
  if (token) {
    api.setAuthToken(token);
  }
};

/**
 * 更新个人信息
 */
export const updateProfile = async (data: UpdateProfileRequest): Promise<User> => {
  return api.put<User>('/api/auth/profile', data);
};

/**
 * 修改密码
 */
export const changePassword = async (data: ChangePasswordRequest): Promise<{ message: string }> => {
  return api.post<{ message: string }>('/api/auth/change-password', data);
};

