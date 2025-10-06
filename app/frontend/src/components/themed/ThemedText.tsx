/**
 * 主题化文本组件示例
 * 展示如何创建完全响应主题的组件
 */

import React, { CSSProperties } from 'react';
import { useThemeContext } from '../../theme';

interface ThemedTextProps {
  variant?: 'primary' | 'secondary' | 'tertiary' | 'success' | 'warning' | 'error' | 'info';
  children: React.ReactNode;
  style?: CSSProperties;
  className?: string;
}

export const ThemedText: React.FC<ThemedTextProps> = ({ 
  variant = 'primary', 
  children,
  style,
  className 
}) => {
  const { colors } = useThemeContext();
  
  const colorMap = {
    primary: colors.textPrimary,
    secondary: colors.textSecondary,
    tertiary: colors.textTertiary,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
  };
  
  return (
    <span 
      className={className}
      style={{ 
        color: colorMap[variant],
        ...style 
      }}
    >
      {children}
    </span>
  );
};

