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
  Typography,
  Button,
  Modal,
  Form,
  Select,
  Checkbox,
  message,
  Space
} from 'antd';
import { 
  BellOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BarChartOutlined,
  FileTextOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { notificationService } from '../../services/notifications';
import NotificationRuleList from './NotificationRuleList';
import NotificationLogList from './NotificationLogList';

const { Title } = Typography;

const NotificationsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');
  const [testVisible, setTestVisible] = useState(false);
  const [testForm] = Form.useForm();

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['notification-stats'],
    queryFn: () => notificationService.getStats(),
    refetchInterval: 30000, // 每30秒刷新一次
  });

  // 通知类型列表（用于测试发送）
  const { data: typeList } = useQuery({
    queryKey: ['notification-types'],
    queryFn: () => notificationService.getTypes(),
  });

  const handleOpenTest = () => {
    setTestVisible(true);
    testForm.setFieldsValue({
      notification_type: typeList?.[0]?.type,
      channels: ['telegram'],
    });
  };

  const handleSendTest = async () => {
    try {
      const values = await testForm.validateFields();
      const ok = await notificationService.testNotification(values.notification_type, values.channels);
      if (ok?.success !== false) {
        message.success('测试通知已发送');
      } else {
        message.error(ok?.message || '测试发送失败');
      }
      setTestVisible(false);
    } catch {}
  };

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
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={2} style={{ marginBottom: 0 }}>
            <BellOutlined /> 推送通知系统
          </Title>
          <Space>
            <Button icon={<ExperimentOutlined />} onClick={handleOpenTest}>测试通知</Button>
          </Space>
        </div>
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

      {/* 测试通知弹窗 */}
      <Modal
        title="发送测试通知"
        open={testVisible}
        onCancel={() => setTestVisible(false)}
        onOk={handleSendTest}
        destroyOnClose
      >
        <Form form={testForm} layout="vertical">
          <Form.Item name="notification_type" label="通知类型" rules={[{ required: true, message: '请选择通知类型' }]}> 
            <Select
              options={(typeList || []).map((t) => ({ label: t.name || t.type, value: t.type }))}
              placeholder="选择要测试的通知类型"
            />
          </Form.Item>
          <Form.Item name="channels" label="通知方式" rules={[{ required: true, message: '请选择通知方式' }]}> 
            <Checkbox.Group options={[
              { label: 'Telegram', value: 'telegram' },
              { label: 'Webhook', value: 'webhook' },
              // { label: 'Email', value: 'email' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default NotificationsPage;
