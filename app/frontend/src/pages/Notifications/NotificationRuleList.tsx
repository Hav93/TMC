/**
 * 通知规则卡片列表组件
 * 
 * 功能：
 * - 响应式卡片布局
 * - 优化加载性能
 * - 简化配置面板
 */

import React, { useState } from 'react';
import { 
  Card, 
  Row,
  Col,
  Switch,
  Tag,
  Space,
  Button,
  Form,
  Input,
  InputNumber,
  Checkbox,
  message,
  Alert,
  Divider,
  Modal,
  Table,
  Select,
  Popconfirm
} from 'antd';
import { 
  SettingOutlined,
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  LinkOutlined,
  WarningOutlined,
  BugOutlined,
  FileTextOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationService } from '../../services/notifications';
import { clientsApi } from '../../services/clients';
import type { NotificationRule, NotificationType } from '../../services/notifications';

const { TextArea } = Input;

// 通知类型配置
const notificationTypeConfigs: Record<NotificationType, {
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  category: string;
  defaultTemplate: string;
  templateVariables: string[];
}> = {
  resource_captured: {
    name: '资源捕获',
    description: '捕获到115/磁力/ed2k链接时通知',
    icon: <LinkOutlined />,
    color: '#1890ff',
    category: '资源监控',
    defaultTemplate: '🔗 新资源捕获\n链接: {link_url}\n类型: {link_type}\n规则: {rule_name}\n来源: {source_chat_name}\n时间: {capture_time}',
    templateVariables: ['link_url', 'link_type', 'rule_name', 'source_chat_name', 'capture_time']
  },
  save_115_success: {
    name: '115转存成功',
    description: '文件成功转存到115网盘',
    icon: <CloudUploadOutlined />,
    color: '#52c41a',
    category: '115转存',
    defaultTemplate: '☁️ 115转存成功\n文件: {file_name}\n路径: {save_path}\n大小: {file_size}\n用时: {duration}',
    templateVariables: ['file_name', 'save_path', 'file_size', 'duration']
  },
  save_115_failed: {
    name: '115转存失败',
    description: '115转存失败',
    icon: <CloseCircleOutlined />,
    color: '#ff4d4f',
    category: '115转存',
    defaultTemplate: '⚠️ 115转存失败\n链接: {link_url}\n错误: {error_message}\n重试: {retry_count}',
    templateVariables: ['link_url', 'error_message', 'retry_count']
  },
  download_complete: {
    name: '下载完成',
    description: '媒体文件下载完成',
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    category: '下载任务',
    defaultTemplate: '✅ 下载完成\n文件: {file_name}\n大小: {file_size}\n耗时: {duration}\n速度: {avg_speed}',
    templateVariables: ['file_name', 'file_size', 'duration', 'avg_speed']
  },
  download_failed: {
    name: '下载失败',
    description: '媒体文件下载失败',
    icon: <CloseCircleOutlined />,
    color: '#ff4d4f',
    category: '下载任务',
    defaultTemplate: '❌ 下载失败\n文件: {file_name}\n错误: {error_message}\n重试: {retry_count}',
    templateVariables: ['file_name', 'error_message', 'retry_count']
  },
  download_progress: {
    name: '下载进度',
    description: '下载进度更新（谨慎启用）',
    icon: <DownloadOutlined />,
    color: '#faad14',
    category: '下载任务',
    defaultTemplate: '📥 下载进度\n文件: {file_name}\n进度: {progress}%\n速度: {current_speed}',
    templateVariables: ['file_name', 'progress', 'current_speed']
  },
  forward_success: {
    name: '转发成功',
    description: '消息转发成功',
    icon: <SendOutlined />,
    color: '#13c2c2',
    category: '消息转发',
    defaultTemplate: '📨 转发成功\n消息数: {message_count}\n源: {source_chat}\n目标: {target_chat}',
    templateVariables: ['message_count', 'source_chat', 'target_chat']
  },
  forward_failed: {
    name: '转发失败',
    description: '消息转发失败',
    icon: <CloseCircleOutlined />,
    color: '#ff4d4f',
    category: '消息转发',
    defaultTemplate: '❌ 转发失败\n错误: {error_message}\n源: {source_chat}',
    templateVariables: ['error_message', 'source_chat']
  },
  task_stale: {
    name: '任务卡住',
    description: '任务长时间未完成警告',
    icon: <WarningOutlined />,
    color: '#faad14',
    category: '系统通知',
    defaultTemplate: '⏳ 任务卡住\n类型: {task_type}\nID: {task_id}\n重试: {retry_count}次\n时长: {stuck_duration}',
    templateVariables: ['task_type', 'task_id', 'retry_count', 'stuck_duration']
  },
  storage_warning: {
    name: '存储警告',
    description: '存储空间不足警告',
    icon: <WarningOutlined />,
    color: '#faad14',
    category: '系统通知',
    defaultTemplate: '💾 存储警告\n剩余: {current_space}GB\n使用率: {usage_percent}%\n阈值: {threshold}%',
    templateVariables: ['current_space', 'usage_percent', 'threshold']
  },
  daily_report: {
    name: '每日报告',
    description: '每日统计报告',
    icon: <FileTextOutlined />,
    color: '#722ed1',
    category: '系统通知',
    defaultTemplate: '📊 每日报告\n日期: {date}\n下载: {download_count}个\n转存: {save_count}个\n转发: {forward_count}条\n资源: {resource_count}个',
    templateVariables: ['date', 'download_count', 'save_count', 'forward_count', 'resource_count']
  },
  system_error: {
    name: '系统错误',
    description: '系统严重错误通知',
    icon: <BugOutlined />,
    color: '#ff4d4f',
    category: '系统通知',
    defaultTemplate: '🚨 系统错误\n类型: {error_type}\n信息: {error_message}\n时间: {error_time}',
    templateVariables: ['error_type', 'error_message', 'error_time']
  }
};

