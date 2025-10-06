/**
 * 主题化空状态组件
 * 用于表格和列表的空状态显示
 */

import React from 'react';
import { useThemeContext } from '../../theme';

interface ThemedEmptyProps {
  icon?: string;
  title?: string;
  description?: string;
}

export const ThemedEmpty: React.FC<ThemedEmptyProps> = ({ 
  icon = '📋',
  title = '暂无数据',
  description 
}) => {
  const { colors } = useThemeContext();
  
  return (
    <div style={{
      padding: '40px 20px',
      textAlign: 'center',
      color: colors.textSecondary,
      backgroundColor: colors.bgContainer,
      borderRadius: 12,
      border: `1px solid ${colors.borderLight}`,
      margin: '20px 0',
    }}>
      <div style={{
        fontSize: 48,
        marginBottom: 16,
        opacity: 0.4,
      }}>
        {icon}
      </div>
      <div style={{
        fontSize: 16,
        marginBottom: description ? 8 : 0,
        color: colors.textPrimary,
      }}>
        {title}
      </div>
      {description && (
        <div style={{
          fontSize: 14,
          color: colors.textSecondary,
        }}>
          {description}
        </div>
      )}
    </div>
  );
};

