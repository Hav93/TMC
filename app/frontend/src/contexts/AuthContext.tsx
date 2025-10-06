import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, getCurrentUser, logout as logoutApi, initAuth, isAuthenticated as checkAuth } from '../services/auth';
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

  // 初始化：从localStorage恢复token并获取用户信息
  useEffect(() => {
    const initializeAuth = async () => {
      try {
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
  }, []);

  const login = (userData: User) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await logoutApi();
      setUser(null);
      message.success('已登出');
    } catch (error) {
      console.error('登出失败:', error);
      // 即使API调用失败，也清除本地状态
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('刷新用户信息失败:', error);
      setUser(null);
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

