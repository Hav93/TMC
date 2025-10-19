import React, { useEffect, useState } from 'react';
import {
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Space,
  message,
  Alert,
  Typography,
} from 'antd';
import { SaveOutlined, ExperimentOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clouddrive2SettingsApi } from '../../services/clouddrive2Settings';
import type { CloudDrive2Config } from '../../services/clouddrive2Settings';
import { useThemeContext } from '../../theme';

const { Paragraph, Link } = Typography;

const CloudDrive2Settings: React.FC = () => {
  const { colors } = useThemeContext();
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // 获取CloudDrive2配置
  const { data: config, isLoading } = useQuery({
    queryKey: ['clouddrive2-settings'],
    queryFn: clouddrive2SettingsApi.getConfig,
  });

  const [dirLoading, setDirLoading] = useState(false);
  const [dirOptions, setDirOptions] = useState<{ name: string; path: string }[]>([]);

  // 更新配置
  const updateMutation = useMutation({
    mutationFn: clouddrive2SettingsApi.updateConfig,
    onSuccess: (data) => {
      message.success({
        content: `✅ ${data.message}\n${data.note}`,
        duration: 5,
        style: { whiteSpace: 'pre-line' }
      });
      queryClient.invalidateQueries({ queryKey: ['clouddrive2-settings'] });
    },
    onError: (error: any) => {
      message.error({
        content: error.response?.data?.detail || '保存失败',
        duration: 3
      });
    },
  });

  // 测试连接
  const testMutation = useMutation({
    mutationFn: clouddrive2SettingsApi.testConnection,
    onSuccess: (result) => {
      if (result.success) {
        message.success({
          content: result.message,
          duration: 3,
          style: { whiteSpace: 'pre-line', fontSize: '14px' }
        });
      } else {
        message.error({
          content: result.message,
          duration: 5,
          style: { whiteSpace: 'pre-line' }
        });
      }
    },
    onError: (error: any) => {
      message.error({
        content: error.message || '❌ 测试失败: 未知错误',
        duration: 5,
        style: { whiteSpace: 'pre-line' }
      });
    },
  });

  // 填充表单数据
  useEffect(() => {
    if (config) {
      form.setFieldsValue(config);
    }
  }, [config, form]);

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateMutation.mutateAsync(values as CloudDrive2Config);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 测试连接
  const handleTest = async () => {
    try {
      const values = await form.validateFields();
      
      if (!values.enabled) {
        message.warning('⚠️ 请先启用CloudDrive2');
        return;
      }
      
      await testMutation.mutateAsync(values as CloudDrive2Config);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handleBrowse = async () => {
    try {
      const values = form.getFieldsValue();
      if (!values.host || !values.port) {
        message.warning('请先填写主机和端口');
        return;
      }
      setDirLoading(true);
      const browsePath: string = values.mount_point || '/';
      const res = await clouddrive2SettingsApi.browse({
        host: values.host,
        port: values.port,
        username: values.username,
        password: values.password,
        path: browsePath,
      });
      setDirOptions(res?.items || []);
      if (!res?.success) message.warning('目录浏览失败');
    } catch (e) {
      message.error('目录浏览失败');
    } finally {
      setDirLoading(false);
    }
  };

  if (isLoading) {
    return <div style={{ padding: '24px', textAlign: 'center' }}>加载中...</div>;
  }

  return (
    <div>
      <Alert
        message="CloudDrive2 配置说明"
        description={
          <div>
            <Paragraph style={{ marginBottom: '8px' }}>
              CloudDrive2 是一个云存储挂载工具，用于解决115网盘上传签名问题，支持大文件和断点续传。
            </Paragraph>
            <Paragraph style={{ marginBottom: '8px' }}>
              <strong>安装指南：</strong>
            </Paragraph>
            <ul style={{ marginBottom: '8px', paddingLeft: '24px' }}>
              <li>下载并安装 CloudDrive2：<Link href="https://www.clouddrive2.com/" target="_blank">官网下载</Link></li>
              <li>在 CloudDrive2 中添加115网盘账号并挂载</li>
              <li>记录挂载点路径（如：/CloudNAS/115）</li>
              <li>配置 gRPC API 地址和端口（默认：localhost:19798）</li>
            </ul>
            <Paragraph style={{ marginBottom: '0', color: colors.info, fontWeight: 'bold' }}>
              💡 确保 CloudDrive2 服务正在运行，并且gRPC API已启用
            </Paragraph>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />

      <Form
        form={form}
        layout="vertical"
        style={{ maxWidth: 600 }}
      >
        <Form.Item
          label="启用CloudDrive2上传"
          name="enabled"
          valuePropName="checked"
          tooltip="启用后，文件上传将通过CloudDrive2进行"
        >
          <Switch />
        </Form.Item>

        <Form.Item
          label="主机地址"
          name="host"
          rules={[{ required: true, message: '请输入主机地址' }]}
          tooltip="CloudDrive2 gRPC服务地址"
        >
          <Input placeholder="例如: localhost" />
        </Form.Item>

        <Form.Item
          label="端口"
          name="port"
          rules={[{ required: true, message: '请输入端口' }]}
          tooltip="CloudDrive2 gRPC服务端口"
        >
          <InputNumber min={1} max={65535} placeholder="默认: 19798" style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="用户名（可选）"
          name="username"
          tooltip="如果启用了gRPC认证，请填写用户名"
        >
          <Input placeholder="CloudDrive2用户名" />
        </Form.Item>

        <Form.Item
          label="密码（可选）"
          name="password"
          tooltip="如果启用了gRPC认证，请填写密码"
        >
          <Input.Password placeholder="CloudDrive2密码" />
        </Form.Item>

        <Form.Item
          label="挂载点路径"
          name="mount_point"
          rules={[{ required: true, message: '请选择或输入挂载点路径' }]}
          tooltip="从 CloudDrive2 返回的目录中选择，或手动输入"
        >
          <Input placeholder="例如: /115open" addonAfter={<Button loading={dirLoading} onClick={handleBrowse}>浏览</Button>} />
        </Form.Item>

        {/* 单独的浏览按钮，确保在某些主题/布局下也可见 */}
        <Form.Item>
          <Button onClick={handleBrowse} loading={dirLoading}>浏览目录</Button>
        </Form.Item>

        {dirOptions?.length > 0 && (
          <Form.Item label="可选目录">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {dirOptions.map((d) => (
                <Button key={d.path} size="small" onClick={() => form.setFieldsValue({ mount_point: d.path })}>
                  {d.path}
                </Button>
              ))}
            </div>
          </Form.Item>
        )}

        <Space>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={updateMutation.isPending}
          >
            保存配置
          </Button>
          <Button
            icon={<ExperimentOutlined />}
            onClick={handleTest}
            loading={testMutation.isPending}
          >
            测试连接
          </Button>
        </Space>
      </Form>
    </div>
  );
};

export default CloudDrive2Settings;

