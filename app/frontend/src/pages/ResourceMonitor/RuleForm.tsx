import React, { useEffect, useMemo, useState } from 'react';
import {
  Form,
  Input,
  Button,
  Switch,
  Select,
  InputNumber,
  Space,
  message,
  Divider,
  Card,
  Row,
  Col,
  Tag,
  Tooltip,
  Alert
} from 'antd';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  SaveOutlined,
  CloseOutlined,
  PlusOutlined,
  MinusCircleOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { resourceMonitorService } from '../../services/resourceMonitor';
import api from '../../services/api';
import type { ResourceMonitorRule, KeywordConfig } from '../../services/resourceMonitor';
import { chatsApi } from '../../services/chats';

const { TextArea } = Input;
const { Option } = Select;

interface RuleFormProps {
  rule?: ResourceMonitorRule;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const RuleForm: React.FC<RuleFormProps> = ({ rule, onSuccess, onCancel }) => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!rule?.id;
  const [showTypeOverrides, setShowTypeOverrides] = useState(false);
  const [cd2Root, setCd2Root] = useState<string>('/115open');
  // 顶层 watch（避免在条件分支中调用 hooks 导致白屏）
  const watchTargetPath = Form.useWatch('target_path', form);
  const watchPan115 = Form.useWatch('target_path_pan115', form);
  const watchMagnet = Form.useWatch('target_path_magnet', form);
  const watchEd2k = Form.useWatch('target_path_ed2k', form);

