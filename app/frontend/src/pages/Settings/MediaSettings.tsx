import React, { useEffect } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Button,
  Space,
  message,
  Alert,
  Divider,
  Select,
  Typography,
} from 'antd';
import { SaveOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mediaSettingsApi } from '../../services/mediaSettings';
import type { MediaSettings } from '../../types/settings';
import { useThemeContext } from '../../theme';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const MediaSettingsPage: React.FC = () => {
  const { colors } = useThemeContext();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取媒体配置
  const { data: settings, isLoading } = useQuery({
    queryKey: ['media-settings'],
    queryFn: mediaSettingsApi.getSettings,
  });

  // 更新配置
  const updateMutation = useMutation({
    mutationFn: mediaSettingsApi.updateSettings,
    onSuccess: () => {
      message.success('媒体配置已保存');
      queryClient.invalidateQueries({ queryKey: ['media-settings'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '保存失败');
    },
  });

  // 填充表单数据
  useEffect(() => {
    if (settings) {
      form.setFieldsValue(settings);
    }
  }, [settings, form]);

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateMutation.mutateAsync(values as MediaSettings);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <InfoCircleOutlined />
            <span>媒体管理全局配置</span>
          </Space>
        }
        style={{ background: colors.cardBg }}
        extra={
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={updateMutation.isPending}
          >
            保存配置
          </Button>
        }
      >
        <Alert
          message="全局配置说明"
          description="这里的配置将作为所有媒体监控规则的默认设置。您可以在创建具体规则时覆盖这些默认值。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form
          form={form}
          layout="vertical"
          initialValues={{
            temp_folder: '/app/media/downloads',
            concurrent_downloads: 3,
            retry_on_failure: true,
            max_retries: 3,
            extract_metadata: true,
            metadata_mode: 'lightweight',
            metadata_timeout: 10,
            async_metadata_extraction: true,
            auto_cleanup_enabled: true,
            auto_cleanup_days: 7,
            cleanup_only_organized: true,
            max_storage_gb: 100,
          }}
        >
          {/* 下载设置 */}
          <Title level={5}>下载设置</Title>
          <Divider />

          <Form.Item
            label="临时下载文件夹"
            name="temp_folder"
            tooltip="媒体文件下载时的临时存储位置"
            rules={[{ required: true, message: '请输入临时文件夹路径' }]}
          >
            <Input placeholder="/app/media/downloads" />
          </Form.Item>

          <Form.Item
            label="并发下载数"
            name="concurrent_downloads"
            tooltip="同时进行的下载任务数量，建议 3-5"
            rules={[
              { required: true, message: '请输入并发下载数' },
              { type: 'number', min: 1, max: 10, message: '范围: 1-10' },
            ]}
          >
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="失败时重试"
            name="retry_on_failure"
            valuePropName="checked"
            tooltip="下载失败时是否自动重试"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="最大重试次数"
            name="max_retries"
            tooltip="下载失败后的最大重试次数"
            rules={[
              { required: true, message: '请输入最大重试次数' },
              { type: 'number', min: 0, max: 10, message: '范围: 0-10' },
            ]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>

          {/* 元数据提取 */}
          <Title level={5} style={{ marginTop: 32 }}>元数据提取</Title>
          <Divider />

          <Form.Item
            label="提取元数据"
            name="extract_metadata"
            valuePropName="checked"
            tooltip="是否提取媒体文件的元数据（标题、时长等）"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="提取模式"
            name="metadata_mode"
            tooltip="元数据提取的详细程度"
          >
            <Select>
              <Option value="disabled">禁用</Option>
              <Option value="lightweight">轻量级（快速）</Option>
              <Option value="full">完整（详细）</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="超时时间（秒）"
            name="metadata_timeout"
            tooltip="元数据提取的超时时间"
            rules={[
              { required: true, message: '请输入超时时间' },
              { type: 'number', min: 1, max: 60, message: '范围: 1-60' },
            ]}
          >
            <InputNumber min={1} max={60} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="异步提取元数据"
            name="async_metadata_extraction"
            valuePropName="checked"
            tooltip="在后台异步提取元数据，不阻塞下载流程"
          >
            <Switch />
          </Form.Item>

          {/* 存储清理 */}
          <Title level={5} style={{ marginTop: 32 }}>存储清理</Title>
          <Divider />

          <Form.Item
            label="启用自动清理"
            name="auto_cleanup_enabled"
            valuePropName="checked"
            tooltip="自动清理过期的临时文件"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="临时文件保留天数"
            name="auto_cleanup_days"
            tooltip="临时文件保留的天数，超过后自动删除"
            rules={[
              { required: true, message: '请输入保留天数' },
              { type: 'number', min: 1, max: 365, message: '范围: 1-365' },
            ]}
          >
            <InputNumber min={1} max={365} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            label="只清理已归档文件"
            name="cleanup_only_organized"
            valuePropName="checked"
            tooltip="只删除已经归档到目标位置的临时文件"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            label="最大存储容量（GB）"
            name="max_storage_gb"
            tooltip="媒体存储的最大容量限制"
            rules={[
              { required: true, message: '请输入最大存储容量' },
              { type: 'number', min: 1, max: 10000, message: '范围: 1-10000' },
            ]}
          >
            <InputNumber min={1} max={10000} style={{ width: '100%' }} />
          </Form.Item>
        </Form>

        <Alert
          message="配置提示"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              <li>并发下载数过高可能导致网络拥塞或被限速</li>
              <li>元数据提取会占用一定的CPU资源，建议使用轻量级模式</li>
              <li>定期清理临时文件可以节省存储空间</li>
              <li>建议设置合理的存储容量限制，避免磁盘空间不足</li>
            </ul>
          }
          type="warning"
          showIcon
          style={{ marginTop: 24 }}
        />
      </Card>
    </div>
  );
};

export default MediaSettingsPage;

