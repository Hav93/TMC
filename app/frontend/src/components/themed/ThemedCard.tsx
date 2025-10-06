/**
 * 主题化卡片组件
 * 展示如何创建复杂的主题化组件
 */

import React, { CSSProperties } from 'react';
import { useThemeContext } from '../../theme';

interface ThemedCardProps {
  children: React.ReactNode;
  style?: CSSProperties;
  className?: string;
  elevated?: boolean;
}

export const ThemedCard: React.FC<ThemedCardProps> = ({ 
  children,
  style,
  className,
  elevated = false
}) => {
  const { colors } = useThemeContext();
  
  const cardStyle: CSSProperties = {
    backgroundColor: elevated ? colors.bgElevated : colors.bgContainer,
    color: colors.textPrimary,
    borderRadius: 8,
    padding: 16,
    border: `1px solid ${colors.borderLight}`,
    ...style
  };
  
  return (
    <div className={className} style={cardStyle}>
      {children}
    </div>
  );
};

