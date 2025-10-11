/**
 * 主题颜色配置
 * 集中管理所有颜色，禁止在组件中使用硬编码颜色
 */

export interface ThemeColors {
  // 主色
  primary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  
  // 文本颜色
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textDisabled: string;
  
  // 背景颜色
  bgPrimary: string;
  bgSecondary: string;
  bgContainer: string;
  bgElevated: string;
  bgLayout: string;
  cardBg: string;  // 卡片背景色
  
  // 边框颜色
  borderBase: string;
  borderLight: string;
  borderStrong: string;
  border: string;  // 通用边框色
  
  // 功能颜色
  link: string;
  linkHover: string;
  
  // 状态颜色
  statusActive: string;
  statusInactive: string;
  statusPending: string;
}

export const lightTheme: ThemeColors = {
  // 主色
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
  info: '#1890ff',
  
  // 文本颜色
  textPrimary: '#141414',
  textSecondary: '#8c8c8c',
  textTertiary: '#bfbfbf',
  textDisabled: '#d9d9d9',
  
  // 背景颜色
  bgPrimary: '#ffffff',
  bgSecondary: '#fafafa',
  bgContainer: '#ffffff',
  bgElevated: '#ffffff',
  bgLayout: '#f5f5f5',
  cardBg: '#ffffff',
  
  // 边框颜色
  borderBase: '#d9d9d9',
  borderLight: '#f0f0f0',
  borderStrong: '#8c8c8c',
  border: '#d9d9d9',
  
  // 功能颜色
  link: '#1890ff',
  linkHover: '#40a9ff',
  
  // 状态颜色
  statusActive: '#52c41a',
  statusInactive: '#d9d9d9',
  statusPending: '#faad14',
};

export const darkTheme: ThemeColors = {
  // 主色
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
  info: '#1890ff',
  
  // 文本颜色
  textPrimary: '#e8eaed',
  textSecondary: '#c8cad0',
  textTertiary: '#9aa0a6',
  textDisabled: '#5f6368',
  
  // 背景颜色
  bgPrimary: '#0a0e27',
  bgSecondary: '#141824',
  bgContainer: '#1a1d2e',
  bgElevated: '#1a1d2e',
  bgLayout: '#0a0e27',
  cardBg: '#1a1d2e',
  
  // 边框颜色
  borderBase: '#2a2f45',
  borderLight: '#1f2437',
  borderStrong: '#3d4463',
  border: '#2a2f45',
  
  // 功能颜色
  link: '#1890ff',
  linkHover: '#40a9ff',
  
  // 状态颜色
  statusActive: '#52c41a',
  statusInactive: '#5f6368',
  statusPending: '#faad14',
};

export type ThemeType = 'light' | 'dark';

export const themes: Record<ThemeType, ThemeColors> = {
  light: lightTheme,
  dark: darkTheme,
};

