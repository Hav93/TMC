import React, { useState } from 'react';
import { 
  Card, 
  Tabs, 
  Row, 
  Col, 
  Statistic,
  Modal,
  Typography
} from 'antd';
import { 
  LinkOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FolderOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { resourceMonitorService } from '../../services/resourceMonitor';
import type { ResourceMonitorRule } from '../../services/resourceMonitor';
import RuleList from './RuleList';
import RuleForm from './RuleForm';
import RecordList from './RecordList';

const { Title } = Typography;

const ResourceMonitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');
  const [formVisible, setFormVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ResourceMonitorRule | undefined>();

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['resource-monitor-stats'],
    queryFn: () => resourceMonitorService.getStats(),
    refetchInterval: 30000, // 每30秒刷新一次
  });

  // 打开创建表单
  const handleCreate = () => {
    setEditingRule(undefined);
    setFormVisible(true);
  };

  // 打开编辑表单
  const handleEdit = (rule: ResourceMonitorRule) => {
    setEditingRule(rule);
    setFormVisible(true);
  };

  // 关闭表单
  const handleFormClose = () => {
    setFormVisible(false);
    setEditingRule(undefined);
  };

  // Tab配置
  const tabItems = [
    {
      key: 'rules',
      label: (
        <span>
          <FolderOutlined />
          监控规则
        </span>
      ),
      children: (
        <RuleList 
          onEdit={handleEdit}
          onCreate={handleCreate}
        />
      ),
    },
    {
      key: 'records',
      label: (
        <span>
          <FileTextOutlined />
          资源记录
        </span>
      ),
      children: <RecordList />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <Title level={2} style={{ marginBottom: 24 }}>
        <LinkOutlined /> 资源监控
      </Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总规则数"
              value={stats?.total_rules || 0}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="活跃规则"
              value={stats?.active_rules || 0}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总记录数"
              value={stats?.total_records || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="转存成功"
              value={stats?.saved_records || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容区 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>

      {/* 规则表单弹窗 */}
      <Modal
        title={editingRule ? '编辑监控规则' : '新建监控规则'}
        open={formVisible}
        onCancel={handleFormClose}
        footer={null}
        width={800}
        destroyOnClose
      >
        <RuleForm
          rule={editingRule}
          onSuccess={handleFormClose}
          onCancel={handleFormClose}
        />
      </Modal>
    </div>
  );
};

export default ResourceMonitor;

