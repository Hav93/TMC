/**
 * 通知历史列表组件
 * 
 * 功能：
 * - 显示所有通知历史
 * - 筛选和搜索
 * - 查看详情
 */

import React, { useState } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Tag, 
  Input,
  Select,
  DatePicker,
  Drawer,
  Descriptions,
  Card
} from 'antd';
import { 
  ReloadOutlined,
  SearchOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { notificationService } from '../../services/notifications';
import type { NotificationLog, NotificationType, LogQueryParams } from '../../services/notifications';
import type { ColumnsType } from 'antd/es/table';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

const NotificationLogList: React.FC = () => {
  const [selectedLog, setSelectedLog] = useState<NotificationLog | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  
  // 筛选条件
  const [notificationType, setNotificationType] = useState<NotificationType | undefined>();
  const [status, setStatus] = useState<'pending' | 'sent' | 'failed' | undefined>();
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);

  // 构建查询参数
  const queryParams: LogQueryParams = {
    limit: 1000,
    ...(notificationType && { notification_type: notificationType }),
    ...(status && { status }),
    ...(dateRange && {
      start_date: dateRange[0].format('YYYY-MM-DD'),
      end_date: dateRange[1].format('YYYY-MM-DD'),
    }),
  };

  // 获取通知历史
  const { data: logs = [], isLoading, refetch } = useQuery({
    queryKey: ['notification-logs', queryParams],
    queryFn: () => notificationService.getLogs(queryParams),
  });

  // 通知类型显示名称
  const getNotificationTypeName = (type: NotificationType): string => {
    const names: Record<NotificationType, string> = {
      resource_captured: '资源捕获',
      save_115_success: '115转存成功',
      save_115_failed: '115转存失败',
      download_complete: '下载完成',
      download_failed: '下载失败',
      download_progress: '下载进度',
      forward_success: '转发成功',
      forward_failed: '转发失败',
      task_stale: '任务卡住',
      storage_warning: '存储警告',
      daily_report: '每日报告',
      system_error: '系统错误',
    };
    return names[type] || type;
  };

  // 状态标签
  const getStatusTag = (status: 'pending' | 'sent' | 'failed') => {
    const configs = {
      pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待发送' },
      sent: { color: 'success', icon: <CheckCircleOutlined />, text: '已发送' },
      failed: { color: 'error', icon: <CloseCircleOutlined />, text: '发送失败' },
    };
    const config = configs[status];
    return (
      <Tag icon={config.icon} color={config.color}>
        {config.text}
      </Tag>
    );
  };

  // 查看详情
  const handleViewDetails = (log: NotificationLog) => {
    setSelectedLog(log);
    setDrawerVisible(true);
  };

  // 表格列定义
  const columns: ColumnsType<NotificationLog> = [
    {
      title: '时间',
      dataIndex: 'sent_at',
      key: 'sent_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
      sorter: (a, b) => new Date(a.sent_at).getTime() - new Date(b.sent_at).getTime(),
      defaultSortOrder: 'descend',
    },
    {
      title: '通知类型',
      dataIndex: 'notification_type',
      key: 'notification_type',
      render: (type: NotificationType) => (
        <Tag color="blue">{getNotificationTypeName(type)}</Tag>
      ),
    },
    {
      title: '消息内容',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (text: string) => (
        <span style={{ fontSize: '13px' }}>
          {text.length > 100 ? `${text.substring(0, 100)}...` : text}
        </span>
      ),
    },
    {
      title: '通知渠道',
      dataIndex: 'channels',
      key: 'channels',
      width: 150,
      render: (channels: string) => {
        const channelList = channels.split(',').filter(c => c);
        return (
          <Space size="small">
            {channelList.map(channel => (
              <Tag key={channel} color={channel === 'telegram' ? 'blue' : channel === 'webhook' ? 'green' : 'orange'}>
                {channel}
              </Tag>
            ))}
          </Space>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: 'pending' | 'sent' | 'failed') => getStatusTag(status),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 100,
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetails(record)}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      {/* 筛选工具栏 */}
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Space wrap>
          <Select
            style={{ width: 180 }}
            placeholder="通知类型"
            allowClear
            value={notificationType}
            onChange={setNotificationType}
          >
            <Option value="resource_captured">资源捕获</Option>
            <Option value="save_115_success">115转存成功</Option>
            <Option value="save_115_failed">115转存失败</Option>
            <Option value="download_complete">下载完成</Option>
            <Option value="download_failed">下载失败</Option>
            <Option value="forward_success">转发成功</Option>
            <Option value="forward_failed">转发失败</Option>
            <Option value="system_error">系统错误</Option>
          </Select>

          <Select
            style={{ width: 120 }}
            placeholder="状态"
            allowClear
            value={status}
            onChange={setStatus}
          >
            <Option value="sent">已发送</Option>
            <Option value="failed">发送失败</Option>
            <Option value="pending">待发送</Option>
          </Select>

          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            format="YYYY-MM-DD"
          />

          <Button
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            刷新
          </Button>
        </Space>
      </Card>

      {/* 历史表格 */}
      <Table
        rowKey="id"
        columns={columns}
        dataSource={logs}
        loading={isLoading}
        pagination={{
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
      />

      {/* 详情抽屉 */}
      <Drawer
        title="通知详情"
        placement="right"
        width={600}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedLog && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="通知ID">
                {selectedLog.id}
              </Descriptions.Item>
              <Descriptions.Item label="通知类型">
                <Tag color="blue">{getNotificationTypeName(selectedLog.notification_type)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="发送时间">
                {new Date(selectedLog.sent_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
              <Descriptions.Item label="通知渠道">
                <Space>
                  {selectedLog.channels.split(',').filter(c => c).map(channel => (
                    <Tag key={channel} color={channel === 'telegram' ? 'blue' : channel === 'webhook' ? 'green' : 'orange'}>
                      {channel}
                    </Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {getStatusTag(selectedLog.status)}
              </Descriptions.Item>
              {selectedLog.error_message && (
                <Descriptions.Item label="错误信息">
                  <span style={{ color: '#ff4d4f' }}>{selectedLog.error_message}</span>
                </Descriptions.Item>
              )}
              {selectedLog.related_type && (
                <Descriptions.Item label="关联类型">
                  {selectedLog.related_type}
                </Descriptions.Item>
              )}
              {selectedLog.related_id && (
                <Descriptions.Item label="关联ID">
                  {selectedLog.related_id}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Card title="消息内容" size="small">
              <pre style={{ 
                whiteSpace: 'pre-wrap', 
                wordBreak: 'break-word',
                margin: 0,
                fontSize: '13px'
              }}>
                {selectedLog.message}
              </pre>
            </Card>
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default NotificationLogList;

