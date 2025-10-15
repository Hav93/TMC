import React, { useState } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Tag, 
  message,
  Input,
  Select,
  DatePicker,
  Tooltip,
  Drawer,
  Descriptions,
  Typography,
  Badge
} from 'antd';
import { 
  ReloadOutlined,
  SearchOutlined,
  LinkOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceMonitorService } from '../../services/resourceMonitor';
import type { ResourceRecord, RecordQueryParams } from '../../services/resourceMonitor';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text, Paragraph } = Typography;

interface RecordListProps {
  ruleId?: number;
}

const RecordList: React.FC<RecordListProps> = ({ ruleId }) => {
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const [linkType, setLinkType] = useState<string>();
  const [saveStatus, setSaveStatus] = useState<string>();
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<ResourceRecord | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // 构建查询参数
  const queryParams: RecordQueryParams = {
    skip: 0,
    limit: 1000,
    ...(ruleId && { rule_id: ruleId }),
    ...(linkType && { link_type: linkType }),
    ...(saveStatus && { save_status: saveStatus }),
    ...(dateRange && {
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
    }),
  };

  // 获取记录列表
  const { data: records = [], isLoading, refetch, error } = useQuery({
    queryKey: ['resource-monitor-records', queryParams],
    queryFn: () => resourceMonitorService.getRecords(queryParams),
    retry: 1,
  });

  // 错误处理
  React.useEffect(() => {
    if (error) {
      console.error('获取资源记录失败:', error);
      message.error('获取资源记录失败，请刷新重试');
    }
  }, [error]);

  // 重试失败的任务
  const retryMutation = useMutation({
    mutationFn: (recordId: number) => resourceMonitorService.retryRecord(recordId),
    onSuccess: () => {
      message.success('已添加到重试队列');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-records'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '重试失败');
    },
  });

  // 筛选记录（添加安全检查）
  const filteredRecords = (records || []).filter(record => {
    if (!record) return false;
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      return (
        (record.link_url || '').toLowerCase().includes(searchLower) ||
        (record.rule_name || '').toLowerCase().includes(searchLower) ||
        (record.source_chat_name || '').toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  // 状态标签
  const getStatusTag = (status: string) => {
    const configs: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
      saving: { color: 'processing', icon: <SyncOutlined spin />, text: '转存中' },
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
    };
    const config = configs[status] || configs.pending;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 链接类型标签
  const getLinkTypeTag = (type: string) => {
    const configs: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pan115: { color: 'blue', icon: <CloudUploadOutlined />, text: '115网盘' },
      magnet: { color: 'purple', icon: <LinkOutlined />, text: '磁力链接' },
      ed2k: { color: 'cyan', icon: <LinkOutlined />, text: 'ed2k链接' },
    };
    const config = configs[type] || { color: 'default', icon: <LinkOutlined />, text: type };
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 查看详情
  const handleViewDetail = (record: ResourceRecord) => {
    setSelectedRecord(record);
    setDrawerVisible(true);
  };

  // 表格列定义
  const columns: ColumnsType<ResourceRecord> = [
    {
      title: '规则',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 150,
      render: (text) => text || '-',
    },
    {
      title: '链接类型',
      dataIndex: 'link_type',
      key: 'link_type',
      width: 120,
      render: (type) => getLinkTypeTag(type),
    },
    {
      title: '链接地址',
      dataIndex: 'link_url',
      key: 'link_url',
      width: 300,
      ellipsis: true,
      render: (url) => (
        <Tooltip title={url}>
          <Text copyable={{ text: url }} ellipsis>
            {url}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '来源',
      key: 'source',
      width: 150,
      render: (_, record) => (
        <div>
          <div>{record.source_chat_name || record.source_chat_id || '-'}</div>
          {record.message_id && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              消息ID: {record.message_id}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '转存状态',
      dataIndex: 'save_status',
      key: 'save_status',
      width: 100,
      align: 'center',
      render: (status) => getStatusTag(status),
    },
    {
      title: '转存路径',
      dataIndex: 'save_path',
      key: 'save_path',
      width: 200,
      ellipsis: true,
      render: (path) => path || '-',
    },
    {
      title: '重试次数',
      dataIndex: 'retry_count',
      key: 'retry_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Badge count={count} showZero style={{ backgroundColor: count > 0 ? '#faad14' : '#d9d9d9' }} />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {record.save_status === 'failed' && (
            <Tooltip title="重试">
              <Button
                type="link"
                size="small"
                icon={<SyncOutlined />}
                onClick={() => retryMutation.mutate(record.id)}
                loading={retryMutation.isPending}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 筛选工具栏 */}
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space wrap>
          <Select
            placeholder="链接类型"
            allowClear
            style={{ width: 150 }}
            value={linkType}
            onChange={setLinkType}
          >
            <Option value="pan115">115网盘</Option>
            <Option value="magnet">磁力链接</Option>
            <Option value="ed2k">ed2k链接</Option>
          </Select>
          <Select
            placeholder="转存状态"
            allowClear
            style={{ width: 120 }}
            value={saveStatus}
            onChange={setSaveStatus}
          >
            <Option value="pending">待处理</Option>
            <Option value="saving">转存中</Option>
            <Option value="success">成功</Option>
            <Option value="failed">失败</Option>
          </Select>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs] | null)}
            placeholder={['开始日期', '结束日期']}
          />
        </Space>
        <Space>
          <Search
            placeholder="搜索链接、规则、来源"
            allowClear
            style={{ width: 250 }}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            prefix={<SearchOutlined />}
          />
          <Tooltip title="刷新">
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            />
          </Tooltip>
        </Space>
      </Space>

      {/* 表格 */}
      <Table
        rowKey="id"
        columns={columns}
        dataSource={filteredRecords}
        loading={isLoading}
        pagination={{
          total: filteredRecords.length,
          pageSize: 50,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        scroll={{ x: 1500 }}
      />

      {/* 详情抽屉 */}
      <Drawer
        title="资源记录详情"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedRecord && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="ID">{selectedRecord.id}</Descriptions.Item>
            <Descriptions.Item label="规则">{selectedRecord.rule_name || '-'}</Descriptions.Item>
            <Descriptions.Item label="链接类型">
              {getLinkTypeTag(selectedRecord.link_type)}
            </Descriptions.Item>
            <Descriptions.Item label="链接地址">
              <Paragraph copyable ellipsis={{ rows: 2, expandable: true }}>
                {selectedRecord.link_url}
              </Paragraph>
            </Descriptions.Item>
            <Descriptions.Item label="来源聊天">
              {selectedRecord.source_chat_name || selectedRecord.source_chat_id || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="消息ID">{selectedRecord.message_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="消息内容">
              <Paragraph ellipsis={{ rows: 3, expandable: true }}>
                {selectedRecord.message_text || '-'}
              </Paragraph>
            </Descriptions.Item>
            <Descriptions.Item label="消息时间">
              {selectedRecord.message_date 
                ? new Date(selectedRecord.message_date).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="转存状态">
              {getStatusTag(selectedRecord.save_status)}
            </Descriptions.Item>
            <Descriptions.Item label="转存路径">
              {selectedRecord.save_path || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="转存时间">
              {selectedRecord.save_time 
                ? new Date(selectedRecord.save_time).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="错误信息">
              {selectedRecord.save_error ? (
                <Text type="danger">{selectedRecord.save_error}</Text>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="重试次数">
              <Badge count={selectedRecord.retry_count} showZero />
            </Descriptions.Item>
            <Descriptions.Item label="标签">
              {selectedRecord.tags && selectedRecord.tags.length > 0 ? (
                <Space size={[0, 4]} wrap>
                  {selectedRecord.tags.map((tag, index) => (
                    <Tag key={index}>{tag}</Tag>
                  ))}
                </Space>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedRecord.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {selectedRecord.updated_at 
                ? new Date(selectedRecord.updated_at).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
};

export default RecordList;

