import React, { useState } from 'react';
import { Tabs, Card, Row, Col, Statistic, Space } from 'antd';
import {
  DashboardOutlined,
  ThunderboltOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import NewDashboard from './NewDashboard';
import RealtimeDashboard from '../PerformanceMonitor/RealtimeDashboard';
import SystemHealth from '../PerformanceMonitor/SystemHealth';
import { performanceService } from '../../services/performance';

/**
 * 整合仪表盘
 * 
 * 包含三个Tab：
 * 1. 业务概览 - 业务数据统计和分析
 * 2. 性能监控 - 系统性能指标和监控
 * 3. 系统健康 - 系统资源和健康状态
 */
const IntegratedDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('business');

  // 获取性能统计（用于顶部摘要）
  const { data: perfStats } = useQuery({
    queryKey: ['performance-stats-summary'],
    queryFn: () => performanceService.getStats(),
    refetchInterval: 10000, // 每10秒刷新一次
  });

  // 计算系统健康状态
  const getSystemStatus = () => {
    if (!perfStats) return { status: 'loading', color: '#d9d9d9', text: '加载中' };
    
    const cacheUsage = perfStats.message_cache?.usage_percent || 0;
    const queueSize = perfStats.retry_queue?.current_queue_size || 0;
    const avgProcessingTime = perfStats.message_dispatcher?.avg_processing_time || 0;
    
    // 判断健康状态
    if (cacheUsage > 90 || queueSize > 50 || avgProcessingTime > 1000) {
      return { status: 'error', color: '#ff4d4f', text: '异常' };
    } else if (cacheUsage > 70 || queueSize > 20 || avgProcessingTime > 500) {
      return { status: 'warning', color: '#faad14', text: '警告' };
    } else {
      return { status: 'success', color: '#52c41a', text: '正常' };
    }
  };

  const systemStatus = getSystemStatus();

  return (
    <div style={{ padding: '24px' }}>
      {/* 顶部性能状态摘要条 */}
      <Card 
        size="small" 
        style={{ 
          marginBottom: 16,
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
          border: `1px solid ${systemStatus.color}20`
        }}
        bodyStyle={{ padding: '12px 24px' }}
      >
        <Row gutter={24} align="middle">
          <Col xs={24} sm={6}>
            <Space>
              {systemStatus.status === 'success' && <CheckCircleOutlined style={{ fontSize: 20, color: systemStatus.color }} />}
              {systemStatus.status === 'warning' && <WarningOutlined style={{ fontSize: 20, color: systemStatus.color }} />}
              {systemStatus.status === 'error' && <WarningOutlined style={{ fontSize: 20, color: systemStatus.color }} />}
              <div>
                <div style={{ fontSize: 12, opacity: 0.65 }}>系统状态</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: systemStatus.color }}>
                  {systemStatus.text}
                </div>
              </div>
            </Space>
          </Col>
          <Col xs={12} sm={6}>
            <Statistic 
              title="今日消息" 
              value={perfStats?.message_dispatcher?.total_messages || 0}
              valueStyle={{ fontSize: 18 }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic 
              title="缓存使用率" 
              value={perfStats?.message_cache?.usage_percent || 0}
              suffix="%"
              valueStyle={{ 
                fontSize: 18,
                color: (perfStats?.message_cache?.usage_percent || 0) > 80 ? '#faad14' : '#52c41a'
              }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic 
              title="队列任务" 
              value={perfStats?.retry_queue?.current_queue_size || 0}
              valueStyle={{ 
                fontSize: 18,
                color: (perfStats?.retry_queue?.current_queue_size || 0) > 10 ? '#faad14' : '#52c41a'
              }}
            />
          </Col>
        </Row>
      </Card>

      {/* Tab 切换 */}
      <Card bodyStyle={{ padding: 0 }} style={{ overflow: 'hidden' }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
          style={{ 
            paddingLeft: '16px',
            paddingRight: '16px',
          }}
          items={[
            {
              key: 'business',
              label: (
                <span>
                  <DashboardOutlined />
                  业务概览
                </span>
              ),
              children: (
                <div style={{ padding: '24px' }}>
                  <NewDashboard />
                </div>
              ),
            },
            {
              key: 'performance',
              label: (
                <span>
                  <ThunderboltOutlined />
                  性能监控
                </span>
              ),
              children: (
                <div style={{ padding: '24px' }}>
                  {perfStats ? (
                    <RealtimeDashboard stats={perfStats} loading={false} />
                  ) : (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                      加载中...
                    </div>
                  )}
                </div>
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
              children: (
                <div style={{ padding: '24px' }}>
                  {perfStats ? (
                    <SystemHealth stats={perfStats} loading={false} />
                  ) : (
                    <div style={{ textAlign: 'center', padding: '60px 0' }}>
                      加载中...
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default IntegratedDashboard;

