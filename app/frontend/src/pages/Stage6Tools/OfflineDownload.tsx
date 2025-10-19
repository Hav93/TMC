/**
 * 115网盘离线下载管理页面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  message,
  Modal,
  Progress,
  Tag,
  Popconfirm,
  Tooltip,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  DownloadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  ClearOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  addOfflineTask,
  getOfflineTasks,
  deleteOfflineTasks,
  clearOfflineTasks,
} from '../../services/offline';
import type {
  OfflineTask,
  OfflineTaskStats,
} from '../../types/offline';
import { OfflineTaskStatus } from '../../types/offline';

const { TextArea } = Input;

/**
 * 格式化文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * 格式化时间
 */
function formatTime(timestamp: number): string {
  if (!timestamp) return '-';
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('zh-CN');
}

/**
 * 获取状态标签
 */
function getStatusTag(status: OfflineTaskStatus, statusText: string) {
  const statusConfig = {
    [OfflineTaskStatus.WAITING]: { color: 'default', icon: <ClockCircleOutlined /> },
    [OfflineTaskStatus.DOWNLOADING]: { color: 'processing', icon: <LoadingOutlined /> },
    [OfflineTaskStatus.COMPLETED]: { color: 'success', icon: <CheckCircleOutlined /> },
    [OfflineTaskStatus.FAILED]: { color: 'error', icon: <ExclamationCircleOutlined /> },
    [OfflineTaskStatus.DELETED]: { color: 'default', icon: null },
  };

  const config = statusConfig[status] || { color: 'default', icon: null };

  return (
    <Tag color={config.color} icon={config.icon}>
      {statusText}
    </Tag>
  );
}

/**
 * 离线下载管理组件
 */
