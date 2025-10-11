import React, { useState } from 'react';
import { 
  Card, 
  Table,
  Button, 
  Space, 
  Tag, 
  message,
  Typography,
  Input,
  Select,
  Tooltip,
  Modal,
  Statistic,
  Row,
  Col,
  DatePicker,
  Switch,
  Image,
  Descriptions,
  Divider
} from 'antd';
import TableEmpty from '../../components/common/TableEmpty';
import { useThemeContext } from '../../theme';
import { 
  ReloadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  StarOutlined,
  StarFilled,
  SearchOutlined,
  FilterOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  FileOutlined,
  CloudUploadOutlined,
  FolderOutlined,
  EyeOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mediaFilesApi } from '../../services/mediaFiles';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import type { MediaFile } from '../../types/media';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { confirm } = Modal;

const MediaLibraryPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { colors } = useThemeContext();
  
  // 视图模式
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  
  // 筛选条件
  const [keyword, setKeyword] = useState('');
  const [fileType, setFileType] = useState('all');
  const [ruleFilter, setRuleFilter] = useState('all');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [organizedFilter, setOrganizedFilter] = useState('all');
  const [cloudFilter, setCloudFilter] = useState('all');
  const [starredOnly, setStarredOnly] = useState(false);
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  
  // 详情对话框
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);

  // 获取媒体文件列表
  const { data: filesData, isLoading, refetch } = useQuery({
    queryKey: ['media-files', keyword, fileType, ruleFilter, organizedFilter, cloudFilter, starredOnly, dateRange],
    queryFn: () => mediaFilesApi.getFiles({
      keyword: keyword || undefined,
      file_type: fileType === 'all' ? undefined : fileType,
      monitor_rule: ruleFilter === 'all' ? undefined : ruleFilter,
      organized: organizedFilter === 'all' ? undefined : organizedFilter,
      cloud_status: cloudFilter === 'all' ? undefined : cloudFilter,
      starred: starredOnly || undefined,
      start_date: dateRange?.[0]?.format('YYYY-MM-DD'),
      end_date: dateRange?.[1]?.format('YYYY-MM-DD'),
      page_size: 100,
    }),
  });

  const files = filesData?.files || [];

  // 获取监控规则列表
  const { data: rulesData } = useQuery({
    queryKey: ['media-monitor-rules'],
    queryFn: () => mediaMonitorApi.getRules(),
  });

  const rules = rulesData?.rules || [];

  // 获取文件统计
  const { data: statsData } = useQuery({
    queryKey: ['media-files-stats'],
    queryFn: mediaFilesApi.getFileStats,
    refetchInterval: 10000,
  });

  const stats = statsData || {
    total: 0,
    by_type: {},
    total_size_mb: 0,
    starred: 0,
  };

  // 收藏/取消收藏
  const starMutation = useMutation({
    mutationFn: (fileId: number) => mediaFilesApi.toggleStar(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['media-files'] });
      queryClient.invalidateQueries({ queryKey: ['media-files-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '操作失败');
    },
  });

  // 删除文件
  const deleteMutation = useMutation({
    mutationFn: (fileId: number) => mediaFilesApi.deleteFile(fileId),
    onSuccess: () => {
      message.success('文件已删除');
      queryClient.invalidateQueries({ queryKey: ['media-files'] });
      queryClient.invalidateQueries({ queryKey: ['media-files-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '删除失败');
    },
  });

  // 批量删除文件
  const batchDeleteMutation = useMutation({
    mutationFn: (fileIds: number[]) => mediaFilesApi.batchDeleteFiles(fileIds),
    onSuccess: (data) => {
      message.success(data.message || '批量删除成功');
      setSelectedRowKeys([]);
      queryClient.invalidateQueries({ queryKey: ['media-files'] });
      queryClient.invalidateQueries({ queryKey: ['media-files-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '批量删除失败');
    },
  });

  // 下载文件
  const handleDownload = async (file: MediaFile) => {
    try {
      const response = await mediaFilesApi.downloadFile(file.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.file_name || 'download');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success('开始下载');
    } catch (error: any) {
      message.error(error.response?.data?.message || '下载失败');
    }
  };

  // 删除确认
  const handleDelete = (file: MediaFile) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除文件"${file.file_name}"吗？这将删除物理文件和数据库记录。`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteMutation.mutate(file.id),
    });
  };

  // 查看详情
  const handleViewDetail = (file: MediaFile) => {
    setSelectedFile(file);
    setDetailVisible(true);
  };

  // 重新整理文件
  const reorganizeMutation = useMutation({
    mutationFn: (fileId: number) => mediaFilesApi.reorganizeFile(fileId),
    onSuccess: () => {
      message.success('文件重新整理成功');
      refetch();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '重新整理失败');
    },
  });

  const handleReorganize = (file: MediaFile) => {
    confirm({
      title: '重新整理文件',
      icon: <ReloadOutlined />,
      content: `确定要重新整理文件"${file.file_name}"吗？将尝试重新上传到115网盘。`,
      okText: '确认',
      cancelText: '取消',
      onOk: () => reorganizeMutation.mutate(file.id),
    });
  };

  // 批量删除
  const handleBatchDelete = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的文件');
      return;
    }
    
    confirm({
      title: '确认批量删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除选中的 ${selectedRowKeys.length} 个文件吗？这将删除物理文件和数据库记录。`,
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => batchDeleteMutation.mutate(selectedRowKeys as number[]),
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

  // 获取发送者显示名称（按优先级：username > 姓名 > ID）
  const getSenderDisplayName = (record: MediaFile) => {
    // 如果sender_username不是纯数字，则认为是username或姓名
    if (record.sender_username && !/^\d+$/.test(record.sender_username)) {
      // 直接返回，不添加@前缀（因为后端已经存储了完整的显示名称）
      return record.sender_username;
    }
    // 否则显示ID
    return record.sender_id || 'Unknown';
  };

  // 获取来源显示名称（如果是纯数字则认为是ID，否则是名称）
  const getSourceDisplayName = (record: MediaFile) => {
    if (!record.source_chat) return 'Unknown';
    // 如果source_chat不是纯数字，则认为是名称
    if (!/^\d+$/.test(record.source_chat)) {
      return record.source_chat;
    }
    // 否则显示ID
    return record.source_chat;
  };

  // 获取文件类型图标
  const getFileTypeIcon = (type: string) => {
    const iconMap: { [key: string]: { icon: any; color: string } } = {
      image: { icon: <FileImageOutlined />, color: '#52c41a' },
      video: { icon: <VideoCameraOutlined />, color: '#1890ff' },
      audio: { icon: <AudioOutlined />, color: '#722ed1' },
      document: { icon: <FileOutlined />, color: '#fa8c16' },
    };

    const config = iconMap[type] || iconMap.document;
    return <span style={{ color: config.color, fontSize: 18 }}>{config.icon}</span>;
  };

  // 表格列定义
  const columns = [
    {
      title: '文件',
      key: 'file',
      width: 300,
      render: (_: any, record: MediaFile) => (
        <Space>
          {getFileTypeIcon(record.file_type || 'document')}
          <div>
            <div style={{ fontWeight: 500, marginBottom: 4 }}>
              {record.file_name}
              {record.is_starred && (
                <StarFilled style={{ color: '#faad14', marginLeft: 8 }} />
              )}
            </div>
            <Space size="small">
              <Tag>{record.file_type}</Tag>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatSize(record.file_size_mb || 0)}
              </Text>
              {record.extension && (
                <Tag color="default">{record.extension}</Tag>
              )}
            </Space>
          </div>
        </Space>
      ),
    },
    {
      title: '元数据',
      key: 'metadata',
      width: 200,
      render: (_: any, record: MediaFile) => {
        const items = [];
        if (record.resolution) items.push(`${record.resolution}`);
        if (record.duration_seconds) {
          const minutes = Math.floor(record.duration_seconds / 60);
          const seconds = record.duration_seconds % 60;
          items.push(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        }
        if (record.codec) items.push(record.codec);
        
        return items.length > 0 ? (
          <Space direction="vertical" size={0}>
            {items.map((item, index) => (
              <Text key={index} type="secondary" style={{ fontSize: 12 }}>
                {item}
              </Text>
            ))}
          </Space>
        ) : '-';
      },
    },
    {
      title: '来源',
      key: 'source',
      width: 150,
      render: (_: any, record: MediaFile) => {
        const senderName = getSenderDisplayName(record);
        const sourceName = getSourceDisplayName(record);
        return (
          <div>
            {senderName && (
              <div style={{ fontSize: 12 }}>
                @{senderName}
              </div>
            )}
            {sourceName && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {sourceName}
              </Text>
            )}
          </div>
        );
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 150,
      render: (_: any, record: MediaFile) => {
        // 调试信息
        console.log('状态渲染:', {
          file_name: record.file_name,
          is_organized: record.is_organized,
          is_uploaded_to_cloud: record.is_uploaded_to_cloud,
          organize_failed: record.organize_failed,
          organize_error: record.organize_error
        });
        
        return (
          <Space direction="vertical" size="small">
            {record.is_organized && (
              <Tag icon={<FolderOutlined />} color="blue">
                已归档
              </Tag>
            )}
            {record.is_uploaded_to_cloud && (
              <Tag icon={<CloudUploadOutlined />} color="cyan">
                云端
              </Tag>
            )}
            {!record.is_organized && !record.is_uploaded_to_cloud && record.organize_failed && (
              <Tooltip title={record.organize_error || '归档失败'}>
                <Tag icon={<ExclamationCircleOutlined />} color="warning">
                  未归档
                </Tag>
              </Tooltip>
            )}
            {!record.is_organized && !record.is_uploaded_to_cloud && !record.organize_failed && (
              <Tag color="default">待整理</Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '下载时间',
      dataIndex: 'downloaded_at',
      key: 'downloaded_at',
      width: 150,
      render: (time: string) => {
        if (!time) return '-';
        return new Date(time).toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: 'right' as const,
      render: (_: any, record: MediaFile) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {record.organize_failed && (
            <Tooltip title="重新整理">
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => handleReorganize(record)}
                style={{ color: colors.primary }}
              />
            </Tooltip>
          )}
          <Tooltip title={record.is_starred ? '取消收藏' : '收藏'}>
            <Button
              type="link"
              size="small"
              icon={record.is_starred ? <StarFilled /> : <StarOutlined />}
              style={{ color: record.is_starred ? '#faad14' : undefined }}
              onClick={() => starMutation.mutate(record.id)}
            />
          </Tooltip>
          <Tooltip title="下载">
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
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

  return (
    <div style={{ padding: '24px' }}>
      {/* 统计卡片 */}
      <Card style={{ marginBottom: 24, background: colors.cardBg }}>
        <Row gutter={16}>
          <Col span={4}>
            <Statistic
              title="全部文件"
              value={stats.total}
              prefix={<FileOutlined />}
              valueStyle={{ color: colors.primary }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="图片"
              value={stats.by_type?.image || 0}
              prefix={<FileImageOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="视频"
              value={stats.by_type?.video || 0}
              prefix={<VideoCameraOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="音频"
              value={stats.by_type?.audio || 0}
              prefix={<AudioOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="收藏"
              value={stats.starred}
              prefix={<StarFilled />}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={4}>
            <Statistic
              title="总大小"
              value={formatSize(stats.total_size_mb || 0)}
              valueStyle={{ color: colors.warning }}
            />
          </Col>
        </Row>
      </Card>

      {/* 文件列表 */}
      <Card 
        title={<Title level={4} style={{ margin: 0 }}>媒体文件库</Title>}
        style={{ background: colors.cardBg }}
        extra={
          <Space wrap>
            <Search
              placeholder="搜索文件名"
              allowClear
              onSearch={setKeyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
            />
            <Select
              value={fileType}
              onChange={setFileType}
              style={{ width: 120 }}
            >
              <Option value="all">全部类型</Option>
              <Option value="image">图片</Option>
              <Option value="video">视频</Option>
              <Option value="audio">音频</Option>
              <Option value="document">文档</Option>
            </Select>
            <Select
              value={ruleFilter}
              onChange={setRuleFilter}
              style={{ width: 150 }}
            >
              <Option value="all">全部规则</Option>
              {rules.map((rule: any) => (
                <Option key={rule.id} value={String(rule.id)}>
                  {rule.name}
                </Option>
              ))}
            </Select>
            <Select
              value={organizedFilter}
              onChange={setOrganizedFilter}
              style={{ width: 120 }}
            >
              <Option value="all">全部状态</Option>
              <Option value="organized">已归档</Option>
              <Option value="pending">未归档</Option>
            </Select>
            <Select
              value={cloudFilter}
              onChange={setCloudFilter}
              style={{ width: 120 }}
            >
              <Option value="all">全部</Option>
              <Option value="uploaded">已上传云端</Option>
              <Option value="local">本地</Option>
            </Select>
            <Switch
              checked={starredOnly}
              onChange={setStarredOnly}
              checkedChildren={<StarFilled />}
              unCheckedChildren={<StarOutlined />}
            />
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              format="YYYY-MM-DD"
              placeholder={['开始日期', '结束日期']}
            />
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
            {/* 视图切换暂时隐藏 */}
            {/* <Button.Group>
              <Button
                type={viewMode === 'grid' ? 'primary' : 'default'}
                icon={<AppstoreOutlined />}
                onClick={() => setViewMode('grid')}
              />
              <Button
                type={viewMode === 'list' ? 'primary' : 'default'}
                icon={<UnorderedListOutlined />}
                onClick={() => setViewMode('list')}
              />
            </Button.Group> */}
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={files}
          rowKey="id"
          loading={isLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            total: files.length,
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个文件`,
          }}
          locale={{
            emptyText: <TableEmpty description="暂无媒体文件" />,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 文件详情对话框 */}
      <Modal
        title="文件详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="download" 
            type="primary" 
            icon={<DownloadOutlined />}
            onClick={() => {
              if (selectedFile) {
                handleDownload(selectedFile);
              }
            }}
          >
            下载
          </Button>,
        ]}
        width={800}
      >
        {selectedFile && (
          <>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="文件名" span={2}>
                {selectedFile.file_name}
              </Descriptions.Item>
              <Descriptions.Item label="文件类型">
                {selectedFile.file_type}
              </Descriptions.Item>
              <Descriptions.Item label="文件大小">
                {formatSize(selectedFile.file_size_mb || 0)}
              </Descriptions.Item>
              <Descriptions.Item label="扩展名">
                {selectedFile.extension || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="文件哈希">
                <Text code style={{ fontSize: 12 }}>
                  {selectedFile.file_hash?.substring(0, 16)}...
                </Text>
              </Descriptions.Item>
              {selectedFile.resolution && (
                <Descriptions.Item label="分辨率">
                  {selectedFile.resolution}
                </Descriptions.Item>
              )}
              {selectedFile.duration_seconds && (
                <Descriptions.Item label="时长">
                  {Math.floor(selectedFile.duration_seconds / 60)}:
                  {(selectedFile.duration_seconds % 60).toString().padStart(2, '0')}
                </Descriptions.Item>
              )}
              {selectedFile.codec && (
                <Descriptions.Item label="编码">
                  {selectedFile.codec}
                </Descriptions.Item>
              )}
              {selectedFile.bitrate_kbps && (
                <Descriptions.Item label="比特率">
                  {selectedFile.bitrate_kbps} kbps
                </Descriptions.Item>
              )}
              <Descriptions.Item label="发送者">
                {selectedFile ? getSenderDisplayName(selectedFile) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="来源频道">
                {selectedFile ? getSourceDisplayName(selectedFile) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="下载时间" span={2}>
                {selectedFile.downloaded_at 
                  ? new Date(selectedFile.downloaded_at).toLocaleString('zh-CN')
                  : '-'}
              </Descriptions.Item>
              {selectedFile.is_organized && (
                <>
                  <Descriptions.Item label="归档时间" span={2}>
                    {selectedFile.organized_at 
                      ? new Date(selectedFile.organized_at).toLocaleString('zh-CN')
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="归档路径" span={2}>
                    <Text code style={{ fontSize: 12 }}>
                      {selectedFile.final_path || '-'}
                    </Text>
                  </Descriptions.Item>
                </>
              )}
              {selectedFile.is_uploaded_to_cloud && (
                <>
                  <Descriptions.Item label="云端上传时间" span={2}>
                    {selectedFile.uploaded_at 
                      ? new Date(selectedFile.uploaded_at).toLocaleString('zh-CN')
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="云端路径" span={2}>
                    <Text code style={{ fontSize: 12 }}>
                      {selectedFile.clouddrive_path || '-'}
                    </Text>
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>
          </>
        )}
      </Modal>
    </div>
  );
};

export default MediaLibraryPage;

