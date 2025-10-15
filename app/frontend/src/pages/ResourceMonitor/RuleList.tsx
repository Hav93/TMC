import React, { useState } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Tag, 
  Switch, 
  message,
  Input,
  Tooltip,
  Modal,
  Badge
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ReloadOutlined,
  LinkOutlined,
  ExclamationCircleOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { resourceMonitorService } from '../../services/resourceMonitor';
import type { ResourceMonitorRule } from '../../services/resourceMonitor';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { confirm } = Modal;

interface RuleListProps {
  onEdit?: (rule: ResourceMonitorRule) => void;
  onCreate?: () => void;
}

const RuleList: React.FC<RuleListProps> = ({ onEdit, onCreate }) => {
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 获取规则列表
  const { data: rules = [], isLoading, refetch } = useQuery({
    queryKey: ['resource-monitor-rules'],
    queryFn: () => resourceMonitorService.getRules(),
  });

  // 切换规则状态
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => 
      resourceMonitorService.toggleRule(id, isActive),
    onSuccess: () => {
      message.success('规则状态已更新');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '状态更新失败');
    },
  });

  // 删除规则
  const deleteMutation = useMutation({
    mutationFn: (id: number) => resourceMonitorService.deleteRule(id),
    onSuccess: () => {
      message.success('规则已删除');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-rules'] });
      setSelectedRowKeys([]);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败');
    },
  });

  // 批量删除
  const batchDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => resourceMonitorService.batchDeleteRules(ids),
    onSuccess: () => {
      message.success('批量删除成功');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-rules'] });
      setSelectedRowKeys([]);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '批量删除失败');
    },
  });

  // 批量启用/禁用
  const batchToggleMutation = useMutation({
    mutationFn: ({ ids, isActive }: { ids: number[]; isActive: boolean }) => 
      resourceMonitorService.batchToggleRules(ids, isActive),
    onSuccess: () => {
      message.success('批量操作成功');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-rules'] });
      setSelectedRowKeys([]);
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '批量操作失败');
    },
  });

  // 处理删除
  const handleDelete = (record: ResourceMonitorRule) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除监控规则"${record.name}"吗？相关的资源记录不会被删除。`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(record.id!),
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    confirm({
      title: '确认批量删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除选中的 ${selectedRowKeys.length} 条规则吗？`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => batchDeleteMutation.mutate(selectedRowKeys as number[]),
    });
  };

  // 筛选规则
  const filteredRules = rules.filter(rule => 
    rule.name.toLowerCase().includes(searchText.toLowerCase())
  );

  // 链接类型图标
  const getLinkTypeIcon = (type: string) => {
    switch (type) {
      case 'pan115':
        return <CloudUploadOutlined style={{ color: '#1890ff' }} />;
      case 'magnet':
        return <LinkOutlined style={{ color: '#722ed1' }} />;
      case 'ed2k':
        return <LinkOutlined style={{ color: '#13c2c2' }} />;
      default:
        return <LinkOutlined />;
    }
  };

  // 链接类型标签
  const getLinkTypeTag = (type: string) => {
    const colors: Record<string, string> = {
      pan115: 'blue',
      magnet: 'purple',
      ed2k: 'cyan',
    };
    const labels: Record<string, string> = {
      pan115: '115网盘',
      magnet: '磁力链接',
      ed2k: 'ed2k链接',
    };
    return (
      <Tag color={colors[type] || 'default'} icon={getLinkTypeIcon(type)}>
        {labels[type] || type}
      </Tag>
    );
  };

  // 表格列定义
  const columns: ColumnsType<ResourceMonitorRule> = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left',
      render: (text, record) => (
        <Space>
          <Badge status={record.is_active ? 'success' : 'default'} />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '源聊天',
      dataIndex: 'source_chats',
      key: 'source_chats',
      width: 200,
      render: (chats: string[]) => (
        <Tooltip title={chats.join(', ')}>
          <span>
            {chats.length > 0 ? `${chats.length} 个聊天` : '未设置'}
          </span>
        </Tooltip>
      ),
    },
    {
      title: '链接类型',
      dataIndex: 'link_types',
      key: 'link_types',
      width: 250,
      render: (types: string[] = ['pan115', 'magnet', 'ed2k']) => (
        <Space size={[0, 4]} wrap>
          {types.map(type => getLinkTypeTag(type))}
        </Space>
      ),
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      width: 150,
      render: (keywords: any[] = []) => (
        <Tooltip title={keywords.map(k => k.keyword).join(', ')}>
          <span>
            {keywords.length > 0 ? `${keywords.length} 个关键词` : '无限制'}
          </span>
        </Tooltip>
      ),
    },
    {
      title: '自动转存',
      dataIndex: 'auto_save_to_115',
      key: 'auto_save_to_115',
      width: 100,
      align: 'center',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? '已启用' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '去重',
      dataIndex: 'enable_deduplication',
      key: 'enable_deduplication',
      width: 100,
      align: 'center',
      render: (enabled: boolean, record) => (
        <Tooltip title={enabled ? `时间窗口: ${record.dedup_time_window}小时` : '未启用'}>
          <Tag color={enabled ? 'processing' : 'default'}>
            {enabled ? '已启用' : '已禁用'}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center',
      render: (isActive: boolean, record) => (
        <Switch
          checked={isActive}
          loading={toggleMutation.isPending}
          onChange={(checked) => toggleMutation.mutate({ id: record.id!, isActive: checked })}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit?.(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              loading={deleteMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 行选择配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  };

  return (
    <div>
      {/* 工具栏 */}
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={onCreate}
          >
            新建规则
          </Button>
          {selectedRowKeys.length > 0 && (
            <>
              <Button
                onClick={() => batchToggleMutation.mutate({ ids: selectedRowKeys as number[], isActive: true })}
                loading={batchToggleMutation.isPending}
              >
                批量启用
              </Button>
              <Button
                onClick={() => batchToggleMutation.mutate({ ids: selectedRowKeys as number[], isActive: false })}
                loading={batchToggleMutation.isPending}
              >
                批量禁用
              </Button>
              <Button
                danger
                onClick={handleBatchDelete}
                loading={batchDeleteMutation.isPending}
              >
                批量删除 ({selectedRowKeys.length})
              </Button>
            </>
          )}
        </Space>
        <Space>
          <Search
            placeholder="搜索规则名称"
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
        dataSource={filteredRules}
        loading={isLoading}
        rowSelection={rowSelection}
        pagination={{
          total: filteredRules.length,
          pageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条规则`,
        }}
        scroll={{ x: 1500 }}
      />
    </div>
  );
};

export default RuleList;

