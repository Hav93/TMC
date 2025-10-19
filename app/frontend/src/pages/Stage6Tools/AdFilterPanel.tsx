/**
 * 广告过滤面板
 */
import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Input, Table, Tag, message, Space, Modal, Form } from 'antd';
import { FilterOutlined, PlusOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import stage6Service from '../../services/stage6';

const { TextArea } = Input;

const AdFilterPanel: React.FC = () => {
  const [checkModalVisible, setCheckModalVisible] = useState(false);
  const [addRuleModalVisible, setAddRuleModalVisible] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['ad-filter-stats'],
    queryFn: () => stage6Service.getAdFilterStats(),
  });

  // 获取规则列表
  const { data: rules = [] } = useQuery({
    queryKey: ['ad-filter-rules'],
    queryFn: () => stage6Service.getAdFilterRules(),
  });

  // 获取白名单
  const { data: whitelist = [] } = useQuery({
    queryKey: ['ad-filter-whitelist'],
    queryFn: () => stage6Service.getAdFilterWhitelist(),
  });

  // 检查文件
  const checkMutation = useMutation({
    mutationFn: (values: { filename: string; file_size?: number }) =>
      stage6Service.checkFile(values.filename, values.file_size),
    onSuccess: (data) => {
      Modal.info({
        title: '检测结果',
        content: (
          <div>
            <p><strong>文件名：</strong>{data.filename}</p>
            <p><strong>是否广告：</strong>
              {data.is_ad ? (
                <Tag color="red">是</Tag>
              ) : (
                <Tag color="green">否</Tag>
              )}
            </p>
            <p><strong>动作：</strong>{data.action}</p>
            <p><strong>原因：</strong>{data.reason}</p>
          </div>
        ),
      });
    },
  });

  // 添加规则
  const addRuleMutation = useMutation({
    mutationFn: (values: any) => stage6Service.addAdFilterRule(values),
    onSuccess: () => {
      message.success('规则添加成功');
      setAddRuleModalVisible(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['ad-filter-rules'] });
      queryClient.invalidateQueries({ queryKey: ['ad-filter-stats'] });
    },
  });

  const handleCheck = (values: any) => {
    checkMutation.mutate(values);
    setCheckModalVisible(false);
    form.resetFields();
  };

  const handleAddRule = (values: any) => {
    addRuleMutation.mutate(values);
  };

  const ruleColumns = [
    {
      title: '模式',
      dataIndex: 'pattern',
      key: 'pattern',
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '动作',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => {
        const colorMap: Record<string, string> = {
          skip: 'orange',
          delete: 'red',
          quarantine: 'purple',
          allow: 'green',
        };
        return <Tag color={colorMap[action]}>{action}</Tag>;
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
    },
  ];

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总规则数"
              value={stats?.total_rules || 0}
              prefix={<FilterOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="高优先级规则"
              value={stats?.rules_by_priority?.high || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="中优先级规则"
              value={stats?.rules_by_priority?.medium || 0}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="白名单数量"
              value={stats?.whitelist_patterns || 0}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮 */}
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<FilterOutlined />}
          onClick={() => setCheckModalVisible(true)}
        >
          检查文件
        </Button>
        <Button
          icon={<PlusOutlined />}
          onClick={() => setAddRuleModalVisible(true)}
        >
          添加规则
        </Button>
      </Space>

      {/* 规则列表 */}
      <Card title="过滤规则" style={{ marginBottom: 16 }}>
        <Table
          dataSource={rules}
          columns={ruleColumns}
          rowKey="pattern"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* 白名单 */}
      <Card title="白名单">
        <div>
          {whitelist.map((pattern, index) => (
            <Tag key={index} style={{ marginBottom: 8 }}>
              {pattern}
            </Tag>
          ))}
        </div>
      </Card>

      {/* 检查文件Modal */}
      <Modal
        title="检查文件"
        open={checkModalVisible}
        onCancel={() => setCheckModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleCheck} layout="vertical">
          <Form.Item
            name="filename"
            label="文件名"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input placeholder="例如：广告.txt" />
          </Form.Item>
          <Form.Item name="file_size" label="文件大小（字节）">
            <Input type="number" placeholder="可选" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={checkMutation.isPending}>
              检查
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加规则Modal */}
      <Modal
        title="添加过滤规则"
        open={addRuleModalVisible}
        onCancel={() => setAddRuleModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} onFinish={handleAddRule} layout="vertical">
          <Form.Item
            name="pattern"
            label="文件名模式（正则表达式）"
            rules={[{ required: true, message: '请输入模式' }]}
          >
            <Input placeholder="例如：(?i).*广告.*" />
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ required: true }]}>
            <Input placeholder="规则描述" />
          </Form.Item>
          <Form.Item name="action" label="动作" initialValue="skip">
            <Input placeholder="skip/delete/quarantine/allow" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="min_size" label="最小文件大小（字节）">
                <Input type="number" placeholder="可选" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_size" label="最大文件大小（字节）">
                <Input type="number" placeholder="可选" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={addRuleMutation.isPending}>
              添加
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdFilterPanel;

