import React, { useEffect, useMemo, useState } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Select,
  InputNumber,
  Space,
  message,
  Typography,
  Divider,
  Row,
  Col,
  Tabs,
  Alert,
  Modal,
  Tree
} from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useThemeContext } from '../../theme';
import {
  SaveOutlined,
  RollbackOutlined,
  FolderOutlined,
  FilterOutlined,
  SettingOutlined,
  FolderOpenOutlined
} from '@ant-design/icons';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import { clientsApi } from '../../services/clients';
import { chatsApi } from '../../services/chats';
// import { mediaSettingsApi } from '../../services/mediaSettings';
import { DirectoryBrowser } from '../../components/common/DirectoryBrowser';
const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// 兼容 Ant Design 5.x - 使用 items 而不是 TabPane

const MonitorRuleForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { colors } = useThemeContext();
  const isEdit = !!id;
  
  // 目录浏览器状态
  const [localArchiveBrowserVisible, setLocalArchiveBrowserVisible] = useState(false);
  const [cd2BrowseOpen, setCd2BrowseOpen] = useState(false);
  const [cd2Tree, setCd2Tree] = useState<any[]>([]);
  const [cd2Selected, setCd2Selected] = useState<string>('');

  // 获取客户端列表
  const { data: clientsData } = useQuery({
    queryKey: ['clients'],
    queryFn: clientsApi.getClients,
  });

  // 将客户端对象转换为数组
  const clients = useMemo(() => {
    if (!clientsData?.clients) return [];
    return Object.values(clientsData.clients);
  }, [clientsData]);

  // 获取聊天列表
  const { data: chatsData } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats,
  });

  const chats = chatsData?.chats || [];

  // 获取规则详情（编辑模式）
  const { data: ruleResponse } = useQuery({
    queryKey: ['media-monitor-rule', id],
    queryFn: () => mediaMonitorApi.getRule(Number(id)),
    enabled: isEdit,
  });

  // 初始化表单
  useEffect(() => {
    console.log('📦 规则响应数据:', ruleResponse);
    
    if (ruleResponse?.rule) {
      const ruleData = ruleResponse.rule;
      console.log('📋 规则详情:', ruleData);
      
      // 后端的 rule_to_dict 已经解析了 JSON 字段，这里直接使用
      const formData: any = {
        ...ruleData,
        // 确保数组类型字段有默认值
        source_chats: ruleData.source_chats || [],
        media_types: ruleData.media_types || ['photo', 'video', 'audio', 'document'],
        file_extensions: ruleData.file_extensions || [],
        // 确保发送者过滤字段有默认值
        sender_whitelist: ruleData.sender_whitelist || '',
        sender_blacklist: ruleData.sender_blacklist || '',
      };
      
      console.log('📝 设置表单值:', formData);
      form.setFieldsValue(formData);
    }
  }, [ruleResponse, form]);

  // 创建/更新规则
  const saveMutation = useMutation({
    mutationFn: (values: any) => {
      const data = {
        ...values,
        // 转换为 JSON 字符串
        source_chats: JSON.stringify(values.source_chats || []),
        media_types: JSON.stringify(values.media_types || []),
        file_extensions: JSON.stringify(values.file_extensions || []),
      };

      if (isEdit) {
        return mediaMonitorApi.updateRule(Number(id), data);
      }
      return mediaMonitorApi.createRule(data);
    },
    onSuccess: () => {
      message.success(isEdit ? '规则更新成功' : '规则创建成功');
      queryClient.invalidateQueries({ queryKey: ['media-monitor-rules'] });
      navigate('/media-monitor');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '保存失败');
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
    media_types: ['photo', 'video', 'audio', 'document'],
    min_size_mb: 0,
    max_size_mb: 2000,
    organize_enabled: false,
    organize_target_type: 'local',
    organize_mode: 'copy',
    keep_temp_file: false,
    folder_structure: 'date',
    rename_files: false,
    enable_sender_filter: false,
    sender_filter_mode: 'whitelist',
  };

  // Tabs items 配置（Ant Design 5.x）
  const tabItems = useMemo(() => {
    // 确保 clients 和 chats 是数组
    const safeClients = Array.isArray(clients) ? clients : [];
    const safeChats = Array.isArray(chats) ? chats : [];
    
    return [
    {
      key: 'basic',
      label: (
        <span>
          <SettingOutlined /> 基础设置
        </span>
      ),
      children: (
        <div>
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label="规则名称"
                    name="name"
                    rules={[{ required: true, message: '请输入规则名称' }]}
                  >
                    <Input placeholder="例如：视频下载规则" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="客户端"
                    name="client_id"
                    rules={[{ required: true, message: '请选择客户端' }]}
                  >
                    <Select placeholder="选择用于下载的客户端">
                      {safeClients.map((client: any) => (
                        <Option key={client.client_id} value={client.client_id}>
                          {client.client_id} ({client.client_type})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="规则描述" name="description">
                <TextArea rows={2} placeholder="选填：规则的简要说明" />
              </Form.Item>

              <Form.Item label="启用规则" name="is_active" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>

              <Divider orientation="left">监听源</Divider>

              <Form.Item
                label="监听的频道/群组"
                name="source_chats"
                rules={[{ required: true, message: '请选择至少一个聊天' }]}
                tooltip="选择要监控媒体文件的频道或群组"
              >
                <Select 
                  mode="multiple" 
                  placeholder="选择频道/群组"
                  showSearch
                  filterOption={(input, option) =>
                    String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {safeChats.map((chat: any) => (
                    <Option key={chat.id} value={String(chat.id)}>
                      {chat.title || chat.id}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
        </div>
      ),
    },
    {
      key: 'filter',
      label: (
        <span>
          <FilterOutlined /> 媒体过滤
        </span>
      ),
      children: (
        <div>
              <Form.Item
                label="文件类型"
                name="media_types"
                tooltip="选择要下载的媒体类型"
              >
                <Select mode="multiple" placeholder="选择媒体类型">
                  <Option value="photo">图片</Option>
                  <Option value="video">视频</Option>
                  <Option value="audio">音频</Option>
                  <Option value="document">文档</Option>
                </Select>
              </Form.Item>

              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label="最小文件大小 (MB)"
                    name="min_size_mb"
                  >
                    <InputNumber min={0} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="最大文件大小 (MB)"
                    name="max_size_mb"
                  >
                    <InputNumber min={0} max={10000} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    label="文件名包含关键词"
                    name="filename_include"
                    tooltip="逗号分隔，只下载文件名包含这些关键词的文件"
                  >
                    <Input placeholder="例如：教程,课程" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="文件名排除关键词"
                    name="filename_exclude"
                    tooltip="逗号分隔，不下载文件名包含这些关键词的文件"
                  >
                    <Input placeholder="例如：广告,spam" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="允许的文件扩展名"
                name="file_extensions"
                tooltip="留空表示不限制扩展名"
              >
                <Select mode="tags" placeholder="例如：.mp4, .mkv, .avi">
                  <Option value=".mp4">.mp4</Option>
                  <Option value=".mkv">.mkv</Option>
                  <Option value=".avi">.avi</Option>
                  <Option value=".jpg">.jpg</Option>
                  <Option value=".png">.png</Option>
                  <Option value=".mp3">.mp3</Option>
                  <Option value=".flac">.flac</Option>
                </Select>
              </Form.Item>

              <Divider orientation="left">发送者过滤</Divider>

              <Form.Item 
                label="启用发送者过滤" 
                name="enable_sender_filter" 
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item noStyle shouldUpdate={(prev, curr) => 
                prev.enable_sender_filter !== curr.enable_sender_filter
              }>
                {({ getFieldValue }) => {
                  const enabled = getFieldValue('enable_sender_filter');
                  return enabled ? (
                    <>
                      <Form.Item
                        label="过滤模式"
                        name="sender_filter_mode"
                      >
                        <Select>
                          <Option value="whitelist">白名单（只下载名单中的发送者）</Option>
                          <Option value="blacklist">黑名单（阻止名单中的发送者）</Option>
                        </Select>
                      </Form.Item>

                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item
                            label="白名单"
                            name="sender_whitelist"
                            tooltip="支持用户名或ID，逗号分隔"
                          >
                            <TextArea 
                              rows={3} 
                              placeholder="@username1, @username2, 123456" 
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            label="黑名单"
                            name="sender_blacklist"
                            tooltip="支持用户名或ID，逗号分隔"
                          >
                            <TextArea 
                              rows={3} 
                              placeholder="@spammer, 987654" 
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </>
                  ) : null;
                }}
              </Form.Item>
        </div>
      ),
    },
    {
      key: 'organize',
      label: (
        <span>
          <FolderOutlined /> 归档配置
        </span>
      ),
      children: (
        <div>
              <Form.Item
                label="启用文件归档"
                name="organize_enabled"
                valuePropName="checked"
                tooltip="将下载的文件整理到指定目录"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>

              <Form.Item noStyle shouldUpdate={(prev, curr) => 
                prev.organize_enabled !== curr.organize_enabled
              }>
                {({ getFieldValue }) => {
                  const enabled = getFieldValue('organize_enabled');
                  return enabled ? (
                    <>
                      <Form.Item
                        label="归档目标类型"
                        name="organize_target_type"
                      >
                        <Select>
                          <Option value="local">📂 本地路径</Option>
                          <Option value="pan115">☁️ CloudDrive2</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item noStyle shouldUpdate={(prev, curr) => 
                        prev.organize_target_type !== curr.organize_target_type
                      }>
                        {({ getFieldValue }) => {
                          const targetType = getFieldValue('organize_target_type');
                          if (targetType === 'local') {
                            return (
                              <Form.Item
                                label="本地归档路径"
                                name="organize_local_path"
                              >
                                <Input
                                  placeholder="/app/media/archive"
                                  addonAfter={
                                    <Button
                                      type="link"
                                      size="small"
                                      icon={<FolderOpenOutlined />}
                                      onClick={() => setLocalArchiveBrowserVisible(true)}
                                    >
                                      浏览
                                    </Button>
                                  }
                                />
                              </Form.Item>
                            );
                          } else if (targetType === 'pan115') {
                            return (
                              <>
                              <Form.Item
                                label="CloudDrive2 远程路径"
                                name="pan115_remote_path"
                                tooltip={
                                  <div>
                                    <p>文件将通过 CloudDrive2 上传到 115 网盘的此路径下</p>
                                    <p><strong>路径优先级：</strong></p>
                                    <p>1. 规则路径（此处设置）- 优先使用</p>
                                    <p>2. 全局默认路径（系统设置 → CloudDrive2 配置中的挂载点路径）</p>
                                    <p style={{ marginTop: '8px', color: '#ff7875' }}>
                                      <strong>注意：</strong>请先在【系统设置 → CloudDrive2】中配置服务并设置挂载点路径
                                    </p>
                                  </div>
                                }
                              >
                                <Input 
                                  placeholder="绝对路径示例：/115open/测试；相对：测试（拼到默认根）" 
                                  addonBefore="规则路径"
                                />
                              </Form.Item>
                              <Form.Item shouldUpdate={true}>
                                {({ getFieldValue }) => {
                                  const rulePath = getFieldValue('pan115_remote_path') || '';
                                  // 实时从设置页的全局根读取（通过 clouddrive2SettingsApi.getConfig）
                                  // 这里使用 useQuery 的缓存：
                                  // 为简洁起见，回退到占位文本，当设置页还未加载时
                                  // @ts-ignore
                                  const globalConfig = (window as any).__cd2_global_config__;
                                  const globalRoot = (globalConfig?.mount_point) || '（将使用系统设置中的“默认根路径”）';
                                  const finalPath = rulePath.startsWith('/') ? rulePath : `${globalRoot}${globalRoot.endsWith('/') ? '' : '/'}${rulePath}`;
                                  return (
                                      <div style={{ color: '#888', marginTop: -8, marginBottom: 8 }}>
                                        最终上传路径预览：{finalPath}
                                      </div>
                                  );
                                }}
                              </Form.Item>
                              </>
                            );
                          }
                          return null;
                        }}
                      </Form.Item>

                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item
                            label="归档方式"
                            name="organize_mode"
                          >
                            <Select>
                              <Option value="copy">复制（保留临时文件）</Option>
                              <Option value="move">移动（删除临时文件）</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            label="归档后保留临时文件"
                            name="keep_temp_file"
                            valuePropName="checked"
                          >
                            <Switch checkedChildren="保留" unCheckedChildren="删除" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Divider orientation="left">文件夹结构</Divider>

                      <Form.Item
                        label="组织方式"
                        name="folder_structure"
                      >
                        <Select>
                          <Option value="flat">扁平（所有文件在同一目录）</Option>
                          <Option value="date">按日期（{'{year}/{month}/{day}'}）</Option>
                          <Option value="type">按类型（{'{type}/'}）</Option>
                          <Option value="source">按来源（{'{source}/'}）</Option>
                          <Option value="sender">按发送者（{'{sender}/'}）</Option>
                          <Option value="custom">自定义模板</Option>
                        </Select>
                      </Form.Item>

                      <Form.Item noStyle shouldUpdate={(prev, curr) => 
                        prev.folder_structure !== curr.folder_structure
                      }>
                        {({ getFieldValue }) => {
                          const structure = getFieldValue('folder_structure');
                          return structure === 'custom' ? (
                            <Form.Item
                              label="自定义文件夹模板"
                              name="custom_folder_template"
                              tooltip="可用变量：{year}, {month}, {day}, {type}, {source}, {sender}, {source_id}, {sender_id}"
                            >
                              <Input placeholder="{type}/{year}/{month}/{day}" />
                            </Form.Item>
                          ) : null;
                        }}
                      </Form.Item>

                      <Form.Item
                        label="重命名文件"
                        name="rename_files"
                        valuePropName="checked"
                      >
                        <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                      </Form.Item>

                      <Form.Item noStyle shouldUpdate={(prev, curr) => 
                        prev.rename_files !== curr.rename_files
                      }>
                        {({ getFieldValue }) => {
                          const rename = getFieldValue('rename_files');
                          return rename ? (
                            <Form.Item
                              label="文件名模板"
                              name="filename_template"
                              tooltip="可用变量：{date}, {time}, {sender}, {sender_id}, {source}, {source_id}, {original_name}, {type}"
                            >
                              <Input placeholder="{date}_{sender}_{original_name}" />
                            </Form.Item>
                          ) : null;
                        }}
                      </Form.Item>
                    </>
                  ) : null;
                }}
              </Form.Item>
        </div>
      ),
    },
  ];
  }, [clients, chats]);

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Title level={4} style={{ margin: 0 }}>
            {isEdit ? '编辑监控规则' : '新建监控规则'}
          </Title>
        }
        style={{ background: colors.bgContainer }}
        extra={
          <Space>
            <Button 
              icon={<RollbackOutlined />} 
              onClick={() => navigate('/media-monitor')}
            >
              返回
            </Button>
            <Button 
              type="primary" 
              icon={<SaveOutlined />}
              onClick={handleSubmit}
              loading={saveMutation.isPending}
            >
              保存
            </Button>
          </Space>
        }
      >
        <Alert
          message="全局配置说明"
          description={
            <span>
              下载设置、元数据提取、存储清理等全局配置已移至{' '}
              <a href="/settings" style={{ color: colors.primary, fontWeight: 'bold' }}>
                系统设置
              </a>
              {' '}页面统一管理。
            </span>
          }
          type="info"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
        
        <Form
          form={form}
          layout="vertical"
          initialValues={initialValues}
        >
          <Tabs defaultActiveKey="basic" items={tabItems} />
        </Form>
      </Card>

      {/* 本地归档路径浏览器 */}
      <DirectoryBrowser
        visible={localArchiveBrowserVisible}
        onCancel={() => setLocalArchiveBrowserVisible(false)}
        onSelect={(path) => {
          form.setFieldValue('organize_local_path', path);
          message.success(`已选择目录: ${path}`);
        }}
        initialPath={form.getFieldValue('organize_local_path') || '/app/media/archive'}
      />

      {/* CloudDrive2 目录浏览弹窗 */}
      <Modal
        title="选择 CloudDrive2 目录"
        open={cd2BrowseOpen}
        onOk={() => { form.setFieldValue('pan115_remote_path', cd2Selected); setCd2BrowseOpen(false); }}
        onCancel={() => setCd2BrowseOpen(false)}
        okText="使用此路径"
        cancelText="取消"
        destroyOnClose
      >
        <Tree
          treeData={cd2Tree}
          loadData={async (node) => {
            const res = await fetch('/api/settings/clouddrive2/browse', {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: node.key })
            }).then(r => r.json());
            const children = (res?.items || []).map((d: any) => ({ title: d.name || d.path.split('/').pop() || d.path, key: d.path }));
            setCd2Tree(prev => prev.map(n => n.key === node.key ? { ...n, children } : n));
          }}
          onSelect={(keys) => { if (keys && keys[0]) setCd2Selected(String(keys[0])); }}
          defaultExpandAll
        />
        <div style={{ marginTop: 8, color: '#888' }}>当前选择: {cd2Selected}</div>
      </Modal>
    </div>
  );
};

export default MonitorRuleForm;

