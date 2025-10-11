/**
 * 资源记录列表
 */
import React, { useState } from 'react';
import {
  Table,
  Space,
  Tag,
  Button,
  Input,
  Select,
  Modal,
  Descriptions,
  Typography,
  message,
  Popconfirm,
} from 'antd';
import {
  EyeOutlined,
  DeleteOutlined,
  CloudUploadOutlined,
  StopOutlined,
  LinkOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceMonitorApi, ResourceRecord } from '../../services/resourceMonitor';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { Text, Paragraph } = Typography;

const RecordList: React.FC = () => {
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentRecord, setCurrentRecord] = useState<ResourceRecord | null>(null);
  const [filters, setFilters] = useState({
    status: undefined as string | undefined,
    search: undefined as string | undefined,
  });
  const queryClient = useQueryClient();

  // 获取记录列表
  const { data: recordsData, isLoading } = useQuery({
    queryKey: ['resource-records', filters],
    queryFn: async () => {
      const res = await resourceMonitorApi.getRecords(filters);
      return res.data;
    },
  });

  // 批量操作
  const batchMutation = useMutation({
    mutationFn: (action: 'save' | 'delete' | 'ignore') =>
      resourceMonitorApi.batchOperation({
        record_ids: selectedRowKeys as number[],
        action,
      }),
    onSuccess: (_, action) => {
      const actionText = action === 'save' ? '转存' : action === 'delete' ? '删除' : '忽略';
      message.success(`批量${actionText}成功`);
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['resource-records'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '操作失败');
    },
  });

  const handleViewDetail = async (record: ResourceRecord) => {
    const res = await resourceMonitorApi.getRecordDetail(record.id);
    setCurrentRecord(res.data.record);
    setDetailModalVisible(true);
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '待处理' },
      saved: { color: 'success', text: '已转存' },
      failed: { color: 'error', text: '失败' },
      ignored: { color: 'warning', text: '已忽略' },
    };
    const config = statusMap[status] || statusMap.pending;
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '消息内容',
      dataIndex: 'message_text',
      key: 'message_text',
      width: 300,
      ellipsis: true,
      render: (text: string) => (
        <Paragraph
          ellipsis={{ rows: 2, expandable: false }}
          style={{ marginBottom: 0 }}
        >
          {text}
        </Paragraph>
      ),
    },
    {
      title: '来源',
      key: 'source',
      width: 150,
      render: (_: any, record: ResourceRecord) => (
        <div>
          <div>{record.chat_title}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.sender_name}
          </Text>
        </div>
      ),
    },
    {
      title: '链接',
      key: 'links',
      width: 120,
      render: (_: any, record: ResourceRecord) => {
        const total =
          record.pan115_links.length +
          record.magnet_links.length +
          record.ed2k_links.length;
        return (
          <Space size={4}>
            {record.pan115_links.length > 0 && (
              <Tag color="blue">115 ({record.pan115_links.length})</Tag>
            )}
            {record.magnet_links.length > 0 && (
              <Tag color="green">磁力 ({record.magnet_links.length})</Tag>
            )}
            {record.ed2k_links.length > 0 && (
              <Tag color="orange">ed2k ({record.ed2k_links.length})</Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '规则',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '捕获时间',
      dataIndex: 'detected_at',
      key: 'detected_at',
      width: 150,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ResourceRecord) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending' && (
            <Button
              type="link"
              size="small"
              icon={<CloudUploadOutlined />}
              onClick={() => batchMutation.mutate('save')}
            >
              转存
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const records = recordsData?.records || [];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索消息内容"
            style={{ width: 300 }}
            onSearch={(value) => setFilters({ ...filters, search: value || undefined })}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            style={{ width: 120 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, status: value })}
          >
            <Option value="pending">待处理</Option>
            <Option value="saved">已转存</Option>
            <Option value="failed">失败</Option>
            <Option value="ignored">已忽略</Option>
          </Select>
          {selectedRowKeys.length > 0 && (
            <>
              <Popconfirm
                title="确定要批量转存选中的记录吗？"
                onConfirm={() => batchMutation.mutate('save')}
              >
                <Button icon={<CloudUploadOutlined />}>
                  批量转存 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
              <Popconfirm
                title="确定要批量忽略选中的记录吗？"
                onConfirm={() => batchMutation.mutate('ignore')}
              >
                <Button icon={<StopOutlined />}>批量忽略</Button>
              </Popconfirm>
              <Popconfirm
                title="确定要批量删除选中的记录吗？"
                onConfirm={() => batchMutation.mutate('delete')}
              >
                <Button danger icon={<DeleteOutlined />}>
                  批量删除
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={records}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 1200 }}
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条记录`,
          total: recordsData?.total || 0,
        }}
      />

      <Modal
        title="资源详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
        ]}
      >
        {currentRecord && (
          <div>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="来源群组" span={2}>
                {currentRecord.chat_title}
              </Descriptions.Item>
              <Descriptions.Item label="发送者">
                {currentRecord.sender_name}
              </Descriptions.Item>
              <Descriptions.Item label="捕获时间">
                {dayjs(currentRecord.detected_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="规则">
                {currentRecord.rule_name}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(currentRecord.status)}
              </Descriptions.Item>
              <Descriptions.Item label="目标路径" span={2}>
                {currentRecord.target_path}
              </Descriptions.Item>
            </Descriptions>

            <div style={{ marginTop: 16 }}>
              <Text strong>消息内容：</Text>
              <Paragraph
                copyable
                style={{
                  marginTop: 8,
                  padding: 12,
                  background: '#f5f5f5',
                  borderRadius: 4,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {currentRecord.message_text}
              </Paragraph>
            </div>

            {currentRecord.pan115_links.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>115分享链接：</Text>
                {currentRecord.pan115_links.map((link, index) => (
                  <Paragraph key={index} copyable style={{ marginTop: 4 }}>
                    {link}
                  </Paragraph>
                ))}
              </div>
            )}

            {currentRecord.magnet_links.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>磁力链接：</Text>
                {currentRecord.magnet_links.map((link, index) => (
                  <Paragraph
                    key={index}
                    copyable
                    ellipsis={{ rows: 1, expandable: true }}
                    style={{ marginTop: 4 }}
                  >
                    {link}
                  </Paragraph>
                ))}
              </div>
            )}

            {currentRecord.ed2k_links.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong>ed2k链接：</Text>
                {currentRecord.ed2k_links.map((link, index) => (
                  <Paragraph
                    key={index}
                    copyable
                    ellipsis={{ rows: 1, expandable: true }}
                    style={{ marginTop: 4 }}
                  >
                    {link}
                  </Paragraph>
                ))}
              </div>
            )}

            {currentRecord.error_message && (
              <div style={{ marginTop: 16 }}>
                <Text strong type="danger">
                  错误信息：
                </Text>
                <Paragraph style={{ marginTop: 4, color: '#ff4d4f' }}>
                  {currentRecord.error_message}
                </Paragraph>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RecordList;

