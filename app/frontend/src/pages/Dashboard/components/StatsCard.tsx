import React from 'react';
import { Card, Statistic, Skeleton } from 'antd';
import { useThemeContext } from '../../../theme';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
  suffix?: string;
  prefix?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon,
  color,
  loading = false,
  suffix,
  prefix,
}) => {
  const { colors } = useThemeContext();
  
  if (loading) {
    return (
      <Card className="glass-card-3d" style={{ height: 120, backgroundColor: colors.bgContainer }}>
        <Skeleton active paragraph={{ rows: 1 }} />
      </Card>
    );
  }

  return (
    <Card
      className="glass-card-3d"
      style={{
        height: 120,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: colors.bgContainer,
        borderColor: colors.borderLight,
      }}
      bodyStyle={{
        padding: 20,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      {/* 背景图标 */}
      <div
        className="stats-card-background-icon"
        style={{ color: color }}
      >
        {icon}
      </div>


      {/* 统计内容 */}
      <div className="stats-card-content">
        <div style={{ color: colors.textSecondary, fontSize: 14, marginBottom: 8, fontWeight: 500 }}>
          {title}
        </div>
        <Statistic
          value={value}
          suffix={suffix}
          prefix={prefix}
          valueStyle={{
            color: color,
            fontSize: 28,
            fontWeight: 'bold',
          }}
        />
      </div>

      {/* 左侧图标 */}
      <div
        className="stats-card-left-icon"
        style={{ color: color }}
      >
        {icon}
      </div>
    </Card>
  );
};

export default StatsCard;
