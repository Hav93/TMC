/**
 * 资源监控规则列表
 */
import React, { useState } from 'react';
import {
  Button,
  Table,
  Space,
  Tag,
  Switch,
  Modal,
  Form,
  Input,
  Select,
  Checkbox,
  message,
  Popconfirm,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceMonitorApi, ResourceMonitorRule } from '../../services/resourceMonitor';

const { TextArea } = Input;
const { Option } = Select;

const RuleList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<ResourceMonitorRule | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取规则列表
  const { data: rulesData, isLoading } = useQuery({
    queryKey: ['resource-rules'],
    queryFn: async () => {
      const res = await resourceMonitorApi.getRules();
      return res.data;
    },
  });

  // 创建/更新规则
  const saveMutation = useMutation({
    mutationFn: async (values: any) => {
      if (editingRule) {
        return resourceMonitorApi.updateRule(editingRule.id, values);
      } else {
        return resourceMonitorApi.createRule(values);
      }
    },
    onSuccess: () => {
      message.success(editingRule ? '规则更新成功' : '规则创建成功');
      setIsModalVisible(false);
      setEditingRule(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['resource-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '操作失败');
    },
  });

  // 删除规则
  const deleteMutation = useMutation({
    mutationFn: (ruleId: number) => resourceMonitorApi.deleteRule(ruleId),
    onSuccess: () => {
      message.success('规则删除成功');
      queryClient.invalidateQueries({ queryKey: ['resource-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 切换规则状态
  const toggleMutation = useMutation({
    mutationFn: ({ ruleId, isActive }: { ruleId: number; isActive: boolean }) =>
      resourceMonitorApi.updateRule(ruleId, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource-rules'] });
    },
  });

  const handleCreate = () => {
    setEditingRule(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (rule: ResourceMonitorRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      ...rule,
      source_chats: rule.source_chats.join(','),
      include_keywords: rule.include_keywords.join(','),
      exclude_keywords: rule.exclude_keywords.join(','),
    });
    setIsModalVisible(true);
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 处理数据格式
      const data = {
        ...values,
        source_chats: values.source_chats
          ? values.source_chats.split(',').map((id: string) => parseInt(id.trim())).filter((id: number) => !isNaN(id))
          : [],
        include_keywords: values.include_keywords
          ? values.include_keywords.split(',').map((kw: string) => kw.trim()).filter((kw: string) => kw)
          : [],
        exclude_keywords: values.exclude_keywords
          ? values.exclude_keywords.split(',').map((kw: string) => kw.trim()).filter((kw: string) => kw)
          : [],
      };

      saveMutation.mutate(data);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '监控来源',
      dataIndex: 'source_chats',
      key: 'source_chats',
      width: 120,
      render: (chats: number[]) => <Tag>{chats.length} 个群组</Tag>,
    },
    {
      title: '链接类型',
      key: 'link_types',
      width: 150,
      render: (_: any, record: ResourceMonitorRule) => (
        <Space size={4}>
          {record.monitor_pan115 && <Tag color="blue">115</Tag>}
          {record.monitor_magnet && <Tag color="green">磁力</Tag>}
          {record.monitor_ed2k && <Tag color="orange">ed2k</Tag>}
        </Space>
      ),
    },
    {
      title: '目标路径',
      dataIndex: 'target_path',
      key: 'target_path',
      width: 180,
      ellipsis: true,
    },
    {
      title: '自动转存',
      dataIndex: 'auto_save',
      key: 'auto_save',
      width: 80,
      render: (autoSave: boolean) => (
        <Tag color={autoSave ? 'success' : 'default'}>
          {autoSave ? '是' : '否'}
        </Tag>
      ),
    },
    {
      title: '统计',
      key: 'stats',
      width: 120,
      render: (_: any, record: ResourceMonitorRule) => (
        <Space split="|" size={4}>
          <span style={{ color: '#1890ff' }}>捕获 {record.total_captured}</span>
          <span style={{ color: '#52c41a' }}>转存 {record.total_saved}</span>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: boolean, record: ResourceMonitorRule) => (
        <Switch
          checked={isActive}
          onChange={(checked) => toggleMutation.mutate({ ruleId: record.id, isActive: checked })}
          checkedChildren="启用"
          unCheckedChildren="暂停"
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ResourceMonitorRule) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个规则吗？"
            description="删除后将无法恢复，相关的资源记录也会被删除。"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rules = rulesData?.rules || [];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          新建规则
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={rules}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条规则`,
        }}
      />

      <Modal
        title={editingRule ? '编辑监控规则' : '新建监控规则'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingRule(null);
          form.resetFields();
        }}
        width={700}
        confirmLoading={saveMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            monitor_pan115: true,
            monitor_magnet: true,
            monitor_ed2k: true,
            auto_save: false,
          }}
        >
          <Form.Item
            label="规则名称"
            name="name"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="如：电影资源、日剧追番" />
          </Form.Item>

          <Form.Item
            label="监控来源"
            name="source_chats"
            rules={[{ required: true, message: '请输入要监控的群组ID' }]}
            tooltip="输入群组/频道的ID，多个用逗号分隔"
          >
            <Input placeholder="如：-1001234567890, -1009876543210" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="包含关键词（可选）" name="include_keywords">
                <Input placeholder="多个关键词用逗号分隔，如：4K,蓝光" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="排除关键词（可选）" name="exclude_keywords">
                <Input placeholder="多个关键词用逗号分隔，如：枪版,CAM" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="链接类型">
            <Space>
              <Form.Item name="monitor_pan115" valuePropName="checked" noStyle>
                <Checkbox>115分享链接</Checkbox>
              </Form.Item>
              <Form.Item name="monitor_magnet" valuePropName="checked" noStyle>
                <Checkbox>磁力链接</Checkbox>
              </Form.Item>
              <Form.Item name="monitor_ed2k" valuePropName="checked" noStyle>
                <Checkbox>ed2k链接</Checkbox>
              </Form.Item>
            </Space>
          </Form.Item>

          <Form.Item
            label="目标路径"
            name="target_path"
            rules={[{ required: true, message: '请输入115网盘目标路径' }]}
            tooltip="资源会保持原有文件夹结构转存到此路径下"
          >
            <Input placeholder="如：/电影 或 /剧集/日剧" />
          </Form.Item>

          <Form.Item name="auto_save" valuePropName="checked">
            <Checkbox>自动转存到115（无需手动确认）</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RuleList;

