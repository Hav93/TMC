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
  Tooltip,
  Alert,
  Divider,
  Modal
} from 'antd';
import { 
  BellOutlined,
  SettingOutlined,
  SendOutlined,
  ThunderboltOutlined,
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

  return (
    <div>
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
                >
                  <Input placeholder="例如: 123456789" />
                </Form.Item>
              )
            }
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
    </div>
  );
};

export default NotificationRuleList;