const NotificationRuleList: React.FC = () => {
  const queryClient = useQueryClient();
  const [editingType, setEditingType] = useState<NotificationType | null>(null);
  const [form] = Form.useForm();
  // 多类型规则 - 创建/编辑
  const [createVisible, setCreateVisible] = useState(false);
  const [editRule, setEditRule] = useState<NotificationRule | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [clientOptions, setClientOptions] = useState<{label: string; value: string; type: 'user'|'bot';}[]>([]);

  // 加载客户端选项
  React.useEffect(() => {
    (async () => {
      try {
        const resp = await clientsApi.getClients();
        const items: {label: string; value: string; type: 'user'|'bot'}[] = [];
        const clients = resp?.clients || {} as any;
        Object.keys(clients).forEach((id) => {
          const c = (clients as any)[id];
          if (c) {
            items.push({
              label: `${id} (${c.client_type}${c.connected ? '·在线' : ''})`,
              value: id,
              type: c.client_type,
            });
          }
        });
        setClientOptions(items);
      } catch {}
    })();
  }, []);

  // 获取所有规则
  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['notification-rules'],
    queryFn: () => notificationService.getRules(),
  });

  // 创建规则的映射
  const rulesMap = new Map<NotificationType, NotificationRule>();
  rules.forEach(rule => {
    rulesMap.set(rule.notification_type, rule);
  });

  // 切换规则启用状态
  const toggleMutation = useMutation({
    mutationFn: async ({ type, isActive, ruleId }: { 
      type: NotificationType; 
      isActive: boolean; 
      ruleId?: number;
    }) => {
      console.log('toggleMutation called:', { type, isActive, ruleId });
      if (ruleId) {
        return notificationService.toggleRule(ruleId, isActive);
      } else {
        // 创建新规则时，默认配置需要有效的telegram_chat_id
        return notificationService.createRule({
          notification_type: type,
          is_active: isActive,
          telegram_enabled: false, // 默认先不启用，等用户配置后再启用
          telegram_chat_id: '',
          webhook_enabled: false,
          webhook_url: '',
          email_enabled: false,
          min_interval: 0,
          max_per_hour: 0,
          include_details: true,
          custom_template: '',
        });
      }
    },
    onSuccess: (data) => {
      console.log('toggleMutation success:', data);
      message.success('状态已更新');
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
    onError: (error: any) => {
      console.error('toggleMutation error:', error);
      message.error(error.response?.data?.detail || '操作失败');
    },
  });

  // 更新规则配置
  const updateMutation = useMutation({
    mutationFn: async ({ ruleId, data }: { ruleId: number; data: any }) => {
      return notificationService.updateRule(ruleId, data);
    },
    onSuccess: () => {
      message.success('配置已保存');
      setEditingType(null);
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '保存失败');
    },
  });

  // 删除规则
  const deleteMutation = useMutation({
    mutationFn: async (ruleId: number) => notificationService.deleteRule(ruleId),
    onSuccess: () => {
      message.success('规则已删除');
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除失败');
    },
  });

  // 处理开关切换
  const handleToggle = (type: NotificationType, checked: boolean) => {
    const existingRule = rulesMap.get(type);
    toggleMutation.mutate({ 
      type, 
      isActive: checked,
      ruleId: existingRule?.id 
    });
  };

  // 打开配置弹窗
  const handleOpenConfig = (type: NotificationType) => {
    const existingRule = rulesMap.get(type);
    if (!existingRule) {
      message.warning('请先启用该通知');
      return;
    }
    
    setEditingType(type);
    form.setFieldsValue({
      telegram_enabled: existingRule.telegram_enabled,
      telegram_chat_id: existingRule.telegram_chat_id,
      webhook_enabled: existingRule.webhook_enabled,
      webhook_url: existingRule.webhook_url,
      min_interval: existingRule.min_interval,
      max_per_hour: existingRule.max_per_hour,
      include_details: existingRule.include_details,
      custom_template: existingRule.custom_template || '',
    });
  };

  // 保存配置
  const handleSaveConfig = async () => {
    if (!editingType) return;
    
    try {
      const values = await form.validateFields();
      const existingRule = rulesMap.get(editingType);
      
      if (!existingRule?.id) {
        message.error('规则不存在');
        return;
      }

      // 验证至少启用一个渠道
      if (!values.telegram_enabled && !values.webhook_enabled) {
        message.error('请至少启用一个通知方式');
        return;
      }

      updateMutation.mutate({ ruleId: existingRule.id, data: values });
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 按类别分组
  const groupedTypes = Object.entries(notificationTypeConfigs).reduce((acc, [type, config]) => {
    if (!acc[config.category]) {
      acc[config.category] = [];
    }
    acc[config.category].push({ type: type as NotificationType, config });
    return acc;
  }, {} as Record<string, Array<{ type: NotificationType; config: typeof notificationTypeConfigs[NotificationType] }>>);

  // 渲染通知卡片
  const renderNotificationCard = (type: NotificationType, config: typeof notificationTypeConfigs[NotificationType]) => {
    const existingRule = rulesMap.get(type);
    const isActive = existingRule?.is_active || false;

    return (
      <Col xs={24} sm={12} lg={8} xl={6} key={type}>
        <Card
          style={{ 
            height: '100%',
            borderColor: isActive ? config.color : undefined,
            borderWidth: isActive ? 2 : 1,
          }}
          bodyStyle={{ padding: '16px' }}
        >
          {/* 卡片头部 */}
          <div style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '24px', color: config.color, marginRight: '8px' }}>
                {config.icon}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ 
                  fontWeight: 'bold', 
                  fontSize: '14px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>
                  {config.name}
                </div>
              </div>
            </div>
            <div style={{ 
              fontSize: '12px', 
              color: '#999',
              lineHeight: '1.4',
              marginBottom: '12px',
              height: '32px',
              overflow: 'hidden'
            }}>
              {config.description}
            </div>
          </div>

          {/* 状态和通知方式 */}
          <div style={{ marginBottom: '12px', minHeight: '22px' }}>
            {existingRule && (existingRule.telegram_enabled || existingRule.webhook_enabled) && (
              <Space size={4} wrap>
                {existingRule.telegram_enabled && (
                  <Tag color="blue" style={{ fontSize: '11px', margin: 0 }}>Telegram</Tag>
                )}
                {existingRule.webhook_enabled && (
                  <Tag color="green" style={{ fontSize: '11px', margin: 0 }}>Webhook</Tag>
                )}
              </Space>
            )}
          </div>

          {/* 操作按钮 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div onClick={(e) => e.stopPropagation()}>
              <Switch
                checked={isActive}
                loading={toggleMutation.isPending}
                onChange={(checked) => {
                  console.log('Switch clicked:', type, checked);
                  handleToggle(type, checked);
                }}
                size="small"
              />
            </div>
            {isActive && (
              <Button
                type="link"
                size="small"
                icon={<SettingOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  console.log('Config button clicked:', type);
                  handleOpenConfig(type);
                }}
                style={{ padding: '0 4px' }}
              >
                配置
              </Button>
            )}
          </div>
        </Card>
      </Col>
    );
  };

  if (isLoading) {
    return (
      <Row gutter={[16, 16]}>
        {[1, 2, 3, 4].map(i => (
          <Col xs={24} sm={12} lg={8} xl={6} key={i}>
            <Card loading />
          </Col>
        ))}
      </Row>
    );
  }

  // 当前编辑的配置
  const currentConfig = editingType ? notificationTypeConfigs[editingType] : null;

  // ========== 多类型规则：Table + 创建/编辑 ========== 
  const typeOptions = Object.keys(notificationTypeConfigs).map(t => ({ label: notificationTypeConfigs[t as NotificationType].name, value: t }));

  const openCreate = () => {
    createForm.resetFields();
    createForm.setFieldsValue({
      notification_types: ['resource_captured'],
      is_active: true,
      telegram_enabled: false,
      webhook_enabled: false,
      min_interval: 0,
      max_per_hour: 0,
      include_details: true,
    });
    setCreateVisible(true);
  };

  const handleCreate = async () => {
    try {
      const values = await createForm.validateFields();
      const types: NotificationType[] = values.notification_types || [];
      if (!types.length) {
        message.warning('请至少选择一种通知类型');
        return;
      }
      const payload = {
        notification_type: types[0],
        notification_types: types,
        is_active: values.is_active !== false,
        telegram_enabled: !!values.telegram_enabled,
        telegram_chat_id: values.telegram_chat_id || '',
        webhook_enabled: !!values.webhook_enabled,
        webhook_url: values.webhook_url || '',
        email_enabled: false,
        min_interval: values.min_interval ?? 0,
        max_per_hour: values.max_per_hour ?? 0,
        include_details: values.include_details !== false,
        custom_template: values.custom_template || '',
      };
      await notificationService.createRule(payload as any);
      message.success('规则已创建');
      setCreateVisible(false);
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    } catch (e) {
      // ignore - antd 会自行提示
    }
  };

  const openEditRule = (rule: NotificationRule) => {
    setEditRule(rule);
    const types = Array.isArray(rule.notification_types)
      ? rule.notification_types
      : (typeof rule.notification_types === 'string' && rule.notification_types.trim()
          ? (JSON.parse(rule.notification_types) as NotificationType[])
          : [rule.notification_type]);
    editForm.setFieldsValue({
      notification_types: types,
      is_active: rule.is_active,
      telegram_enabled: rule.telegram_enabled,
      telegram_chat_id: rule.telegram_chat_id,
      webhook_enabled: rule.webhook_enabled,
      webhook_url: rule.webhook_url,
      min_interval: rule.min_interval,
      max_per_hour: rule.max_per_hour,
      include_details: rule.include_details,
      custom_template: rule.custom_template || '',
    });
  };

  const handleEditSave = async () => {
    if (!editRule?.id) return;
    try {
      const values = await editForm.validateFields();
      await notificationService.updateRule(editRule.id, values);
      message.success('规则已更新');
      setEditRule(null);
      queryClient.invalidateQueries({ queryKey: ['notification-rules'] });
      queryClient.invalidateQueries({ queryKey: ['notification-stats'] });
    } catch (e) {
      // ignore
    }
  };

  const columns: any[] = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '通知类型', key: 'types', render: (_: any, r: NotificationRule) => {
        const types = Array.isArray(r.notification_types)
          ? r.notification_types
          : (typeof r.notification_types === 'string' && r.notification_types.trim()
              ? (JSON.parse(r.notification_types) as NotificationType[])
              : [r.notification_type]);
        return (
          <Space size={4} wrap>
            {types.map(t => (
              <Tag key={t} color={notificationTypeConfigs[t].color} style={{ margin: 0 }}>
                {notificationTypeConfigs[t].name}
              </Tag>
            ))}
          </Space>
        );
      }
    },
    { title: '方式', key: 'channels', render: (_: any, r: NotificationRule) => (
        <Space size={4} wrap>
          {r.telegram_enabled && <Tag color="blue" style={{ margin: 0 }}>Telegram</Tag>}
          {r.webhook_enabled && <Tag color="green" style={{ margin: 0 }}>Webhook</Tag>}
          {r.email_enabled && <Tag color="purple" style={{ margin: 0 }}>Email</Tag>}
        </Space>
      )
    },
    { title: '限流', key: 'rate', render: (_: any, r: NotificationRule) => (
        <span>间隔{r.min_interval || 0}s / 每小时{r.max_per_hour || 0}</span>
      )
    },
    { title: '状态', key: 'active', width: 100, render: (_: any, r: NotificationRule) => (
        <Switch
          checked={r.is_active}
          onChange={() => toggleMutation.mutate({ type: r.notification_type, isActive: !r.is_active, ruleId: r.id })}
          size="small"
        />
      )
    },
    { title: '操作', key: 'action', width: 160, render: (_: any, r: NotificationRule) => (
        <Space size={8}>
          <Button size="small" type="link" onClick={() => openEditRule(r)}>编辑</Button>
          <Popconfirm title="确定删除该规则？" onConfirm={() => r.id && deleteMutation.mutate(r.id)}>
            <Button size="small" type="link" danger loading={deleteMutation.isPending}>删除</Button>
          </Popconfirm>
        </Space>
      )
    },
  ];

  return (
    <div>
      {/* 多类型规则 - 顶部操作与规则表 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontWeight: 600 }}>规则列表（多类型合并配置）</div>
        <Button type="primary" onClick={openCreate}>新建规则</Button>
      </div>
      <Card size="small" style={{ marginBottom: 24 }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={rules}
          size="small"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {Object.entries(groupedTypes).map(([category, types]) => (
        <div key={category} style={{ marginBottom: '24px' }}>
          <div style={{ 
            fontSize: '16px', 
            fontWeight: 'bold', 
            marginBottom: '12px',
            paddingLeft: '8px',
            borderLeft: '3px solid #1890ff'
          }}>
            {category}
          </div>
          <Row gutter={[16, 16]}>
            {types.map(({ type, config }) => renderNotificationCard(type, config))}
          </Row>
        </div>
      ))}

      {/* 配置弹窗 */}
      <Modal
        title={`配置通知 - ${currentConfig?.name}`}
        open={!!editingType}
        onCancel={() => setEditingType(null)}
        onOk={handleSaveConfig}
        confirmLoading={updateMutation.isPending}
        width={700}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Divider orientation="left" plain>通知方式</Divider>
          
          <Form.Item name="telegram_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="blue">Telegram</Tag>
                启用Telegram通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item name="bot_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="geekblue">Bot</Tag>
                启用Bot直发（令牌通过环境变量配置）
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, current) => prev.bot_enabled !== current.bot_enabled}
          >
            {({ getFieldValue }) =>
              getFieldValue('bot_enabled') && (
                <Form.Item
                  name="bot_recipients"
                  label="Bot接收者chat_id（多个）"
                  tooltip="从白名单中匹配：NOTIFY_BOT_WHITELIST；为空则不限制"
                >
                  <Select mode="tags" placeholder="输入chat_id后回车，可添加多个" />
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, current) => prev.telegram_enabled !== current.telegram_enabled}
          >
            {({ getFieldValue }) =>
              getFieldValue('telegram_enabled') && (
                <Form.Item
                  name="telegram_chat_id"
                  label="Telegram聊天ID"
                  rules={[{ required: true, message: '请输入Telegram聊天ID' }]}
                  extra="群/频道请填带 -100 的聊天 ID；私聊填纯数字 ID"
                >
                  <Input placeholder="例如: -1001234567890（群/频道）或 123456789（私聊）" />
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.telegram_enabled!==c.telegram_enabled}>
            {({getFieldValue}) => getFieldValue('telegram_enabled') && (
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="telegram_client_id" label="发送客户端">
                    <Select allowClear options={clientOptions} placeholder="不选则自动选择可用客户端" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="telegram_client_type" label="客户端类型">
                    <Select allowClear options={[{label:'用户', value:'user'},{label:'机器人', value:'bot'}]} placeholder="可选（用于偏好类型）" />
                  </Form.Item>
                </Col>
              </Row>
            )}
          </Form.Item>

          <Form.Item name="webhook_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="green">Webhook</Tag>
                启用Webhook通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, current) => prev.webhook_enabled !== current.webhook_enabled}
          >
            {({ getFieldValue }) =>
              getFieldValue('webhook_enabled') && (
                <Form.Item
                  name="webhook_url"
                  label="Webhook URL"
                  rules={[
                    { required: true, message: '请输入Webhook URL' },
                    { type: 'url', message: '请输入有效的URL' }
                  ]}
                >
                  <Input placeholder="https://example.com/webhook" />
                </Form.Item>
              )
            }
          </Form.Item>

          <Divider orientation="left" plain>频率控制</Divider>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="min_interval"
                label="最小间隔（秒）"
                extra="0 = 无限制"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="max_per_hour"
                label="每小时最大数量"
                extra="0 = 无限制"
              >
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left" plain>高级选项</Divider>
          
          <Form.Item name="include_details" valuePropName="checked">
            <Checkbox>包含详细信息</Checkbox>
          </Form.Item>

          <Form.Item
            name="custom_template"
            label="自定义模板"
          >
            <TextArea
              rows={6}
              placeholder="留空使用默认模板"
            />
          </Form.Item>

          {currentConfig && (
            <Alert
              message="模板参考"
              description={
                <div>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>默认模板：</strong>
                  </div>
                  <pre style={{ 
                    fontSize: '12px', 
                    background: '#f5f5f5', 
                    padding: '8px',
                    borderRadius: '4px',
                    whiteSpace: 'pre-wrap',
                    marginBottom: '8px'
                  }}>
                    {currentConfig.defaultTemplate}
                  </pre>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    <strong>可用变量：</strong> {currentConfig.templateVariables.map(v => `{${v}}`).join(', ')}
                  </div>
                </div>
              }
              type="info"
              showIcon
            />
          )}
        </Form>
      </Modal>

      {/* 新建规则弹窗（多类型） */}
      <Modal
        title="新建通知规则（多类型）"
        open={createVisible}
        onCancel={() => setCreateVisible(false)}
        onOk={handleCreate}
        confirmLoading={false}
        width={760}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical">
          <Form.Item name="notification_types" label="通知类型" rules={[{ required: true, message: '请选择通知类型' }]}> 
            <Select mode="multiple" options={typeOptions} placeholder="选择要覆盖的通知类型" />
          </Form.Item>
          <Divider orientation="left" plain>通知方式</Divider>
          <Form.Item name="telegram_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="blue">Telegram</Tag>
                启用Telegram通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item name="bot_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="geekblue">Bot</Tag>
                启用Bot直发（令牌通过环境变量配置）
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.bot_enabled!==c.bot_enabled}>
            {({getFieldValue}) => getFieldValue('bot_enabled') && (
              <Form.Item name="bot_recipients" label="Bot接收者chat_id（多个）" tooltip="从白名单中匹配：NOTIFY_BOT_WHITELIST；为空则不限制">
                <Select mode="tags" placeholder="输入chat_id后回车，可添加多个" />
              </Form.Item>
            )}
          </Form.Item>
          
          <Form.Item noStyle shouldUpdate={(p,c)=>p.bot_enabled!==c.bot_enabled}>
            {({getFieldValue}) => getFieldValue('bot_enabled') && (
              <Form.Item name="bot_token" label="Bot令牌（可选）" tooltip="留空则使用环境变量 NOTIFY_BOT_TOKEN/TELEGRAM_BOT_TOKEN">
                <Input.Password placeholder="123456:ABC-DEF..." />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.telegram_enabled!==c.telegram_enabled}>
            {({getFieldValue}) => getFieldValue('telegram_enabled') && (
              <Form.Item name="telegram_chat_id" label="Telegram聊天ID" rules={[{ required: true, message: '请输入Telegram聊天ID' }]} extra="群/频道请填带 -100 的聊天 ID；私聊填纯数字 ID"> 
                <Input placeholder="例如: -1001234567890（群/频道）或 123456789（私聊）" />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.telegram_enabled!==c.telegram_enabled}>
            {({getFieldValue}) => getFieldValue('telegram_enabled') && (
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="telegram_client_id" label="发送客户端">
                    <Select allowClear options={clientOptions} placeholder="不选则自动选择可用客户端" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="telegram_client_type" label="客户端类型">
                    <Select allowClear options={[{label:'用户', value:'user'},{label:'机器人', value:'bot'}]} placeholder="可选（用于偏好类型）" />
                  </Form.Item>
                </Col>
              </Row>
            )}
          </Form.Item>
          <Form.Item name="webhook_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="green">Webhook</Tag>
                启用Webhook通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.webhook_enabled!==c.webhook_enabled}>
            {({getFieldValue}) => getFieldValue('webhook_enabled') && (
              <Form.Item name="webhook_url" label="Webhook URL" rules={[{ required: true, message: '请输入Webhook URL' }, { type: 'url', message: '请输入有效的URL' }]}> 
                <Input placeholder="https://example.com/webhook" />
              </Form.Item>
            )}
          </Form.Item>
          <Divider orientation="left" plain>频率控制</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="min_interval" label="最小间隔（秒）" extra="0 = 无限制">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_per_hour" label="每小时最大数量" extra="0 = 无限制">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Divider orientation="left" plain>高级选项</Divider>
          <Form.Item name="include_details" valuePropName="checked">
            <Checkbox>包含详细信息</Checkbox>
          </Form.Item>
          <Form.Item name="custom_template" label="自定义模板">
            <TextArea rows={6} placeholder="留空使用默认模板" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑规则弹窗（多类型） */}
      <Modal
        title="编辑通知规则"
        open={!!editRule}
        onCancel={() => setEditRule(null)}
        onOk={handleEditSave}
        confirmLoading={updateMutation.isPending}
        width={760}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="notification_types" label="通知类型" rules={[{ required: true, message: '请选择通知类型' }]}> 
            <Select mode="multiple" options={typeOptions} placeholder="选择要覆盖的通知类型" />
          </Form.Item>
          <Divider orientation="left" plain>通知方式</Divider>
          <Form.Item name="telegram_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="blue">Telegram</Tag>
                启用Telegram通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.telegram_enabled!==c.telegram_enabled}>
            {({getFieldValue}) => getFieldValue('telegram_enabled') && (
              <Form.Item name="telegram_chat_id" label="Telegram聊天ID" rules={[{ required: true, message: '请输入Telegram聊天ID' }]}> 
                <Input placeholder="例如: 123456789" />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item name="webhook_enabled" valuePropName="checked">
            <Checkbox>
              <Space>
                <Tag color="green">Webhook</Tag>
                启用Webhook通知
              </Space>
            </Checkbox>
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(p,c)=>p.webhook_enabled!==c.webhook_enabled}>
            {({getFieldValue}) => getFieldValue('webhook_enabled') && (
              <Form.Item name="webhook_url" label="Webhook URL" rules={[{ required: true, message: '请输入Webhook URL' }, { type: 'url', message: '请输入有效的URL' }]}> 
                <Input placeholder="https://example.com/webhook" />
              </Form.Item>
            )}
          </Form.Item>
          <Divider orientation="left" plain>频率控制</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="min_interval" label="最小间隔（秒）" extra="0 = 无限制">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="max_per_hour" label="每小时最大数量" extra="0 = 无限制">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Divider orientation="left" plain>高级选项</Divider>
          <Form.Item name="include_details" valuePropName="checked">
            <Checkbox>包含详细信息</Checkbox>
          </Form.Item>
          <Form.Item name="custom_template" label="自定义模板">
            <TextArea rows={6} placeholder="留空使用默认模板" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default NotificationRuleList;
