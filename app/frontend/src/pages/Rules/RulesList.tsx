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
  Upload,
  Modal
} from 'antd';
import TableEmpty from '../../components/common/TableEmpty';
import { useThemeContext } from '../../theme';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ExportOutlined,
  ImportOutlined,
  ReloadOutlined,
  FilterOutlined,
  SwapOutlined,
  MessageOutlined,
  FileImageOutlined,
  VideoCameraOutlined,
  FileOutlined,
  AudioOutlined,
  SoundOutlined,
  SmileOutlined,
  GifOutlined,
  LinkOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { rulesApi } from '../../services/rules';
import { chatsApi } from '../../services/chats';
import type { ForwardRule } from '../../types/rule';
// z-index问题已在 styles/components/modal.css 中解决

const { Title } = Typography;
const { Search } = Input;

const RulesList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchText, setSearchText] = useState('');
  const { colors } = useThemeContext();

  // 获取规则列表
  const { data: rules = [], isLoading, refetch } = useQuery({
    queryKey: ['rules'],
    queryFn: rulesApi.list,
  });

  // 获取聊天列表
  const { data: chatsData } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats
  });

  const chats = chatsData?.chats || [];

  // 根据chat_id获取聊天显示名称（优先first_name）
  const getChatDisplayName = (chatId: string) => {
    const chat = chats.find(chat => String(chat.id) === String(chatId));
    
    if (chat) {
      return chat.title || chat.id;
    }
    return `聊天 ${chatId}`;
  };

  // 自动更新聊天名称
  const fetchChatInfoMutation = useMutation({
    mutationFn: rulesApi.fetchChatInfo,
    onSuccess: (response: { success: boolean; message?: string }) => {
      if (response.success) {
        message.success('聊天名称已自动更新');
        queryClient.invalidateQueries({ queryKey: ['rules'] });
      }
    },
    onError: () => {
      // 不显示错误消息，避免打扰用户
    },
  });

  // 监听规则数据变化并自动更新占位符名称
  React.useEffect(() => {
    if (rules && rules.length > 0) {
      // 检查是否有占位符格式的聊天名称或空名称
      const hasPlaceholderNames = rules.some(rule => 
        (!rule.source_chat_name || rule.source_chat_name.trim() === '' || rule.source_chat_name.startsWith('聊天 ')) ||
        (!rule.target_chat_name || rule.target_chat_name.trim() === '' || rule.target_chat_name.startsWith('聊天 '))
      );

      // 如果发现占位符名称，自动调用更新API
      if (hasPlaceholderNames && !fetchChatInfoMutation.isPending) {
        fetchChatInfoMutation.mutate();
      }
    }
  }, [rules, fetchChatInfoMutation]);

  // 删除规则
  const deleteMutation = useMutation({
    mutationFn: rulesApi.delete,
    onSuccess: () => {
      message.success('规则删除成功');
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
    onError: () => {
      message.error('规则删除失败');
    },
  });

  // 切换规则状态 - 优化版（简单乐观更新）
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      rulesApi.toggle(id, enabled),
    onMutate: async ({ id, enabled }) => {
      // 取消正在进行的查询，防止覆盖乐观更新
      await queryClient.cancelQueries({ queryKey: ['rules'] });
      
      // 获取当前数据快照
      const previousRules = queryClient.getQueryData<ForwardRule[]>(['rules']);
      
      // 乐观更新：立即修改UI状态
      if (previousRules) {
        const updatedRules = previousRules.map(rule => 
          rule.id === id ? { ...rule, is_active: enabled, updated_at: new Date().toISOString() } : rule
        );
        queryClient.setQueryData(['rules'], updatedRules);
      }
      
      return { previousRules };
    },
    onSuccess: () => {
      message.success('规则状态更新成功');
      // 刷新规则列表以获取最新数据
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
    onError: (error: any) => {
      message.error(error?.message || '规则状态更新失败');
      // 刷新规则列表以恢复正确状态
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
  });

  // 导出规则
  const exportMutation = useMutation({
    mutationFn: rulesApi.export,
    onSuccess: (response: { success: boolean; data?: unknown; filename?: string; message?: string }) => {
      if (response.success) {
        // 创建下载链接
        const content = JSON.stringify(response.data, null, 2);
        const blob = new Blob([content], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = response.filename || `rules_export_${new Date().getTime()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        message.success('规则导出成功');
      } else {
        message.error('规则导出失败');
      }
    },
    onError: () => {
      message.error('规则导出失败');
    },
  });

  // 导入规则
  const importMutation = useMutation({
    mutationFn: rulesApi.import,
    onSuccess: (response: { success: boolean; message?: string; imported_count?: number; failed_count?: number; errors?: string[] }) => {
      if (response.success) {
        message.success({
          content: response.message,
          duration: 5,
        });
        queryClient.invalidateQueries({ queryKey: ['rules'] });
        
        // 如果有失败的记录，显示详细信息
        if (response.failed_count && response.failed_count > 0 && response.errors?.length) {
          const errorDetails = `成功导入: ${response.imported_count} 个\n失败: ${response.failed_count} 个\n\n失败详情:\n${response.errors.join('\n')}`;
          Modal.warning({
            title: '部分规则导入失败',
            content: errorDetails,
            okText: '我知道了',
          });
        }
      } else {
        message.error(`导入失败: ${response.message}`);
      }
    },
    onError: (error: Error) => {
      message.error(`导入失败: ${error.message || '网络错误'}`);
    },
  });

  // 处理删除
  const handleDelete = (rule: ForwardRule) => {
    console.log('🔴 handleDelete called', rule);
    Modal.confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: `确定要删除规则"${rule.name}"吗？此操作不可恢复。`,
      okText: '删除',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        console.log('🔴 onOk called, deleting rule id:', rule.id);
        deleteMutation.mutate(rule.id);
      },
    });
  };

  // 处理状态切换 - 简化版（参考v3.1）
  const handleToggle = (rule: ForwardRule, enabled: boolean) => {
    // 防止重复点击
    if (toggleMutation.isPending) {
      console.log('⚠️ 规则切换进行中，跳过重复操作');
      return;
    }
    
    console.log('🔄 开始切换规则状态:', { ruleId: rule.id, enabled });
    toggleMutation.mutate({ id: rule.id, enabled });
  };

  // 切换功能特性
  const toggleFeatureMutation = useMutation({
    mutationFn: ({ id, feature, enabled }: { id: number; feature: string; enabled: boolean }) =>
      rulesApi.toggleFeature(id, feature, enabled),
    onSuccess: (_, variables) => {
      console.log('🔄 功能切换成功:', variables);
      message.success(`${getFeatureName(variables.feature)}${variables.enabled ? '已启用' : '已禁用'}`);
      // 立即刷新数据，避免延迟导致的显示问题
      queryClient.invalidateQueries({ queryKey: ['rules'] });
    },
    onError: (error, variables) => {
      console.error('❌ 功能切换失败:', error, variables);
      message.error(`${getFeatureName(variables.feature)}设置失败`);
    },
  });

  // 获取功能名称
  const getFeatureName = (feature: string) => {
    const names: Record<string, string> = {
      'enable_keyword_filter': '关键词过滤',
      'enable_regex_replace': '正则替换',
      'enable_link_preview': '链接预览',
      'enable_text': '文本消息',
      'enable_photo': '图片消息',
      'enable_video': '视频消息',
      'enable_document': '文档消息',
      'enable_audio': '音频消息',
      'enable_voice': '语音消息',
      'enable_sticker': '贴纸消息',
      'enable_animation': '动画消息',
      'enable_webpage': '网页消息',
    };
    return names[feature] || feature;
  };

  // 渲染时间过滤规则卡片
  const renderTimeFilter = (record: ForwardRule) => {
    if (!record.time_filter_type || record.time_filter_type === 'all_messages') {
      return (
        <Tag color="default" icon={<ClockCircleOutlined />} style={{ color: colors.textSecondary }}>
          无限制
        </Tag>
      );
    }

    const getTimeFilterInfo = () => {
      switch (record.time_filter_type) {
        case 'today_only':
          return { text: '仅今日', color: 'blue', icon: <CalendarOutlined /> };
        case 'time_range':
          const startTime = record.start_time ? record.start_time.substring(0, 5) : '00:00';
          const endTime = record.end_time ? record.end_time.substring(0, 5) : '23:59';
          return { 
            text: `${startTime}-${endTime}`, 
            color: 'green', 
            icon: <ClockCircleOutlined /> 
          };
        case 'from_time':
          const fromTime = record.start_time ? record.start_time.substring(0, 5) : '00:00';
          return { 
            text: `${fromTime}起`, 
            color: 'orange', 
            icon: <ClockCircleOutlined /> 
          };
        case 'after_start':
          return { text: '启动后', color: 'purple', icon: <CalendarOutlined /> };
        default:
          return { text: record.time_filter_type, color: 'default', icon: <ClockCircleOutlined /> };
      }
    };

    const filterInfo = getTimeFilterInfo();
    
    return (
      <Tag color={filterInfo.color} icon={filterInfo.icon}>
        {filterInfo.text}
      </Tag>
    );
  };

  // 处理功能切换
  const handleFeatureToggle = (rule: ForwardRule, feature: string, currentValue: boolean) => {
    const newValue = !currentValue;
    console.log('🔄 切换功能:', rule.id, feature, currentValue, '->', newValue);
    console.log('🔄 切换前规则数据:', rule);
    
    // 防止重复点击
    if (toggleFeatureMutation.isPending) {
      message.warning('请等待上一个操作完成');
      return;
    }
    
    toggleFeatureMutation.mutate({ id: rule.id, feature, enabled: newValue });
  };

  // 处理文件导入
  const handleFileImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const importData = JSON.parse(content);
        
        // 验证文件格式
        if (!importData.rules || !Array.isArray(importData.rules)) {
          message.error('文件格式错误：缺少rules数组');
          return;
        }
        
        importMutation.mutate(importData);
      } catch (error) {
        message.error('文件解析失败：请确保文件是有效的JSON格式');
      }
    };
    reader.readAsText(file);
    return false; // 阻止默认上传行为
  };

  // 过滤规则
  const filteredRules = (rules as ForwardRule[]).filter((rule: ForwardRule) => {
    // 基本搜索过滤
    const matchesSearch = rule.name.toLowerCase().includes(searchText.toLowerCase()) ||
      rule.source_chat_id?.toString().includes(searchText.toLowerCase()) ||
      rule.target_chat_id?.toString().includes(searchText.toLowerCase());
    
    // 确保规则有有效的ID（不应该隐藏任何有效规则）
    const hasValidId = rule.id && rule.id > 0;
    
    return matchesSearch && hasValidId;
  });

  // 调试过滤结果
  console.log('🔍 规则过滤结果:', {
    总规则数: rules?.length || 0,
    过滤后数量: filteredRules?.length || 0,
    搜索文本: searchText,
    规则详情: filteredRules?.map(r => ({ id: r.id, name: r.name, is_active: r.is_active }))
  });

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text: string, record: ForwardRule) => {
        const displayName = text || `规则 #${record.id}` || '未命名规则';
        return (
          <div>
            <div style={{ color: colors.textPrimary, fontWeight: 'bold' }}>{displayName}</div>
          </div>
        );
      },
    },
    {
      title: '源聊天',
      dataIndex: 'source_chat_id',
      key: 'source_chat_id',
      width: 120,
      render: (_: number, record: ForwardRule) => {
        const displayName = getChatDisplayName(record.source_chat_id || '');
        return (
          <Tag color="blue">
            {displayName}
          </Tag>
        );
      },
    },
    {
      title: '目标聊天',
      dataIndex: 'target_chat_id',
      key: 'target_chat_id',
      width: 120,
      render: (_: number, record: ForwardRule) => {
        const displayName = getChatDisplayName(record.target_chat_id || '');
        return (
          <Tag color="green">
            {displayName}
          </Tag>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (is_active: boolean, record: ForwardRule) => (
        <Switch
          checked={is_active}
          onChange={(checked) => handleToggle(record, checked)}
          loading={toggleMutation.isPending}
        />
      ),
    },
    {
      title: '时间过滤',
      key: 'time_filter',
      width: 120,
      render: (_: unknown, record: ForwardRule) => renderTimeFilter(record),
    },
    {
      title: '功能设置',
      key: 'features',
      width: 150,
      render: (_: unknown, record: ForwardRule) => (
        <Space size="small">
          <Tooltip title={`关键词过滤: ${record.enable_keyword_filter ? '已启用' : '已禁用'} (右键编辑关键词)`}>
            <Button
              type="text"
              size="small"
              icon={<FilterOutlined />}
              style={{ 
                color: record.enable_keyword_filter ? colors.info : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_keyword_filter', record.enable_keyword_filter)}
              onContextMenu={(e) => {
                e.preventDefault();
                console.log('跳转到关键词编辑:', record.id);
                navigate(`/rules/${record.id}/keywords`);
              }}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`正则替换: ${record.enable_regex_replace ? '已启用' : '已禁用'} (右键编辑替换规则)`}>
            <Button
              type="text"
              size="small"
              icon={<SwapOutlined />}
              style={{ 
                color: record.enable_regex_replace ? colors.success : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_regex_replace', record.enable_regex_replace)}
              onContextMenu={(e) => {
                e.preventDefault();
                console.log('跳转到替换规则编辑:', record.id);
                navigate(`/rules/${record.id}/replacements`);
              }}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_link_preview ? '关闭' : '开启'}链接预览`}>
            <Button
              type="text"
              size="small"
              icon={<LinkOutlined />}
              style={{ 
                color: record.enable_link_preview ? '#722ed1' : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_link_preview', record.enable_link_preview)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '消息类型',
      key: 'message_types',
      width: 250,
      render: (_: unknown, record: ForwardRule) => (
        <Space size="small" wrap>
          <Tooltip title={`点击${record.enable_text ? '关闭' : '开启'}文本消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<MessageOutlined />}
              style={{ 
                color: record.enable_text ? colors.info : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_text', record.enable_text)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_photo ? '关闭' : '开启'}图片消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<FileImageOutlined />}
              style={{ 
                color: record.enable_photo ? colors.success : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_photo', record.enable_photo)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_video ? '关闭' : '开启'}视频消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<VideoCameraOutlined />}
              style={{ 
                color: record.enable_video ? colors.error : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_video', record.enable_video)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_document ? '关闭' : '开启'}文档消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<FileOutlined />}
              style={{ 
                color: record.enable_document ? '#722ed1' : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_document', record.enable_document)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_audio ? '关闭' : '开启'}音频消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<AudioOutlined />}
              style={{ 
                color: record.enable_audio ? '#13c2c2' : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_audio', record.enable_audio)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_voice ? '关闭' : '开启'}语音消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<SoundOutlined />}
              style={{ 
                color: record.enable_voice ? colors.warning : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_voice', record.enable_voice)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_sticker ? '关闭' : '开启'}贴纸消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<SmileOutlined />}
              style={{ 
                color: record.enable_sticker ? colors.warning : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_sticker', record.enable_sticker)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_animation ? '关闭' : '开启'}动画消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<GifOutlined />}
              style={{ 
                color: record.enable_animation ? '#f759ab' : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_animation', record.enable_animation)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
          <Tooltip title={`点击${record.enable_webpage ? '关闭' : '开启'}网页消息转发`}>
            <Button
              type="text"
              size="small"
              icon={<LinkOutlined />}
              style={{ 
                color: record.enable_webpage ? colors.success : colors.textTertiary,
                border: 'none',
                padding: '2px',
                fontSize: '14px'
              }}
              onClick={() => handleFeatureToggle(record, 'enable_webpage', record.enable_webpage)}
              loading={toggleFeatureMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 100,
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
      render: (_: any, record: ForwardRule) => (
        <Space>
          <Tooltip title="编辑规则">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                console.log('编辑规则:', record.id, '跳转到:', `/rules/${record.id}/edit`);
                console.log('当前路径:', window.location.pathname);
                try {
                  navigate(`/rules/${record.id}/edit`);
                  console.log('导航成功');
                } catch (error) {
                  console.error('导航失败:', error);
                  message.error('页面跳转失败');
                }
              }}
            />
          </Tooltip>
          <Tooltip title="删除规则">
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={(e) => {
                console.log('删除按钮被点击 - 事件:', e);
                console.log('删除按钮被点击 - 规则:', record);
                console.log('删除按钮被点击 - 规则ID:', record.id);
                e.preventDefault();
                e.stopPropagation();
                try {
                  handleDelete(record);
                } catch (error) {
                  console.error('handleDelete 执行出错:', error);
                }
              }}
              loading={deleteMutation.isPending}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 调试信息
  console.log('RulesList 渲染', { 
    rules: rules?.length || 0, 
    isLoading, 
    filteredRules: filteredRules?.length || 0 
  });

  // 移除简化版本的渲染，始终显示完整的界面包括功能按钮

  return (
    <div style={{ padding: '24px' }}>
      <Card className="glass-card">
        <div style={{ marginBottom: '16px' }}>
          <Title level={2} style={{ color: colors.textPrimary, margin: '0 0 16px 0' }}>转发规则管理</Title>
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
            <Space>
            <Search
              placeholder="搜索规则..."
              allowClear
              style={{ 
                width: 250,
              }}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                console.log('刷新规则列表');
                queryClient.invalidateQueries({ queryKey: ['rules'] });
                refetch();
              }}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/rules/new')}
            >
              新建规则
            </Button>
            <Upload
              accept=".json"
              beforeUpload={handleFileImport}
              showUploadList={false}
            >
              <Button
                icon={<ImportOutlined />}
                loading={importMutation.isPending}
              >
                导入
              </Button>
            </Upload>
            <Button
              icon={<ExportOutlined />}
              onClick={() => exportMutation.mutate([])}
              loading={exportMutation.isPending}
            >
              导出
            </Button>
            </Space>
          </div>
        </div>

        <Table
          columns={columns}
          dataSource={filteredRules}
          rowKey="id"
          loading={isLoading}
          scroll={{ x: 1420 }}
          locale={{
            emptyText: (
              <TableEmpty 
                icon="📋"
                title="暂无转发规则"
                description='点击"新建规则"开始创建您的第一个转发规则'
              />
            )
          }}
          pagination={{
            total: filteredRules.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条规则`,
          }}
          style={{ 
            background: 'transparent',
          }}
        />
      </Card>
    </div>
  );
};

export default RulesList;