  // 获取聊天列表
  const { data: chatsData } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats,
  });

  const chats = chatsData?.chats || [];

  // 读取CD2在线根（从设置接口推导）
  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/api/settings/clouddrive2');
        const mount: string = data?.mount_point || '/CloudNAS/115';
        let onlineRoot = '/115open';
        if (typeof mount === 'string' && mount.startsWith('/CloudNAS/')) {
          const seg = mount.split('/').filter(Boolean).pop();
          onlineRoot = seg ? `/${seg}` : '/115open';
        } else if (typeof mount === 'string' && mount.startsWith('/')) {
          onlineRoot = mount;
        }
        setCd2Root(onlineRoot);
      } catch {
        setCd2Root('/115open');
      }
    })();
  }, []);

  // 初始化表单
  useEffect(() => {
    if (rule) {
      form.setFieldsValue({
        ...rule,
        source_chats: rule.source_chats || [],
        link_types: rule.link_types || ['pan115', 'magnet', 'ed2k'],
        keywords: rule.keywords || [],
        default_tags: rule.default_tags || [],
        auto_save_to_115: rule.auto_save_to_115 || false,
        target_path: rule.target_path || '',
        target_path_pan115: (rule as any).target_path_pan115 || '',
        target_path_magnet: (rule as any).target_path_magnet || '',
        target_path_ed2k: (rule as any).target_path_ed2k || '',
      });
      // 根据是否存在类型专属路径，恢复开关显示为开启
      const anyOverride = Boolean(
        (rule as any).target_path_pan115 ||
        (rule as any).target_path_magnet ||
        (rule as any).target_path_ed2k
      );
      setShowTypeOverrides(anyOverride);
    }
  }, [rule, form]);

  // 保存规则
  const saveMutation = useMutation({
    mutationFn: (values: any) => {
      if (isEdit && rule?.id) {
        return resourceMonitorService.updateRule(rule.id, values);
      }
      return resourceMonitorService.createRule(values);
    },
    onSuccess: () => {
      message.success(isEdit ? '规则更新成功' : '规则创建成功');
      queryClient.invalidateQueries({ queryKey: ['resource-monitor-rules'] });
      onSuccess?.();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '保存失败');
    },
  });

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      saveMutation.mutate(values);
    } catch (error) {
      message.error('请检查表单填写');
    }
  };

  // 初始值
  const initialValues = {
    is_active: true,
    link_types: ['pan115', 'magnet', 'ed2k'],
    keywords: [],
    auto_save_to_115: false,
    default_tags: [],
    enable_deduplication: true,
    dedup_time_window: 24,
  };

  // 路径预览计算
  const renderPreview = (val?: string) => {
    const p = (val || '').trim();
    const rel = p.startsWith('/') ? p.replace(/^\/CloudNAS\/[^/]+\//, '/').replace(/^\//, '') : p;
    const pan = rel ? `/${rel}` : '/';
    const cd2 = rel ? `${cd2Root}/${rel}`.replace(/\/+/g, '/') : cd2Root;
    return (
      <div style={{ fontSize: 12, color: '#888' }}>
        <div>pan115 预览: {pan}</div>
        <div>CloudDrive2 预览: {cd2}</div>
      </div>
    );
  };

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={initialValues}
      onFinish={handleSubmit}
    >
      {/* 基本信息 */}
      <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={16}>
            <Form.Item
              label="规则名称"
              name="name"
              rules={[{ required: true, message: '请输入规则名称' }]}
            >
              <Input placeholder="例如：115资源监控" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              label="启用状态"
              name="is_active"
              valuePropName="checked"
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label={
            <Space>
              <span>源聊天</span>
              <Tooltip title="选择要监控的Telegram聊天/频道">
                <QuestionCircleOutlined />
              </Tooltip>
            </Space>
          }
          name="source_chats"
          rules={[{ required: true, message: '请选择至少一个源聊天' }]}
        >
          <Select
            mode="multiple"
            placeholder="选择要监控的聊天"
            showSearch
            filterOption={(input, option) =>
              (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {chats.map((chat: any) => (
              <Option key={chat.id} value={chat.id}>
                {chat.title || chat.username || chat.id}
              </Option>
            ))}
          </Select>
        </Form.Item>
      </Card>

      {/* 链接类型 */}
      <Card title="链接类型" size="small" style={{ marginBottom: 16 }}>
        <Form.Item
          label="监控的链接类型"
          name="link_types"
          rules={[{ required: true, message: '请选择至少一种链接类型' }]}
        >
          <Select mode="multiple" placeholder="选择要监控的链接类型">
            <Option value="pan115">
              <Tag color="blue">115网盘</Tag>
            </Option>
            <Option value="magnet">
              <Tag color="purple">磁力链接</Tag>
            </Option>
            <Option value="ed2k">
              <Tag color="cyan">ed2k链接</Tag>
            </Option>
          </Select>
        </Form.Item>
      </Card>

      {/* 关键词过滤 */}
      <Card title="关键词过滤" size="small" style={{ marginBottom: 16 }}>
        <Alert
          message="留空表示不限制，匹配任何消息中的链接"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Form.List name="keywords">
          {(fields, { add, remove }) => (
            <>
              {fields.map(({ key, name, ...restField }) => (
                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                  <Form.Item
                    {...restField}
                    name={[name, 'keyword']}
                    rules={[{ required: true, message: '请输入关键词' }]}
                    style={{ marginBottom: 0, width: 200 }}
                  >
                    <Input placeholder="关键词" />
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'mode']}
                    initialValue="contains"
                    style={{ marginBottom: 0, width: 120 }}
                  >
                    <Select>
                      <Option value="contains">包含</Option>
                      <Option value="regex">正则</Option>
                      <Option value="exact">完全匹配</Option>
                      <Option value="starts_with">开头</Option>
                      <Option value="ends_with">结尾</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'case_sensitive']}
                    valuePropName="checked"
                    initialValue={false}
                    style={{ marginBottom: 0 }}
                  >
                    <Tooltip title="区分大小写">
                      <Switch checkedChildren="Aa" unCheckedChildren="aa" />
                    </Tooltip>
                  </Form.Item>
                  <Form.Item
                    {...restField}
                    name={[name, 'is_exclude']}
                    valuePropName="checked"
                    initialValue={false}
                    style={{ marginBottom: 0 }}
                  >
                    <Tooltip title="排除模式">
                      <Switch checkedChildren="排除" unCheckedChildren="包含" />
                    </Tooltip>
                  </Form.Item>
                  <MinusCircleOutlined onClick={() => remove(name)} />
                </Space>
              ))}
              <Form.Item>
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  添加关键词
                </Button>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Card>

      {/* 115转存设置 */}
      <Card title="115转存设置" size="small" style={{ marginBottom: 16 }}>
        <Form.Item
          label="自动转存到115"
          name="auto_save_to_115"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) => 
            prevValues.auto_save_to_115 !== currentValues.auto_save_to_115
          }
        >
          {({ getFieldValue }) =>
            getFieldValue('auto_save_to_115') ? (
              <>
                <Alert
                  message="将使用系统设置中配置的115账号进行转存"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Form.Item
                  label="目标路径（相对在线路径）"
                  name="target_path"
                  rules={[{ required: true, message: '请输入目标路径' }]}
                  tooltip="不写根名，如 分类/电影/{YYYY}/{MM}；绝对路径也兼容"
                >
                  <Input placeholder="分类/资源/{YYYY}/{MM}" />
                </Form.Item>
                {renderPreview(watchTargetPath)}

                <Divider style={{ margin: '12px 0' }} />
                <Space align="center" style={{ marginBottom: 8 }}>
                  <Switch
                    checked={showTypeOverrides}
                    onChange={(checked) => {
                      setShowTypeOverrides(checked);
                      // 若关闭开关，清空类型专属路径，确保后端不再使用覆盖路径
                      if (!checked) {
                        form.setFieldsValue({
                          target_path_pan115: '',
                          target_path_magnet: '',
                          target_path_ed2k: ''
                        });
                      }
                    }}
                  />
                  <span>按类型使用不同目录（可选）</span>
                </Space>
                {showTypeOverrides && (
                  <>
                    <Form.Item label="115分享覆盖路径" name="target_path_pan115">
                      <Input placeholder="分享/{YYYY}/{MM}" />
                    </Form.Item>
                    {renderPreview(watchPan115)}
                    <Form.Item label="磁力覆盖路径" name="target_path_magnet">
                      <Input placeholder="离线/磁力/{YYYY}/{MM}" />
                    </Form.Item>
                    {renderPreview(watchMagnet)}
                    <Form.Item label="ed2k覆盖路径" name="target_path_ed2k">
                      <Input placeholder="离线/ed2k/{YYYY}/{MM}" />
                    </Form.Item>
                    {renderPreview(watchEd2k)}
                  </>
                )}

                <Form.Item
                  label="默认标签"
                  name="default_tags"
                  tooltip="为转存的资源添加默认标签，方便后续管理"
                >
                  <Select
                    mode="tags"
                    placeholder="输入标签后按回车添加"
                  />
                </Form.Item>
              </>
            ) : null
          }
        </Form.Item>
      </Card>

      {/* 去重设置 */}
      <Card title="去重设置" size="small" style={{ marginBottom: 16 }}>
        <Form.Item
          label="启用去重"
          name="enable_deduplication"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) => 
            prevValues.enable_deduplication !== currentValues.enable_deduplication
          }
        >
          {({ getFieldValue }) =>
            getFieldValue('enable_deduplication') ? (
              <Form.Item
                label={
                  <Space>
                    <span>去重时间窗口（小时）</span>
                    <Tooltip title="在此时间窗口内，相同的链接只会被记录一次">
                      <QuestionCircleOutlined />
                    </Tooltip>
                  </Space>
                }
                name="dedup_time_window"
                rules={[{ required: true, message: '请输入去重时间窗口' }]}
              >
                <InputNumber min={1} max={720} style={{ width: '100%' }} />
              </Form.Item>
            ) : null
          }
        </Form.Item>
      </Card>

      {/* 操作按钮 */}
      <Form.Item>
        <Space>
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={saveMutation.isPending}
          >
            {isEdit ? '更新规则' : '创建规则'}
          </Button>
          <Button icon={<CloseOutlined />} onClick={onCancel}>
            取消
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default RuleForm;

