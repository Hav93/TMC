/**
 * 样式工具函数
 * 提供类型安全的样式对象创建
 */

import { CSSProperties } from 'react';
import { ThemeColors } from './colors';

/**
 * 创建主题相关的样式对象
 * 这样可以确保所有颜色都从主题系统获取
 */
export const createStyles = <T extends Record<string, CSSProperties>>(
  stylesFn: (colors: ThemeColors) => T
) => stylesFn;

/**
 * 文本颜色样式
 */
export const textStyles = (colors: ThemeColors) => ({
  primary: {
    color: colors.textPrimary,
  },
  secondary: {
    color: colors.textSecondary,
  },
  tertiary: {
    color: colors.textTertiary,
  },
  disabled: {
    color: colors.textDisabled,
  },
  success: {
    color: colors.success,
  },
  warning: {
    color: colors.warning,
  },
  error: {
    color: colors.error,
  },
  info: {
    color: colors.info,
  },
});

/**
 * 背景颜色样式
 */
export const bgStyles = (colors: ThemeColors) => ({
  primary: {
    backgroundColor: colors.bgPrimary,
  },
  secondary: {
    backgroundColor: colors.bgSecondary,
  },
  container: {
    backgroundColor: colors.bgContainer,
  },
  elevated: {
    backgroundColor: colors.bgElevated,
  },
});

/**
 * 边框样式
 */
export const borderStyles = (colors: ThemeColors) => ({
  base: {
    borderColor: colors.borderBase,
  },
  light: {
    borderColor: colors.borderLight,
  },
  strong: {
    borderColor: colors.borderStrong,
  },
});

/**
 * 组合多个样式
 */
export const combineStyles = (...styles: CSSProperties[]): CSSProperties => {
  return Object.assign({}, ...styles);
};

