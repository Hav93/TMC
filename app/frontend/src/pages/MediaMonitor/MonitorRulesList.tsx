import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Switch, 
  message,
  Typography,
  Input,
  Tooltip,
  Modal,
  Progress,
  Statistic,
  Row,
  Col
} from 'antd';
import TableEmpty from '../../components/common/TableEmpty';
import { useThemeContext } from '../../theme';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ReloadOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileOutlined,
  CloudUploadOutlined,
  FolderOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import type { MediaMonitorRule } from '../../types/media';

const { Title } = Typography;
const { Search } = Input;
const { confirm } = Modal;

const MonitorRulesList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const { colors } = useThemeContext();

  // 获取监控规则列表
  const { data: rulesData, isLoading, refetch } = useQuery({
    queryKey: ['media-monitor-rules'],
    queryFn: () => mediaMonitorApi.getRules(),
  });

  const rules = rulesData?.rules || [];

  // 切换规则状态
  const toggleMutation = useMutation({
    mutationFn: (id: number) => mediaMonitorApi.toggleRule(id),
    onSuccess: () => {
      message.success('规则状态已更新');
      queryClient.invalidateQueries({ queryKey: ['media-monitor-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '状态更新失败');
    },
  });

  // 删除规则
  const deleteMutation = useMutation({
    mutationFn: (id: number) => mediaMonitorApi.deleteRule(id),
    onSuccess: () => {
      message.success('规则已删除');
      queryClient.invalidateQueries({ queryKey: ['media-monitor-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 处理删除
  const handleDelete = (record: MediaMonitorRule) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除监控规则"${record.name}"吗？这将同时删除相关的下载任务和文件记录（物理文件不会被删除）。`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(record.id),
    });
  };

  // 过滤规则
  const filteredRules = rules.filter((rule: MediaMonitorRule) =>
    rule.name.toLowerCase().includes(searchText.toLowerCase()) ||
    (rule.description && rule.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  // 获取媒体类型图标
  const getMediaTypeIcon = (types: string[]) => {
    if (!types || types.length === 0) return null;
    
    const iconMap: { [key: string]: any } = {
      photo: <FileImageOutlined style={{ color: '#52c41a' }} />,
      video: <VideoCameraOutlined style={{ color: '#1890ff' }} />,
      audio: <AudioOutlined style={{ color: '#722ed1' }} />,
      document: <FileOutlined style={{ color: '#fa8c16' }} />,
    };

    return types.map(type => (
      <Tooltip key={type} title={type}>
        {iconMap[type] || <FileOutlined />}
      </Tooltip>
    ));
  };

  // 格式化文件大小
  const formatSize = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  };

  // 表格列定义
  const columns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text: string, record: MediaMonitorRule) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: 4 }}>{text}</div>
          {record.description && (
            <div style={{ fontSize: 12, color: colors.textSecondary }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean, record: MediaMonitorRule) => (
        <Switch
          checked={active}
          onChange={() => toggleMutation.mutate(record.id)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '客户端',
      dataIndex: 'client_id',
      key: 'client_id',
      width: 120,
    },
    {
      title: '媒体类型',
      dataIndex: 'media_types',
      key: 'media_types',
      width: 120,
      render: (types: string) => {
        try {
          const typeArray = types ? JSON.parse(types) : [];
          return (
            <Space>
              {getMediaTypeIcon(typeArray)}
            </Space>
          );
        } catch {
          return '-';
        }
      },
    },
    {
      title: '文件大小范围',
      key: 'size_range',
      width: 150,
      render: (_: any, record: MediaMonitorRule) => {
        const min = record.min_size_mb || 0;
        const max = record.max_size_mb || 2000;
        return `${min} ~ ${max} MB`;
      },
    },
    {
      title: '归档设置',
      key: 'organize',
      width: 120,
      render: (_: any, record: MediaMonitorRule) => (
        <Space direction="vertical" size="small">
          {record.organize_enabled && (
            <Tag icon={<FolderOutlined />} color="blue">
              归档
            </Tag>
          )}
          {record.clouddrive_enabled && (
            <Tag icon={<CloudUploadOutlined />} color="cyan">
              云盘
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '下载统计',
      key: 'stats',
      width: 180,
      render: (_: any, record: MediaMonitorRule) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <div>
            <DownloadOutlined style={{ marginRight: 4, color: colors.primary }} />
            已下载: {record.total_downloaded || 0} 个
          </div>
          <div style={{ fontSize: 12, color: colors.textSecondary }}>
            累计: {formatSize(record.total_size_mb || 0)}
          </div>
          {record.failed_downloads > 0 && (
            <div style={{ fontSize: 12, color: colors.error }}>
              失败: {record.failed_downloads} 个
            </div>
          )}
        </Space>
      ),
    },
    {
      title: '最后下载',
      dataIndex: 'last_download_at',
      key: 'last_download_at',
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
      render: (_: any, record: MediaMonitorRule) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => navigate(`/media-monitor/${record.id}/edit`)}
            />
          </Tooltip>
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

  // 计算总统计
  const totalStats = {
    totalRules: rules.length,
    activeRules: rules.filter((r: MediaMonitorRule) => r.is_active).length,
    totalDownloaded: rules.reduce((sum: number, r: MediaMonitorRule) => sum + (r.total_downloaded || 0), 0),
    totalSize: rules.reduce((sum: number, r: MediaMonitorRule) => sum + (r.total_size_mb || 0), 0),
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card style={{ marginBottom: 24, background: colors.cardBg }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="监控规则"
              value={totalStats.totalRules}
              suffix="个"
              valueStyle={{ color: colors.primary }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="启用规则"
              value={totalStats.activeRules}
              suffix="个"
              valueStyle={{ color: colors.success }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="累计下载"
              value={totalStats.totalDownloaded}
              suffix="个文件"
              valueStyle={{ color: colors.info }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="总大小"
              value={formatSize(totalStats.totalSize)}
              valueStyle={{ color: colors.warning }}
            />
          </Col>
        </Row>
      </Card>

      <Card 
        title={<Title level={4} style={{ margin: 0 }}>媒体监控规则</Title>}
        style={{ background: colors.cardBg }}
        extra={
          <Space>
            <Search
              placeholder="搜索规则名称或描述"
              allowClear
              onSearch={setSearchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 250 }}
              prefix={<SearchOutlined />}
            />
            <Tooltip title="刷新">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => refetch()}
              />
            </Tooltip>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => navigate('/media-monitor/new')}
            >
              新建规则
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filteredRules}
          rowKey="id"
          loading={isLoading}
          pagination={{
            total: filteredRules.length,
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条规则`,
          }}
          locale={{
            emptyText: <TableEmpty description="暂无监控规则，点击"新建规则"开始创建" />,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>
    </div>
  );
};

export default MonitorRulesList;

