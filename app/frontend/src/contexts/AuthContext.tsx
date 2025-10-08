import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, getCurrentUser, logout as logoutApi, initAuth, isAuthenticated as checkAuth } from '../services/auth';
import { setUnauthorizedCallback } from '../services/api';
import { message } from 'antd';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // 【优化】使用 useCallback 确保回调函数引用稳定
  const handleUnauthorized = useCallback(() => {
    console.log('🔐 检测到登录状态过期，清除用户状态并跳转到登录页');
    setUser(null);
    message.warning('登录已过期，请重新登录');
    navigate('/login', { replace: true });
  }, [navigate]);

  // 初始化：从localStorage恢复token并获取用户信息
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // 【优化】注册401未授权回调
        setUnauthorizedCallback(handleUnauthorized);
        
        // 初始化API认证token
        initAuth();
        
        // 检查是否有token
        if (checkAuth()) {
          // 获取用户信息
          const userData = await getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        console.error('初始化认证失败:', error);
        // 清除无效的token
        localStorage.removeItem('access_token');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, [handleUnauthorized]); // 【优化】正确的依赖项

  const login = (userData: User) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await logoutApi();
      setUser(null);
      message.success('已登出');
      // 【优化】登出后跳转到登录页
      navigate('/login', { replace: true });
    } catch (error) {
      console.error('登出失败:', error);
      // 即使API调用失败，也清除本地状态
      setUser(null);
      navigate('/login', { replace: true });
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error: any) {
      console.error('刷新用户信息失败:', error);
      
      // 【优化】如果是 401，拦截器已处理，不需要再次 setUser(null)
      if (error.response?.status !== 401) {
        setUser(null);
      }
      // 401 错误由拦截器统一处理（自动跳转登录页）
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

