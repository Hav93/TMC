import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Divider,
  Row,
  Col,
  Select,
  Alert,
  Typography,
  Space,
  Spin,
} from 'antd';
import {
  SaveOutlined,
  CloudUploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useThemeContext } from '../../theme';
import { mediaSettingsApi } from '../../services/mediaSettings';
import { DirectoryBrowser } from '../../components/common/DirectoryBrowser';
import type { MediaSettings } from '../../types/settings';

const { Title, Text } = Typography;
const { Option } = Select;

const MediaSettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { colors } = useThemeContext();
  
  // 目录浏览器状态
  const [cloudDriveBrowserVisible, setCloudDriveBrowserVisible] = useState(false);
  const [localBrowserVisible, setLocalBrowserVisible] = useState(false);

  // 获取配置
  const { data: settings, isLoading } = useQuery({
    queryKey: ['media-settings'],
    queryFn: mediaSettingsApi.getSettings,
  });

  // 保存配置
  const saveMutation = useMutation({
    mutationFn: (values: MediaSettings) => mediaSettingsApi.updateSettings(values),
    onSuccess: () => {
      message.success('配置保存成功');
      queryClient.invalidateQueries({ queryKey: ['media-settings'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.message || '保存失败');
    },
  });

  // 测试 CloudDrive 连接
  const testMutation = useMutation({
    mutationFn: (values: MediaSettings) => mediaSettingsApi.testCloudDrive(values),
    onSuccess: (result) => {
      if (result.success) {
        message.success(result.message);
      } else {
        message.error(result.message);
      }
    },
    onError: () => {
      message.error('测试失败');
    },
  });

  // 初始化表单
  React.useEffect(() => {
    if (settings) {
      form.setFieldsValue(settings);
    }
  }, [settings, form]);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      saveMutation.mutate(values);
    } catch (error) {
      message.error('请检查表单填写');
    }
  };

  const handleTestCloudDrive = async () => {
    try {
      const values = await form.validateFields([
        'clouddrive_url',
        'clouddrive_username',
        'clouddrive_password',
      ]);
      testMutation.mutate(values);
    } catch (error) {
      message.error('请填写 CloudDrive 配置');
    }
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载配置中..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={<Title level={4} style={{ margin: 0 }}>媒体管理配置</Title>}
        style={{ background: colors.cardBg }}
        extra={
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saveMutation.isPending}
          >
            保存配置
          </Button>
        }
      >
        <Alert
          message="全局配置"
          description="这些配置将应用于所有媒体监控规则，除非规则中有特殊设置。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form form={form} layout="vertical">
          {/* CloudDrive 配置 */}
          <Divider orientation="left">
            <Space>
              <CloudUploadOutlined />
              CloudDrive 配置
            </Space>
          </Divider>

          <Form.Item
            label="启用 CloudDrive"
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
                    label="服务地址"
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
                    <Input
                      placeholder="/Media"
                      addonAfter={
                        <Button
                          type="link"
                          size="small"
                          icon={<FolderOpenOutlined />}
                          onClick={() => setCloudDriveBrowserVisible(true)}
                        >
                          浏览
                        </Button>
                      }
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      icon={<ExperimentOutlined />}
                      onClick={handleTestCloudDrive}
                      loading={testMutation.isPending}
                    >
                      测试连接
                    </Button>
                  </Form.Item>
                </>
              ) : null;
            }}
          </Form.Item>

          {/* 下载设置 */}
          <Divider orientation="left">
            <Space>
              <DownloadOutlined />
              下载设置
            </Space>
          </Divider>

          <Form.Item
            label="临时下载文件夹"
            name="temp_folder"
          >
            <Input
              placeholder="/app/media/downloads"
              addonAfter={
                <Button
                  type="link"
                  size="small"
                  icon={<FolderOpenOutlined />}
                  onClick={() => setLocalBrowserVisible(true)}
                >
                  浏览
                </Button>
              }
            />
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
                label="失败时重试"
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

          {/* 元数据提取 */}
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

          {/* 存储清理 */}
          <Divider orientation="left">
            <Space>
              <DeleteOutlined />
              存储清理
            </Space>
          </Divider>

          <Form.Item
            label="启用自动清理"
            name="auto_cleanup_enabled"
            valuePropName="checked"
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
                        label="临时文件保留天数"
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
        </Form>
      </Card>

      {/* CloudDrive 目录浏览器 */}
      <DirectoryBrowser
        visible={cloudDriveBrowserVisible}
        onCancel={() => setCloudDriveBrowserVisible(false)}
        onSelect={(path) => {
          form.setFieldValue('clouddrive_remote_path', path);
          message.success(`已选择目录: ${path}`);
        }}
        type="clouddrive"
        clouddriveUrl={form.getFieldValue('clouddrive_url')}
        clouddriveUsername={form.getFieldValue('clouddrive_username')}
        clouddrivePassword={form.getFieldValue('clouddrive_password')}
        initialPath={form.getFieldValue('clouddrive_remote_path') || '/'}
      />

      {/* 本地目录浏览器 */}
      <DirectoryBrowser
        visible={localBrowserVisible}
        onCancel={() => setLocalBrowserVisible(false)}
        onSelect={(path) => {
          form.setFieldValue('temp_folder', path);
          message.success(`已选择目录: ${path}`);
        }}
        type="local"
        initialPath={form.getFieldValue('temp_folder') || '/app'}
      />
    </div>
  );
};

export default MediaSettingsPage;

