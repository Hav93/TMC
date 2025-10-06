import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Modal,
  Form,
  Input,
  Switch,
  message,
  Tooltip
} from 'antd';
import TableEmpty from '../../components/common/TableEmpty';
import { useThemeContext } from '../../theme';
// z-index问题已在 styles/components/modal.css 中解决
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { keywordsApi } from '../../services/rules';

const { Title } = Typography;

interface Keyword {
  id: number;
  rule_id: number;
  keyword: string;
  is_blacklist: boolean;
  created_at: string;
}

const KeywordsPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const ruleId = id ? parseInt(id, 10) : 0;
  const { colors } = useThemeContext();
  
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingKeyword, setEditingKeyword] = useState<Keyword | null>(null);
  const [form] = Form.useForm();

  // 获取关键词列表
  const { data: keywords = [], isLoading } = useQuery({
    queryKey: ['keywords', ruleId],
    queryFn: () => keywordsApi.getByRule(ruleId),
    enabled: !!ruleId,
  });

  // 创建关键词
  const createMutation = useMutation({
    mutationFn: keywordsApi.create,
    onSuccess: () => {
      message.success('关键词添加成功');
      queryClient.invalidateQueries({ queryKey: ['keywords', ruleId] });
      setIsModalVisible(false);
      form.resetFields();
    },
    onError: () => {
      message.error('关键词添加失败');
    },
  });

  // 更新关键词
  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Partial<Keyword>) => 
      keywordsApi.update(id, data),
    onSuccess: () => {
      message.success('关键词更新成功');
      queryClient.invalidateQueries({ queryKey: ['keywords', ruleId] });
      setIsModalVisible(false);
      setEditingKeyword(null);
      form.resetFields();
    },
    onError: () => {
      message.error('关键词更新失败');
    },
  });

  // 删除关键词
  const deleteMutation = useMutation({
    mutationFn: keywordsApi.delete,
    onSuccess: () => {
      message.success('关键词删除成功');
      queryClient.invalidateQueries({ queryKey: ['keywords', ruleId] });
    },
    onError: () => {
      message.error('关键词删除失败');
    },
  });

  const handleAdd = () => {
    setEditingKeyword(null);
    form.resetFields();
    setIsModalVisible(true);
  };

  const handleEdit = (keyword: Keyword) => {
    setEditingKeyword(keyword);
    form.setFieldsValue(keyword);
    setIsModalVisible(true);
  };

  const handleDelete = (keyword: Keyword) => {
    console.log('🔴 handleDelete called', keyword);
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除关键词"${keyword.keyword}"吗？`,
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        console.log('🔴 onOk called, deleting keyword id:', keyword.id);
        deleteMutation.mutate(keyword.id);
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingKeyword) {
        updateMutation.mutate({ id: editingKeyword.id, ...values });
      } else {
        createMutation.mutate({ rule_id: ruleId, ...values });
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const columns = [
    {
      title: '关键词',
      dataIndex: 'keyword',
      key: 'keyword',
      render: (text: string) => (
        <span style={{ color: colors.textPrimary, fontFamily: 'monospace' }}>{text}</span>
      ),
    },
    {
      title: '类型',
      dataIndex: 'is_blacklist',
      key: 'is_blacklist',
      width: 100,
      render: (is_blacklist: boolean) => (
        <span className={is_blacklist ? 'table-type-blacklist' : 'table-type-whitelist'}>
          {is_blacklist ? '黑名单' : '白名单'}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => (
        <span style={{ color: colors.textSecondary }}>
          {text ? new Date(text).toLocaleString() : '-'}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Keyword) => (
        <Space>
          <Tooltip title="编辑关键词">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除关键词">
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => {
                console.log('🔴 Button clicked!', record);
                handleDelete(record);
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/rules')}
            >
              返回规则列表
            </Button>
            <Title level={2} style={{ margin: 0, color: colors.textPrimary }}>
              关键词管理 (规则 #{ruleId})
            </Title>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加关键词
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={keywords}
          rowKey="id"
          loading={isLoading}
          locale={{
            emptyText: (
              <TableEmpty 
                icon="🔍"
                title="暂无关键词"
                description='点击"添加关键词"开始设置过滤条件'
              />
            )
          }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个关键词`,
          }}
          style={{ 
            background: 'transparent',
          }}
        />
      </Card>

      <Modal
        title={editingKeyword ? '编辑关键词' : '添加关键词'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingKeyword(null);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        className="glass-modal"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="关键词"
            name="keyword"
            rules={[{ required: true, message: '请输入关键词' }]}
          >
            <Input placeholder="输入关键词或正则表达式" />
          </Form.Item>
          <Form.Item
            label="类型"
            name="is_blacklist"
            valuePropName="checked"
            tooltip="黑名单：包含该关键词的消息不会被转发；白名单：只有包含该关键词的消息才会被转发"
          >
            <Switch
              checkedChildren="黑名单"
              unCheckedChildren="白名单"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KeywordsPage;
