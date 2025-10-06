import React from 'react';
import { Skeleton } from 'antd';
import ReactECharts from 'echarts-for-react';
import { useThemeContext } from '../../../theme';

interface MessageChartProps {
  data: Array<{
    date: string;
    count: number;
  }>;
  loading?: boolean;
}

const MessageChart: React.FC<MessageChartProps> = ({ data, loading = false }) => {
  const { colors } = useThemeContext();
  
  if (loading) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  // ECharts 配置 - 使用主题颜色
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: 'transparent',
      textStyle: {
        color: '#fff',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: colors.borderBase,
        },
      },
      axisLabel: {
        color: colors.textSecondary,
      },
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: colors.borderBase,
        },
      },
      axisLabel: {
        color: colors.textSecondary,
      },
      splitLine: {
        lineStyle: {
          color: colors.borderLight,
        },
      },
    },
    series: [
      {
        name: '消息数量',
        type: 'line',
        smooth: true,
        data: data.map(item => item.count),
        itemStyle: {
          color: colors.primary,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(24, 144, 255, 0.3)',
              },
              {
                offset: 1,
                color: 'rgba(24, 144, 255, 0.05)',
              },
            ],
          },
        },
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: 300 }}
      opts={{ renderer: 'svg' }}
    />
  );
};

export default MessageChart;