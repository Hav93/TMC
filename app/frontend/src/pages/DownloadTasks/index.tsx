import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Progress,
  message,
  Typography,
  Select,
  Tooltip,
  Modal,
  Row,
  Col,
  Badge,
  InputNumber
} from 'antd';
import TableEmpty from '../../components/common/TableEmpty';
import { useThemeContext } from '../../theme';
import { 
  ReloadOutlined,
  DeleteOutlined,
  RedoOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  FilterOutlined,
  ExclamationCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mediaFilesApi } from '../../services/mediaFiles';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import type { DownloadTask } from '../../types/media';

const { Title, Text } = Typography;
const { Option } = Select;
const { confirm } = Modal;

const DownloadTasksPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { colors } = useThemeContext();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [ruleFilter, setRuleFilter] = useState<string>('all');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 获取下载任务列表
  const { data: tasksData, isLoading, refetch } = useQuery({
    queryKey: ['download-tasks', statusFilter, ruleFilter],
    queryFn: () => mediaFilesApi.getTasks({
      status: statusFilter === 'all' ? undefined : statusFilter,
      monitor_rule: ruleFilter === 'all' ? undefined : ruleFilter,
      page_size: 100,
    }),
    refetchInterval: 3000, // 每3秒自动刷新
  });

  const tasks = tasksData?.tasks || [];

  // 获取监控规则列表（用于筛选）
  const { data: rulesData } = useQuery({
    queryKey: ['media-monitor-rules'],
    queryFn: () => mediaMonitorApi.getRules(),
  });

  const rules = rulesData?.rules || [];

  // 获取任务统计
  const { data: statsData } = useQuery({
    queryKey: ['download-tasks-stats'],
    queryFn: mediaFilesApi.getTaskStats,
    refetchInterval: 5000,
  });

  const stats = statsData?.stats || {
    total_count: 0,
    pending_count: 0,
    downloading_count: 0,
    success_count: 0,
    failed_count: 0,
  };

  // 重试任务
  const retryMutation = useMutation({
    mutationFn: (taskId: number) => mediaFilesApi.retryTask(taskId),
    onSuccess: () => {
      message.success('任务已重新加入队列');
      queryClient.invalidateQueries({ queryKey: ['download-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['download-tasks-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '重试失败');
    },
  });

  // 删除任务
  const deleteMutation = useMutation({
    mutationFn: (taskId: number) => mediaFilesApi.deleteTask(taskId),
    onSuccess: () => {
      message.success('任务已删除');
      queryClient.invalidateQueries({ queryKey: ['download-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['download-tasks-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 批量删除任务
  const batchDeleteMutation = useMutation({
    mutationFn: (taskIds: number[]) => mediaFilesApi.batchDeleteTasks(taskIds),
    onSuccess: (data) => {
      message.success(data.message || '批量删除成功');
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['download-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['download-tasks-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '批量删除失败');
    },
  });

  // 更新优先级
  const priorityMutation = useMutation({
    mutationFn: ({ taskId, priority }: { taskId: number; priority: number }) =>
      mediaFilesApi.updateTaskPriority(taskId, priority),
    onSuccess: () => {
      message.success('优先级已更新');
      queryClient.invalidateQueries({ queryKey: ['download-tasks'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '更新失败');
    },
  });

  // 处理删除
  const handleDelete = (task: DownloadTask) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除任务"${task.file_name}"吗？`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(task.id),
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的任务');
      return;
    }
    
    confirm({
      title: '确认批量删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除选中的 ${selectedRowKeys.length} 个任务吗？`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => batchDeleteMutation.mutate(selectedRowKeys as number[]),
    });
  };

  // 批量重试失败任务
  const handleRetryAllFailed = () => {
    const failedTasks = tasks.filter((t: DownloadTask) => t.status === 'failed');
    if (failedTasks.length === 0) {
      message.info('没有失败的任务需要重试');
      return;
    }

    confirm({
      title: '批量重试',
      icon: <ExclamationCircleOutlined />,
      content: `确定要重试全部 ${failedTasks.length} 个失败任务吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        for (const task of failedTasks) {
          await retryMutation.mutateAsync(task.id);
        }
        message.success(`已重试 ${failedTasks.length} 个任务`);
      },
    });
  };

  // 格式化文件大小
  const formatSize = (mb: number) => {
    if (!mb) return '-';
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  // 格式化速度
  const formatSpeed = (mbps: number) => {
    if (!mbps) return '-';
    return `${mbps.toFixed(2)} MB/s`;
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig: { [key: string]: { color: string; icon: any; text: string } } = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      downloading: { color: 'processing', icon: <SyncOutlined spin />, text: '下载中' },
      success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    return (
      <Tag icon={config.icon} color={config.color}>
        {config.text}
      </Tag>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 250,
      ellipsis: true,
      render: (text: string, record: DownloadTask) => (
        <div>
          <Tooltip title={text}>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>{text || '未知文件'}</div>
          </Tooltip>
          <Space size="small">
            <Tag>{record.file_type || 'unknown'}</Tag>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {formatSize(record.file_size_mb || 0)}
            </Text>
          </Space>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_: any, record: DownloadTask) => {
        if (record.status === 'downloading') {
          return (
            <div>
              <Progress 
                percent={record.progress_percent || 0} 
                size="small"
                status="active"
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatSpeed(record.download_speed_mbps || 0)}
              </Text>
            </div>
          );
        } else if (record.status === 'success') {
          return <Progress percent={100} size="small" status="success" />;
        } else if (record.status === 'failed') {
          return <Progress percent={record.progress_percent || 0} size="small" status="exception" />;
        }
        return <Progress percent={0} size="small" />;
      },
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 120,
      render: (priority: number, record: DownloadTask) => {
        if (record.status === 'success' || record.status === 'failed') {
          return <Text type="secondary">-</Text>;
        }
        return (
          <Space>
            <InputNumber
              size="small"
              min={1}
              max={10}
              value={priority || 5}
              style={{ width: 60 }}
              onChange={(value) => {
                if (value) {
                  priorityMutation.mutate({ taskId: record.id, priority: value });
                }
              }}
            />
            {priority >= 8 && <ArrowUpOutlined style={{ color: colors.error }} />}
            {priority <= 3 && <ArrowDownOutlined style={{ color: colors.textSecondary }} />}
          </Space>
        );
      },
    },
    {
      title: '重试次数',
      key: 'retry',
      width: 100,
      render: (_: any, record: DownloadTask) => (
        <Text type={record.retry_count && record.retry_count > 0 ? 'warning' : 'secondary'}>
          {record.retry_count || 0} / {record.max_retries || 3}
        </Text>
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'last_error',
      key: 'last_error',
      width: 200,
      ellipsis: true,
      render: (error: string) => {
        if (!error) return '-';
        return (
          <Tooltip title={error}>
            <Text type="danger" style={{ fontSize: 12 }}>
              {error}
            </Text>
          </Tooltip>
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (time: string) => {
        if (!time) return '-';
        return new Date(time).toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: DownloadTask) => (
        <Space size="small">
          {(record.status === 'failed' || record.status === 'success') && (
            <Tooltip title={record.status === 'failed' ? '重试失败任务' : '重新下载'}>
              <Button
                type="link"
                size="small"
                icon={<RedoOutlined />}
                onClick={() => retryMutation.mutate(record.id)}
                danger={record.status === 'failed'}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Button
              type="link"
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 计算成功率和失败率
  const totalCompleted = (stats.total_downloaded_ever || 0) + (stats.total_failed_ever || 0);
  const successRate = totalCompleted > 0 
    ? ((stats.total_downloaded_ever || 0) / totalCompleted * 100).toFixed(1) 
    : '0.0';
  const failedRate = totalCompleted > 0 
    ? ((stats.total_failed_ever || 0) / totalCompleted * 100).toFixed(1) 
    : '0.0';

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 - 左右分栏布局 */}
      <Card 
        title="📊 下载统计" 
        style={{ marginBottom: 24, background: colors.cardBg }}
        extra={
          <Button
            type="primary"
            danger
            icon={<RedoOutlined />}
            onClick={handleRetryAllFailed}
            disabled={(stats.failed_count || 0) === 0}
            size="small"
          >
            重试失败任务
          </Button>
        }
      >
        <Row gutter={16}>
          {/* 左侧：核心数据大卡片（淡雅蓝色渐变） - 一行四列 */}
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Card
              bordered={false}
              style={{
                background: 'linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%)',
                height: '100%',
                border: '1px solid #91d5ff',
              }}
              bodyStyle={{ padding: '16px 20px' }}
            >
              <Row gutter={16}>
                <Col span={6} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#0050b3', marginBottom: 4 }}>📈 累计下载</div>
                  <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1, color: '#003a8c' }}>
                    {stats.total_downloaded_ever || 0}
                  </div>
                  <div style={{ fontSize: 11, color: '#0050b3', marginTop: 4 }}>个文件</div>
                </Col>
                <Col span={6} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#0050b3', marginBottom: 4 }}>💾 累计大小</div>
                  <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1, color: '#003a8c' }}>
                    {stats.total_size_ever_mb ? (stats.total_size_ever_mb / 1024).toFixed(0) : 0}
                  </div>
                  <div style={{ fontSize: 11, color: '#0050b3', marginTop: 4 }}>GB</div>
                </Col>
                <Col span={6} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#0050b3', marginBottom: 4 }}>✅ 成功率</div>
                  <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1, color: '#003a8c' }}>
                    {successRate}
                  </div>
                  <div style={{ fontSize: 11, color: '#0050b3', marginTop: 4 }}>%</div>
                </Col>
                <Col span={6} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: '#0050b3', marginBottom: 4 }}>❌ 失败率</div>
                  <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1, color: '#003a8c' }}>
                    {failedRate}
                  </div>
                  <div style={{ fontSize: 11, color: '#0050b3', marginTop: 4 }}>%</div>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* 右侧：4个状态卡片（一行四列） */}
          <Col xs={24} sm={24} md={12} lg={12} xl={12}>
            <Row gutter={12}>
              <Col span={6}>
                <Card 
                  bordered={false}
                  style={{ 
                    background: colors.cardBg,
                    height: '100%',
                    textAlign: 'center',
                  }}
                  bodyStyle={{ padding: '16px 8px' }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: colors.warning, marginBottom: 4 }}>
                    {stats.pending_count || 0}
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>⏳ 等待中</Text>
                </Card>
              </Col>

              <Col span={6}>
                <Card 
                  bordered={false}
                  style={{ 
                    background: colors.cardBg,
                    height: '100%',
                    textAlign: 'center',
                  }}
                  bodyStyle={{ padding: '16px 8px' }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: colors.info, marginBottom: 4 }}>
                    {stats.downloading_count || 0}
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>🔄 下载中</Text>
                </Card>
              </Col>

              <Col span={6}>
                <Card 
                  bordered={false}
                  style={{ 
                    background: colors.cardBg,
                    height: '100%',
                    textAlign: 'center',
                  }}
                  bodyStyle={{ padding: '16px 8px' }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: colors.success, marginBottom: 4 }}>
                    {stats.success_count || 0}
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>✅ 已完成</Text>
                </Card>
              </Col>

              <Col span={6}>
                <Card 
                  bordered={false}
                  style={{ 
                    background: colors.cardBg,
                    height: '100%',
                    textAlign: 'center',
                  }}
                  bodyStyle={{ padding: '16px 8px' }}
                >
                  <div style={{ fontSize: 28, fontWeight: 700, color: colors.error, marginBottom: 4 }}>
                    {stats.failed_count || 0}
                  </div>
                  <Text type="secondary" style={{ fontSize: 11 }}>❌ 失败</Text>
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* 任务列表 */}
      <Card 
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>下载任务</Title>
            <Badge 
              count={stats.downloading} 
              overflowCount={99}
              style={{ backgroundColor: colors.info }}
            />
          </Space>
        }
        style={{ background: colors.cardBg }}
        extra={
          <Space>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 120 }}
              suffixIcon={<FilterOutlined />}
            >
              <Option value="all">全部状态</Option>
              <Option value="pending">等待中</Option>
              <Option value="downloading">下载中</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
            </Select>
            <Select
              value={ruleFilter}
              onChange={setRuleFilter}
              style={{ width: 200 }}
              placeholder="全部规则"
            >
              <Option value="all">全部规则</Option>
              {rules.map((rule: any) => (
                <Option key={rule.id} value={String(rule.id)}>
                  {rule.name}
                </Option>
              ))}
            </Select>
            {selectedRowKeys.length > 0 && (
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleBatchDelete}
              >
                批量删除 ({selectedRowKeys.length})
              </Button>
            )}
            <Tooltip title="刷新">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => refetch()}
              />
            </Tooltip>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={isLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            total: tasks.length,
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个任务`,
          }}
          locale={{
            emptyText: <TableEmpty description="暂无下载任务" />,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>
    </div>
  );
};

export default DownloadTasksPage;

