import React, { useState } from 'react';
import { 
  Card, 
  Tabs, 
  Button,
  Space,
  Typography,
  message,
  Spin
} from 'antd';
import { 
  DashboardOutlined,
  HeartOutlined,
  ReloadOutlined,
  ClearOutlined,
  SaveOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { performanceService } from '../../services/performance';
import RealtimeDashboard from './RealtimeDashboard';
import SystemHealth from './SystemHealth';

const { Title } = Typography;

/**
 * 性能监控主页面
 * 
 * 功能：
 * - 实时监控仪表板
 * - 系统健康状态
 * - 缓存管理
 * - 批量写入器管理
 */
const PerformanceMonitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const queryClient = useQueryClient();

  // 获取性能统计（自动刷新）
  const { data: stats, isLoading, refetch } = useQuery({
    queryKey: ['performance-stats'],
    queryFn: () => performanceService.getStats(),
    refetchInterval: 5000, // 每5秒刷新一次
  });

  // 清空缓存
  const clearCacheMutation = useMutation({
    mutationFn: () => performanceService.clearCache(),
    onSuccess: () => {
      message.success('缓存已清空');
      queryClient.invalidateQueries({ queryKey: ['performance-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '清空缓存失败');
    },
  });

  // 刷新批量写入器
  const flushBatchWriterMutation = useMutation({
    mutationFn: () => performanceService.flushBatchWriter(),
    onSuccess: () => {
      message.success('批量写入器已刷新');
      queryClient.invalidateQueries({ queryKey: ['performance-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '刷新失败');
    },
  });

  // 清空过滤引擎缓存
  const clearFilterCacheMutation = useMutation({
    mutationFn: () => performanceService.clearFilterEngineCache(),
    onSuccess: () => {
      message.success('过滤引擎缓存已清空');
      queryClient.invalidateQueries({ queryKey: ['performance-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '清空失败');
    },
  });

  // Tab配置
  const tabItems = [
    {
      key: 'dashboard',
      label: (
        <span>
          <DashboardOutlined />
          实时监控
        </span>
      ),
      children: stats ? (
        <RealtimeDashboard stats={stats} loading={isLoading} />
      ) : (
        <Spin tip="加载中..." />
      ),
    },
    {
      key: 'health',
      label: (
        <span>
          <HeartOutlined />
          系统健康
        </span>
      ),
      children: stats ? (
        <SystemHealth stats={stats} loading={isLoading} />
      ) : (
        <Spin tip="加载中..." />
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和操作按钮 */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>
          <DashboardOutlined /> 性能监控
        </Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            刷新数据
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={() => clearCacheMutation.mutate()}
            loading={clearCacheMutation.isPending}
          >
            清空缓存
          </Button>
          <Button
            icon={<SaveOutlined />}
            onClick={() => flushBatchWriterMutation.mutate()}
            loading={flushBatchWriterMutation.isPending}
          >
            刷新写入器
          </Button>
          <Button
            icon={<ClearOutlined />}
            onClick={() => clearFilterCacheMutation.mutate()}
            loading={clearFilterCacheMutation.isPending}
          >
            清空过滤缓存
          </Button>
        </Space>
      </div>

      {/* 主内容区 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>
    </div>
  );
};

export default PerformanceMonitor;

