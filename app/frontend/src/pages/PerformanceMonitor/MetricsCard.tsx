import React from 'react';
import { Card, Statistic, Progress, Space, Typography, Tooltip } from 'antd';
import {
  QuestionCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface MetricsCardProps {
  title: string;
  value: number | string;
  suffix?: string;
  prefix?: React.ReactNode;
  precision?: number;
  valueStyle?: React.CSSProperties;
  tooltip?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  progress?: {
    percent: number;
    status?: 'success' | 'exception' | 'normal' | 'active';
  };
  extra?: React.ReactNode;
}

/**
 * 性能指标卡片组件
 * 
 * 功能：
 * - 显示单个性能指标
 * - 支持趋势显示
 * - 支持进度条
 * - 支持工具提示
 */
const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  suffix,
  prefix,
  precision = 0,
  valueStyle,
  tooltip,
  trend,
  progress,
  extra,
}) => {
  return (
    <Card size="small">
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* 标题和工具提示 */}
        <Space>
          <Text type="secondary">{title}</Text>
          {tooltip && (
            <Tooltip title={tooltip}>
              <QuestionCircleOutlined style={{ color: '#8c8c8c' }} />
            </Tooltip>
          )}
        </Space>

        {/* 主要数值 */}
        <Statistic
          value={value}
          suffix={suffix}
          prefix={prefix}
          precision={precision}
          valueStyle={valueStyle}
        />

        {/* 趋势指示 */}
        {trend && (
          <Space size="small">
            {trend.isPositive ? (
              <ArrowUpOutlined style={{ color: '#52c41a' }} />
            ) : (
              <ArrowDownOutlined style={{ color: '#f5222d' }} />
            )}
            <Text
              type={trend.isPositive ? 'success' : 'danger'}
              style={{ fontSize: 12 }}
            >
              {Math.abs(trend.value)}%
            </Text>
          </Space>
        )}

        {/* 进度条 */}
        {progress && (
          <Progress
            percent={progress.percent}
            status={progress.status}
            size="small"
            showInfo={false}
          />
        )}

        {/* 额外内容 */}
        {extra && <div>{extra}</div>}
      </Space>
    </Card>
  );
};

export default MetricsCard;

