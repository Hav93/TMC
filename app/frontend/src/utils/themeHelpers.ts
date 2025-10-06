/**
 * 主题迁移辅助函数
 * 帮助快速创建符合新主题系统的样式
 */

import { CSSProperties } from 'react';
import { ThemeColors } from '../theme/colors';

/**
 * 常用的表格列渲染样式
 */
export const getTableColumnStyles = (colors: ThemeColors) => ({
  // 主要文本
  primary: {
    color: colors.textPrimary,
    fontWeight: 'bold' as const,
  },
  
  // 次要文本
  secondary: {
    color: colors.textSecondary,
    fontSize: 12,
  },
  
  // 代码/关键词样式
  code: {
    color: colors.textPrimary,
    fontFamily: 'monospace',
    backgroundColor: colors.bgElevated,
    padding: '2px 6px',
    borderRadius: 4,
    display: 'inline-block' as const,
  },
  
  // 成功状态
  success: {
    color: colors.success,
    fontWeight: 'bold' as const,
  },
  
  // 错误状态
  error: {
    color: colors.error,
    fontWeight: 'bold' as const,
  },
  
  // 警告状态
  warning: {
    color: colors.warning,
    fontWeight: 'bold' as const,
  },
  
  // 信息/链接
  info: {
    color: colors.info,
    fontWeight: 'bold' as const,
  },
  
  // 禁用状态
  disabled: {
    color: colors.textDisabled,
  },
});

/**
 * 卡片样式
 */
export const getCardStyles = (colors: ThemeColors) => ({
  container: {
    backgroundColor: colors.bgContainer,
    color: colors.textPrimary,
    borderRadius: 8,
    border: `1px solid ${colors.borderLight}`,
  },
  
  elevated: {
    backgroundColor: colors.bgElevated,
    color: colors.textPrimary,
    borderRadius: 8,
    border: `1px solid ${colors.borderLight}`,
  },
  
  header: {
    color: colors.textPrimary,
    fontSize: 16,
    fontWeight: 'bold' as const,
  },
  
  subtitle: {
    color: colors.textSecondary,
    fontSize: 14,
  },
});

/**
 * 空状态样式
 */
export const getEmptyStyles = (colors: ThemeColors): Record<string, CSSProperties> => ({
  container: {
    padding: '40px 20px',
    textAlign: 'center',
    color: colors.textSecondary,
    backgroundColor: colors.bgContainer,
    borderRadius: 12,
    border: `1px solid ${colors.borderLight}`,
    margin: '20px 0',
  },
  
  icon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.4,
  },
  
  title: {
    fontSize: 16,
    marginBottom: 8,
    color: colors.textPrimary,
  },
  
  description: {
    fontSize: 14,
    color: colors.textSecondary,
  },
});

/**
 * 日志样式
 */
export const getLogStyles = (colors: ThemeColors) => ({
  line: {
    padding: '6px 12px',
    borderRadius: 4,
    marginBottom: 2,
    wordBreak: 'break-all' as const,
    whiteSpace: 'pre-wrap' as const,
    transition: 'all 0.2s',
  },
  
  highlighted: {
    background: 'rgba(24, 144, 255, 0.08)',
    borderLeft: '2px solid #1890ff',
  },
  
  source: {
    marginRight: 8,
    color: colors.info,
    fontSize: 11,
    fontWeight: 'bold' as const,
  },
  
  icon: {
    marginRight: 6,
    fontSize: 14,
  },
});

/**
 * 按钮样式
 */
export const getButtonStyles = (colors: ThemeColors) => ({
  primary: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
    color: '#ffffff',
  },
  
  danger: {
    backgroundColor: colors.error,
    borderColor: colors.error,
    color: '#ffffff',
  },
  
  text: {
    color: colors.textPrimary,
  },
  
  link: {
    color: colors.link,
  },
});

/**
 * 快速获取文本颜色
 */
export const textColor = (colors: ThemeColors, variant: 'primary' | 'secondary' | 'tertiary' | 'disabled' = 'primary'): CSSProperties => {
  const colorMap = {
    primary: colors.textPrimary,
    secondary: colors.textSecondary,
    tertiary: colors.textTertiary,
    disabled: colors.textDisabled,
  };
  
  return { color: colorMap[variant] };
};

/**
 * 快速获取背景颜色
 */
export const bgColor = (colors: ThemeColors, variant: 'primary' | 'secondary' | 'container' | 'elevated' = 'container'): CSSProperties => {
  const colorMap = {
    primary: colors.bgPrimary,
    secondary: colors.bgSecondary,
    container: colors.bgContainer,
    elevated: colors.bgElevated,
  };
  
  return { backgroundColor: colorMap[variant] };
};

