/**
 * 推送通知系统 - 主页面
 * 
 * 功能：
 * - Tab切换（通知规则/通知历史）
 * - 统计卡片展示
 * - 卡片式规则管理
 */

import React, { useState } from 'react';
import { 
  Card, 
  Tabs, 
  Row, 
  Col, 
  Statistic,
  Typography
} from 'antd';
import { 
  BellOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BarChartOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { notificationService } from '../../services/notifications';
import NotificationRuleList from './NotificationRuleList';
import NotificationLogList from './NotificationLogList';

const { Title } = Typography;

const NotificationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['notification-stats'],
    queryFn: () => notificationService.getStats(),
    refetchInterval: 30000, // 每30秒刷新一次
  });

  // Tab配置
  const tabItems = [
    {
      key: 'rules',
      label: (
        <span>
          <BellOutlined />
          通知规则
        </span>
      ),
      children: <NotificationRuleList />,
    },
    {
      key: 'logs',
      label: (
        <span>
          <FileTextOutlined />
          通知历史
        </span>
      ),
      children: <NotificationLogList />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <BellOutlined /> 推送通知系统
        </Title>
        <div style={{ color: '#666', fontSize: '14px', marginTop: '8px' }}>
          为每个通知类型配置推送规则，支持Telegram和Webhook两种通知方式
        </div>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总规则数"
              value={stats?.total_rules || 0}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃规则"
              value={stats?.active_rules || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日发送"
              value={stats?.total_sent_today || 0}
              prefix={<BellOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日失败"
              value={stats?.total_failed_today || 0}
              valueStyle={{ color: stats?.total_failed_today ? '#cf1322' : undefined }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Tab内容 */}
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

export default NotificationsPage;