export const OfflineDownload: React.FC = () => {
  const [tasks, setTasks] = useState<OfflineTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [newTaskUrl, setNewTaskUrl] = useState('');
  const [stats, setStats] = useState<OfflineTaskStats>({
    total: 0,
    waiting: 0,
    downloading: 0,
    completed: 0,
    failed: 0,
  });

  /**
   * 加载离线任务列表
   */
  const loadTasks = async () => {
    setLoading(true);
    try {
      const response = await getOfflineTasks(1);
      if (response.success) {
        setTasks(response.tasks);
        calculateStats(response.tasks);
      } else {
        message.error(response.message || '获取离线任务列表失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '获取离线任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 计算统计信息
   */
  const calculateStats = (taskList: OfflineTask[]) => {
    const newStats: OfflineTaskStats = {
      total: taskList.length,
      waiting: 0,
      downloading: 0,
      completed: 0,
      failed: 0,
    };

    taskList.forEach((task) => {
      switch (task.status) {
        case OfflineTaskStatus.WAITING:
          newStats.waiting++;
          break;
        case OfflineTaskStatus.DOWNLOADING:
          newStats.downloading++;
          break;
        case OfflineTaskStatus.COMPLETED:
          newStats.completed++;
          break;
        case OfflineTaskStatus.FAILED:
          newStats.failed++;
          break;
      }
    });

    setStats(newStats);
  };

  /**
   * 添加离线任务
   */
  const handleAddTask = async () => {
    if (!newTaskUrl.trim()) {
      message.warning('请输入下载链接');
      return;
    }

    setLoading(true);
    try {
      const response = await addOfflineTask({
        url: newTaskUrl.trim(),
        target_dir_id: '0',
      });

      if (response.success) {
        message.success('离线任务添加成功');
        setAddModalVisible(false);
        setNewTaskUrl('');
        loadTasks(); // 刷新列表
      } else {
        message.error(response.message || '添加离线任务失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '添加离线任务失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 删除选中的任务
   */
  const handleDeleteSelected = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的任务');
      return;
    }

    setLoading(true);
    try {
      const response = await deleteOfflineTasks({
        task_ids: selectedRowKeys as string[],
      });

      if (response.success) {
        message.success(response.message || `成功删除 ${selectedRowKeys.length} 个任务`);
        setSelectedRowKeys([]);
        loadTasks(); // 刷新列表
      } else {
        message.error(response.message || '删除任务失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '删除任务失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 清空已完成的任务
   */
  const handleClearCompleted = async () => {
    setLoading(true);
    try {
      const response = await clearOfflineTasks({ flag: 1 });

      if (response.success) {
        message.success(response.message || '已清空已完成的任务');
        loadTasks(); // 刷新列表
      } else {
        message.error(response.message || '清空任务失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '清空任务失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 清空失败的任务
   */
  const handleClearFailed = async () => {
    setLoading(true);
    try {
      const response = await clearOfflineTasks({ flag: 2 });

      if (response.success) {
        message.success(response.message || '已清空失败的任务');
        loadTasks(); // 刷新列表
      } else {
        message.error(response.message || '清空任务失败');
      }
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '清空任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载任务列表
  useEffect(() => {
    loadTasks();

    // 设置自动刷新（每30秒）
    const interval = setInterval(() => {
      loadTasks();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  // 表格列定义
  const columns: ColumnsType<OfflineTask> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: {
        showTitle: false,
      },
      render: (name: string) => (
        <Tooltip title={name}>
          <span>{name}</span>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: OfflineTaskStatus, record: OfflineTask) =>
        getStatusTag(status, record.status_text),
    },
    {
      title: '进度',
      dataIndex: 'percentDone',
      key: 'percentDone',
      width: 200,
      render: (percentDone: number, record: OfflineTask) => {
        const isDownloading = record.status === OfflineTaskStatus.DOWNLOADING;
        return (
          <Progress
            percent={percentDone}
            size="small"
            status={
              record.status === OfflineTaskStatus.COMPLETED
                ? 'success'
                : record.status === OfflineTaskStatus.FAILED
                ? 'exception'
                : isDownloading
                ? 'active'
                : 'normal'
            }
          />
        );
      },
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '添加时间',
      dataIndex: 'add_time',
      key: 'add_time',
      width: 180,
      render: (addTime: number) => formatTime(addTime),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record: OfflineTask) => (
        <Popconfirm
          title="确定删除这个任务吗？"
          onConfirm={async () => {
            setLoading(true);
            try {
              const response = await deleteOfflineTasks({
                task_ids: [record.task_id],
              });
              if (response.success) {
                message.success('任务已删除');
                loadTasks();
              } else {
                message.error(response.message || '删除失败');
              }
            } catch (error: any) {
              message.error(error?.response?.data?.detail || '删除失败');
            } finally {
              setLoading(false);
            }
          }}
        >
          <Button type="link" danger size="small" icon={<DeleteOutlined />}>
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总任务数"
              value={stats.total}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="下载中"
              value={stats.downloading}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LoadingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={stats.completed}
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败"
              value={stats.failed}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作栏 */}
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddModalVisible(true)}
          >
            添加任务
          </Button>
          <Button icon={<ReloadOutlined />} onClick={loadTasks} loading={loading}>
            刷新
          </Button>
          <Popconfirm
            title="确定删除选中的任务吗？"
            onConfirm={handleDeleteSelected}
            disabled={selectedRowKeys.length === 0}
          >
            <Button
              danger
              icon={<DeleteOutlined />}
              disabled={selectedRowKeys.length === 0}
            >
              删除选中
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定清空所有已完成的任务吗？"
            onConfirm={handleClearCompleted}
            disabled={stats.completed === 0}
          >
            <Button
              icon={<ClearOutlined />}
              disabled={stats.completed === 0}
            >
              清空已完成
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定清空所有失败的任务吗？"
            onConfirm={handleClearFailed}
            disabled={stats.failed === 0}
          >
            <Button
              icon={<ClearOutlined />}
              disabled={stats.failed === 0}
            >
              清空失败
            </Button>
          </Popconfirm>
        </Space>

        {/* 任务列表 */}
        <Table
          rowSelection={{
            selectedRowKeys,
            onChange: (newSelectedRowKeys) => {
              setSelectedRowKeys(newSelectedRowKeys);
            },
          }}
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `共 ${total} 个任务`,
          }}
        />
      </Card>

      {/* 添加任务对话框 */}
      <Modal
        title="添加离线下载任务"
        open={addModalVisible}
        onOk={handleAddTask}
        onCancel={() => {
          setAddModalVisible(false);
          setNewTaskUrl('');
        }}
        confirmLoading={loading}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <div style={{ marginBottom: 8, fontWeight: 500 }}>下载链接</div>
            <TextArea
              placeholder="支持 HTTP/HTTPS 直链、磁力链接 (magnet:) 或 BT 种子 URL"
              value={newTaskUrl}
              onChange={(e) => setNewTaskUrl(e.target.value)}
              rows={4}
            />
          </div>
          <div style={{ color: '#666', fontSize: '12px' }}>
            <div>支持的链接类型：</div>
            <div>• HTTP/HTTPS 直链</div>
            <div>• 磁力链接 (magnet:?xt=urn:btih:...)</div>
            <div>• BT 种子文件 URL</div>
          </div>
        </Space>
      </Modal>
    </div>
  );
};

export default OfflineDownload;

