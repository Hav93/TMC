import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Space, 
  Typography,
  Tabs,
  Switch,
  InputNumber,
  Select,
  message,
  Alert
} from 'antd';
import { 
  SaveOutlined, 
  ExperimentOutlined
} from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { settingsApi } from '../../services/settings';
import { useThemeContext } from '../../theme';
import Pan115Settings from './Pan115Settings';
import MediaSettingsPage from './MediaSettings';
import CloudDrive2Settings from './CloudDrive2Settings';

const { Title, Text } = Typography;
const { Option } = Select;

const SettingsPage: React.FC = () => {
  const { colors } = useThemeContext();
  const [proxyForm] = Form.useForm();
  const [systemForm] = Form.useForm();
  const [activeTab, setActiveTab] = useState('proxy');

  // 获取当前配置
  const { data: currentConfig, isLoading, refetch } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  });

  // 当获取到配置数据时，填充表单
  useEffect(() => {
    if (currentConfig) {
      proxyForm.setFieldsValue({
        enable_proxy: currentConfig.enable_proxy,
        proxy_type: currentConfig.proxy_type,
        proxy_host: currentConfig.proxy_host,
        proxy_port: currentConfig.proxy_port,
        proxy_username: currentConfig.proxy_username,
        proxy_password: currentConfig.proxy_password === '***' ? '' : currentConfig.proxy_password,
      });
      
      systemForm.setFieldsValue({
        api_id: currentConfig.api_id,
        api_hash: currentConfig.api_hash,
        bot_token: currentConfig.bot_token,
        phone_number: currentConfig.phone_number,
        admin_user_ids: currentConfig.admin_user_ids,
        enable_log_cleanup: currentConfig.enable_log_cleanup,
        log_retention_days: currentConfig.log_retention_days,
        log_cleanup_time: currentConfig.log_cleanup_time,
        max_log_size: currentConfig.max_log_size,
      });
    }
  }, [currentConfig, proxyForm, systemForm]);

  // 测试代理连接
  const testProxyMutation = useMutation({
    mutationFn: settingsApi.testProxy,
    onSuccess: (result) => {
      if (result.success) {
        message.success({
          content: result.message || '✅ 代理连接测试成功！',
          duration: 3,  // 3秒后自动关闭
          style: { whiteSpace: 'pre-line', fontSize: '14px' }
        });
      } else {
        message.error({
          content: result.message || '❌ 代理测试失败',
          duration: 5,  // 失败消息显示5秒，方便查看详情
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

  // 保存代理配置
  const saveProxyMutation = useMutation({
    mutationFn: settingsApi.save,
    onSuccess: (data: any) => {
      if (data.requires_client_restart) {
        message.warning({
          content: '✅ 代理配置保存成功！请重启已运行的客户端以使新配置生效。',
          duration: 5,
        });
      } else {
        message.success('✅ 代理配置保存成功');
      }
      refetch();
    },
    onError: (error: any) => {
      message.error(`❌ 保存失败: ${error.message || '未知错误'}`);
    },
  });

  // 保存系统配置
  const saveSystemMutation = useMutation({
    mutationFn: settingsApi.save,
    onSuccess: () => {
      message.success('✅ 系统配置保存成功');
      refetch();
    },
    onError: (error: any) => {
      message.error(`❌ 保存失败: ${error.message || '未知错误'}`);
    },
  });

  const handleTestProxy = () => {
    proxyForm.validateFields().then((values) => {
      if (!values.enable_proxy) {
        message.warning('⚠️ 请先启用代理');
        return;
      }
      testProxyMutation.mutate(values);
    });
  };

  const handleSaveProxy = () => {
    proxyForm.validateFields().then((values) => {
      saveProxyMutation.mutate(values);
    });
  };

  const handleSaveSystem = () => {
    systemForm.validateFields().then((values) => {
      saveSystemMutation.mutate(values);
    });
  };

  if (isLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Text>加载中...</Text>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={2} style={{ marginBottom: '24px' }}>系统设置</Title>
        
        <Alert
          message="Telegram配置已迁移"
          description="Telegram客户端配置功能已迁移到「客户端管理」页面，您可以在那里添加和管理多个Telegram客户端。"
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />
        
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'proxy',
              label: '代理设置',
              children: (
                    <div>
            <Form
              form={proxyForm}
              layout="vertical"
              style={{ maxWidth: 600 }}
            >
              <Alert
                message="代理配置"
                description={
                  <div>
                    <p style={{ marginBottom: '8px' }}>如果您在国内环境使用Telegram，建议配置代理以确保连接稳定。</p>
                    <p style={{ marginBottom: '0', color: colors.info, fontWeight: 'bold' }}>
                      💡 支持 HTTP 和 SOCKS5 代理，推荐使用 SOCKS5 以获得更好的性能
                    </p>
                    <p style={{ marginBottom: '0', marginTop: '8px', fontSize: '12px', color: colors.textTertiary }}>
                      常见代理工具端口 - Clash: HTTP 7890 / SOCKS5 7891, v2rayN: SOCKS5 10808
                    </p>
                  </div>
                }
                type="info"
                showIcon
                style={{ marginBottom: '24px' }}
              />

              <Form.Item
                label="启用代理"
                name="enable_proxy"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="代理类型"
                name="proxy_type"
                tooltip="支持 HTTP 和 SOCKS5，推荐 SOCKS5 以获得更好的性能和稳定性"
              >
                <Select>
                  <Option value="socks5">SOCKS5（推荐）</Option>
                  <Option value="http">HTTP</Option>
                  <Option value="socks4">SOCKS4</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="代理地址"
                name="proxy_host"
                rules={[{ required: proxyForm.getFieldValue('enable_proxy'), message: '请输入代理地址' }]}
              >
                <Input placeholder="例如: 127.0.0.1" />
              </Form.Item>

              <Form.Item
                label="代理端口"
                name="proxy_port"
                rules={[{ required: proxyForm.getFieldValue('enable_proxy'), message: '请输入代理端口' }]}
                tooltip="常见 SOCKS5 端口：Clash 7891, v2rayN 10808, SSR 1080"
              >
                <InputNumber min={1} max={65535} placeholder="SOCKS5 常用: 7891 或 10808" style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="用户名（可选）"
                name="proxy_username"
              >
                <Input placeholder="如果代理需要认证" />
              </Form.Item>

              <Form.Item
                label="密码（可选）"
                name="proxy_password"
              >
                <Input.Password placeholder="如果代理需要认证" />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSaveProxy}
                  loading={saveProxyMutation.isPending}
                >
                  保存配置
                </Button>
                <Button
                  icon={<ExperimentOutlined />}
                  onClick={handleTestProxy}
                  loading={testProxyMutation.isPending}
                >
                  测试连接
                </Button>
              </Space>
            </Form>
                </div>
              ),
            },
            {
              key: 'system',
              label: '系统设置',
              children: (
                <div>
            <Form
              form={systemForm}
              layout="vertical"
              style={{ maxWidth: 600 }}
            >
              <Alert
                message="日志清理配置"
                description="自动清理旧日志文件以节省存储空间"
                type="info"
                showIcon
                style={{ marginBottom: '24px' }}
              />

              <Form.Item
                label="启用日志清理"
                name="enable_log_cleanup"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="日志保留天数"
                name="log_retention_days"
              >
                <InputNumber min={1} max={365} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="清理时间"
                name="log_cleanup_time"
              >
                <Input placeholder="例如: 02:00" />
              </Form.Item>

              <Form.Item
                label="最大日志文件大小（MB）"
                name="max_log_size"
              >
                <InputNumber min={1} max={1000} style={{ width: '100%' }} />
              </Form.Item>

                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                onClick={handleSaveSystem}
                loading={saveSystemMutation.isPending}
                >
                保存配置
                </Button>
            </Form>
                </div>
              ),
            },
            {
              key: 'media',
              label: '媒体配置',
              children: <MediaSettingsPage />,
            },
            {
              key: 'pan115',
              label: '115网盘',
              children: <Pan115Settings />,
            },
            {
              key: 'clouddrive2',
              label: 'CloudDrive2',
              children: <CloudDrive2Settings />,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default SettingsPage;
