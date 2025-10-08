import React, { useState, useEffect } from 'react';
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
  Tooltip,
  Tag
} from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useThemeContext } from '../../theme';
import {
  SaveOutlined,
  RollbackOutlined,
  InfoCircleOutlined,
  CloudUploadOutlined,
  FolderOutlined,
  FilterOutlined,
  DownloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import { clientsApi } from '../../services/clients';
import { chatsApi } from '../../services/chats';
import type { MediaMonitorRule } from '../../types/media';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

const MonitorRuleForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { colors } = useThemeContext();
  const isEdit = !!id;

  // 获取客户端列表
  const { data: clientsData } = useQuery({
    queryKey: ['clients'],
    queryFn: clientsApi.getClients,
  });

  const clients = clientsData?.clients || [];

  // 获取聊天列表
  const { data: chatsData } = useQuery({
    queryKey: ['chats'],
    queryFn: chatsApi.getChats,
  });

  const chats = chatsData?.chats || [];

  // 获取规则详情（编辑模式）
  const { data: ruleData, isLoading } = useQuery({
    queryKey: ['media-monitor-rule', id],
    queryFn: () => mediaMonitorApi.getRule(Number(id)),
    enabled: isEdit,
  });

  // 初始化表单
  useEffect(() => {
    if (ruleData) {
      const formData: any = {
        ...ruleData,
        // 解析 JSON 字段
        source_chats: ruleData.source_chats ? JSON.parse(ruleData.source_chats) : [],
        media_types: ruleData.media_types ? JSON.parse(ruleData.media_types) : ['photo', 'video', 'audio', 'document'],
        file_extensions: ruleData.file_extensions ? JSON.parse(ruleData.file_extensions) : [],
      };
      form.setFieldsValue(formData);
    }
  }, [ruleData, form]);

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
    concurrent_downloads: 3,
    retry_on_failure: true,
    max_retries: 3,
    extract_metadata: true,
    metadata_mode: 'lightweight',
    metadata_timeout: 10,
    async_metadata_extraction: true,
    organize_enabled: false,
    organize_target_type: 'local',
    organize_mode: 'copy',
    keep_temp_file: false,
    clouddrive_enabled: false,
    folder_structure: 'date',
    rename_files: false,
    auto_cleanup_enabled: true,
    auto_cleanup_days: 7,
    cleanup_only_organized: true,
    max_storage_gb: 100,
    enable_sender_filter: false,
    sender_filter_mode: 'whitelist',
    temp_folder: '/app/media/downloads',
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Title level={4} style={{ margin: 0 }}>
            {isEdit ? '编辑监控规则' : '新建监控规则'}
          </Title>
        }
        style={{ background: colors.cardBg }}
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
        <Form
          form={form}
          layout="vertical"
          initialValues={initialValues}
        >
          <Tabs defaultActiveKey="basic">
            {/* 基础设置 */}
            <TabPane tab={<span><SettingOutlined /> 基础设置</span>} key="basic">
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
                      {clients.map((client: any) => (
                        <Option key={client.id} value={client.id}>
                          {client.id} ({client.type})
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
                    (option?.children as string).toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {chats.map((chat: any) => (
                    <Option key={chat.id} value={String(chat.id)}>
                      {chat.title || chat.id}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </TabPane>

            {/* 媒体过滤 */}
            <TabPane tab={<span><FilterOutlined /> 媒体过滤</span>} key="filter">
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
            </TabPane>

            {/* 下载设置 */}
            <TabPane tab={<span><DownloadOutlined /> 下载设置</span>} key="download">
              <Form.Item
                label="临时下载文件夹"
                name="temp_folder"
              >
                <Input placeholder="/app/media/downloads" />
              </Form.Item>

              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    label="并发下载数"
                    name="concurrent_downloads"
                  >
                    <InputNumber min={1} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="失败重试"
                    name="retry_on_failure"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="最大重试次数"
                    name="max_retries"
                  >
                    <InputNumber min={1} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">元数据提取</Divider>

              <Row gutter={24}>
                <Col span={8}>
                  <Form.Item
                    label="提取元数据"
                    name="extract_metadata"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="提取模式"
                    name="metadata_mode"
                  >
                    <Select>
                      <Option value="disabled">禁用</Option>
                      <Option value="lightweight">轻量级（快速）</Option>
                      <Option value="full">完整（详细）</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="超时时间（秒）"
                    name="metadata_timeout"
                  >
                    <InputNumber min={5} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="异步提取元数据"
                name="async_metadata_extraction"
                valuePropName="checked"
                tooltip="启用后元数据提取不会阻塞下载队列"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </TabPane>

            {/* 归档配置 */}
            <TabPane tab={<span><FolderOutlined /> 归档配置</span>} key="organize">
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
                          <Option value="local">本地路径</Option>
                          <Option value="clouddrive_mount">CloudDrive 挂载路径</Option>
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
                                <Input placeholder="/app/media/archive" />
                              </Form.Item>
                            );
                          } else if (targetType === 'clouddrive_mount') {
                            return (
                              <Form.Item
                                label="CloudDrive 挂载路径"
                                name="organize_clouddrive_mount"
                              >
                                <Input placeholder="/mnt/clouddrive/Media" />
                              </Form.Item>
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
                              tooltip="可用变量：{year}, {month}, {day}, {type}, {source}, {sender}"
                            >
                              <Input placeholder="{year}/{month}/{type}" />
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
                              tooltip="可用变量：{date}, {time}, {sender}, {original_name}, {type}"
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
            </TabPane>

            {/* CloudDrive 设置 */}
            <TabPane tab={<span><CloudUploadOutlined /> CloudDrive</span>} key="clouddrive">
              <Alert
                message="CloudDrive API 上传"
                description="除了使用挂载路径外，还可以通过 CloudDrive API 直接上传文件到云端"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="启用 CloudDrive API 上传"
                name="clouddrive_enabled"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>

              <Form.Item noStyle shouldUpdate={(prev, curr) => 
                prev.clouddrive_enabled !== curr.clouddrive_enabled
              }>
                {({ getFieldValue }) => {
                  const enabled = getFieldValue('clouddrive_enabled');
                  return enabled ? (
                    <>
                      <Form.Item
                        label="CloudDrive 服务地址"
                        name="clouddrive_url"
                        rules={[{ required: enabled, message: '请输入服务地址' }]}
                      >
                        <Input placeholder="http://localhost:19798" />
                      </Form.Item>

                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item
                            label="用户名"
                            name="clouddrive_username"
                            rules={[{ required: enabled, message: '请输入用户名' }]}
                          >
                            <Input placeholder="admin" />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            label="密码"
                            name="clouddrive_password"
                            rules={[{ required: enabled, message: '请输入密码' }]}
                          >
                            <Input.Password placeholder="密码" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item
                        label="远程路径"
                        name="clouddrive_remote_path"
                      >
                        <Input placeholder="/Media" />
                      </Form.Item>
                    </>
                  ) : null;
                }}
              </Form.Item>
            </TabPane>

            {/* 清理设置 */}
            <TabPane tab="清理设置" key="cleanup">
              <Form.Item
                label="启用自动清理"
                name="auto_cleanup_enabled"
                valuePropName="checked"
                tooltip="定期清理过期的临时文件"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>

              <Form.Item noStyle shouldUpdate={(prev, curr) => 
                prev.auto_cleanup_enabled !== curr.auto_cleanup_enabled
              }>
                {({ getFieldValue }) => {
                  const enabled = getFieldValue('auto_cleanup_enabled');
                  return enabled ? (
                    <>
                      <Row gutter={24}>
                        <Col span={12}>
                          <Form.Item
                            label="保留天数"
                            name="auto_cleanup_days"
                          >
                            <InputNumber 
                              min={1} 
                              max={365} 
                              style={{ width: '100%' }}
                              addonAfter="天"
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            label="只清理已归档文件"
                            name="cleanup_only_organized"
                            valuePropName="checked"
                          >
                            <Switch checkedChildren="是" unCheckedChildren="否" />
                          </Form.Item>
                        </Col>
                      </Row>
                    </>
                  ) : null;
                }}
              </Form.Item>

              <Divider orientation="left">存储限制</Divider>

              <Form.Item
                label="最大存储容量 (GB)"
                name="max_storage_gb"
                tooltip="超过此容量将触发自动清理"
              >
                <InputNumber 
                  min={10} 
                  max={10000} 
                  style={{ width: '100%' }}
                  addonAfter="GB"
                />
              </Form.Item>

              <Alert
                message="存储管理"
                description="当存储使用率超过90%时，系统会自动触发清理。超过95%时会发出严重警告并建议暂停下载。"
                type="warning"
                showIcon
              />
            </TabPane>
          </Tabs>
        </Form>
      </Card>
    </div>
  );
};

export default MonitorRuleForm;

