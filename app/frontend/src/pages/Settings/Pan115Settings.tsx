/**
 * 115网盘配置页面
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  message,
  Space,
  Modal,
  QRCode,
  Typography,
  Alert,
  Spin,
  InputNumber,
  Divider,
  Select,
  Switch,
} from 'antd';
import {
  QrcodeOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import pan115Api from '../../services/pan115';

const { Text, Link } = Typography;

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

const Pan115Settings: React.FC = () => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const [qrcodeModalVisible, setQrcodeModalVisible] = useState(false);
  const [qrcodeUrl, setQrcodeUrl] = useState('');
  const [qrcodeToken, setQrcodeToken] = useState<any>(null);
  const [qrcodeTokenData, setQrcodeTokenData] = useState<any>(null);
  const [qrcodeStatus, setQrcodeStatus] = useState<'waiting' | 'scanned' | 'confirmed' | 'expired' | 'error'>('waiting');
  const [polling, setPolling] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingCountRef = useRef<number>(0); // 轮询次数计数器
  const maxPollingCount = 150; // 最大轮询次数（150次 * 2秒 = 5分钟）
  const [useOpenApi, setUseOpenApi] = useState(false); // 是否使用115开放平台API
  const [openApiActivated, setOpenApiActivated] = useState(false); // 开放平台API是否已激活
  const [deviceType, setDeviceType] = useState('qandroid'); // 设备类型
  const [currentLoginDeviceType, setCurrentLoginDeviceType] = useState('qandroid'); // 当前登录使用的设备类型
  
  // OAuth 2.0 Device Code Flow状态
  const [authModalVisible, setAuthModalVisible] = useState(false);
  const [authUserCode, setAuthUserCode] = useState('');
  const [authVerificationUri, setAuthVerificationUri] = useState('');
  const [authDeviceCode, setAuthDeviceCode] = useState('');
  const [authCodeVerifier, setAuthCodeVerifier] = useState('');
  const [authQrcodeToken, setAuthQrcodeToken] = useState<any>(null);
  const [authPolling, setAuthPolling] = useState(false);
  const [authStatus, setAuthStatus] = useState<'pending' | 'authorized' | 'error' | 'expired'>('pending');
  const authPollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const authPollingCountRef = useRef<number>(0);

  // 获取配置
  const { data: config, isLoading } = useQuery({
    queryKey: ['pan115Config'],
    queryFn: pan115Api.getConfig,
  });

  // 当配置加载完成后，更新设备类型和激活状态
  useEffect(() => {
    if (config?.pan115_device_type) {
      setDeviceType(config.pan115_device_type);
    }
    // 同步后端的激活状态到前端
    if (config?.open_api_activated !== undefined) {
      setOpenApiActivated(config.open_api_activated);
    }
  }, [config]);

  // 更新配置
  const updateConfigMutation = useMutation({
    mutationFn: pan115Api.updateConfig,
    onSuccess: () => {
      message.success('115网盘配置已保存');
      queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
    },
    onError: (error) => {
      const err = error as any;
      message.error(`保存失败: ${err.response?.data?.detail || err.message}`);
    },
  });

  // 获取常规115二维码
  const getRegularQRCodeMutation = useMutation({
    mutationFn: (deviceType: string) => pan115Api.getRegularQRCode(deviceType),
    onSuccess: (data: any) => {
      console.log('✅ 获取二维码成功，返回数据:', data);
      console.log('  - qrcode_url:', data.qrcode_url);
      console.log('  - qrcode_token:', data.qrcode_token);
      console.log('  - app:', data.app);
      console.log('  - device_type:', data.device_type);
      
      // 立即设置状态并显示Modal，不等待第一次状态检查
      setQrcodeUrl(data.qrcode_url);
      setQrcodeToken(data.qrcode_token);
      setQrcodeTokenData(data.qrcode_token);
      setCurrentLoginDeviceType(data.device_type || deviceType);
      setQrcodeStatus('waiting');
      setQrcodeModalVisible(true); // 立即显示Modal
      
      // 延迟启动轮询，让Modal先渲染
      setTimeout(() => {
        startPolling(data.qrcode_token, data.device_type || deviceType);
      }, 500);
      
      // 根据是否使用开放平台二维码给出不同提示
      if (data.app === 'openapi') {
        message.success({
          content: '📱 使用开放平台二维码（扫码后自动绑定AppID）',
          duration: 4,
        });
      } else {
        message.success('请使用115 APP扫码登录');
      }
    },
    onError: (error) => {
      const err = error as any;
      console.error('❌ 获取常规二维码错误:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || '未知错误';
      message.error(`获取二维码失败: ${errorMsg}`);
    },
  });

  // 测试cookies可用性
  const testCookiesMutation = useMutation({
    mutationFn: pan115Api.testCookies,
    onSuccess: (data) => {
      if (data.success) {
        message.success({
          content: data.message || '✅ Cookies可用',
          duration: 5,
          style: { whiteSpace: 'pre-line' }
        });
        queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
      }
    },
    onError: (error) => {
      const err = error as any;
      const errorMsg = err.response?.data?.detail || err.message || '测试失败';
      message.error({
        content: `❌ ${errorMsg}`,
        duration: 5,
        style: { whiteSpace: 'pre-line' }
      });
    },
  });

  // 测试连接并刷新用户信息
  const testConnectionMutation = useMutation({
    mutationFn: pan115Api.refreshUserInfo,
    onSuccess: (data) => {
      if (data.from_cache) {
        message.warning({
          content: (
            <div>
              <div>⚠️ {data.message || 'API调用失败,使用缓存数据'}</div>
              <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                提示: 115服务器限流,显示的是上次成功获取的数据
              </div>
            </div>
          ),
          duration: 5,
        });
      } else {
        message.success(data.message || '✅ 用户信息已刷新');
      }
      // 刷新配置数据
      queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
    },
    onError: (error) => {
      const err = error as any;
      message.error(`刷新失败: ${err.response?.data?.detail || err.message}`);
    },
  });

  // 加载配置到表单
  useEffect(() => {
    if (config) {
      form.setFieldsValue({
        pan115_app_id: config.pan115_app_id || '',
        pan115_request_interval: config.pan115_request_interval || 1.0,
      });
    }
  }, [config, form]);

  // 开始轮询二维码状态
  const startPolling = (tokenData: any, loginDeviceType?: string) => {
    setPolling(true);
    pollingCountRef.current = 0; // 重置计数器
    const deviceTypeForPolling = loginDeviceType || currentLoginDeviceType; // 使用传入的设备类型或当前登录设备类型
    
    const poll = async () => {
      try {
        pollingCountRef.current += 1;
        
        // 检查是否超时（5分钟）
        if (pollingCountRef.current > maxPollingCount) {
          console.log('二维码已超时，自动刷新...');
          message.warning('二维码已过期，正在自动刷新...');
          stopPolling();
          // 自动重新获取二维码
          await handleQRCodeLogin();
          return;
        }
        
        // 使用常规方式检查状态，传递保存的设备类型
        const result = await pan115Api.checkRegularQRCodeStatus(tokenData, deviceTypeForPolling);
        
        setQrcodeStatus(result.status);

        if (result.status === 'confirmed') {
          // 显示用户信息
          const userInfo = result.user_info || {};
          const userName = userInfo.user_name || userInfo.user_id || '未知用户';
          const vipLevel = userInfo.vip_name || (userInfo.is_vip 
            ? `VIP${userInfo.vip_level || ''} 会员` 
            : '普通用户');
          
          message.success({
            content: `登录成功！用户: ${userName} (${vipLevel})`,
            duration: 5,
          });
          
          stopPolling();
          setQrcodeModalVisible(false);
          queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
        } else if (result.status === 'expired') {
          message.warning('二维码已过期，正在自动刷新...');
          stopPolling();
          // 自动重新获取二维码
          await handleQRCodeLogin();
        } else if (result.status === 'error') {
          console.error('检查状态错误:', result.message);
          // 不停止轮询，继续尝试
        }
      } catch (error: any) {
        console.error('轮询二维码状态失败:', error);
        // 不停止轮询，继续尝试
      }
    };

    // 立即执行一次
    poll();

    // 每2秒轮询一次
    pollingTimerRef.current = setInterval(poll, 2000);
  };

  // 停止轮询
  const stopPolling = () => {
    setPolling(false);
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  };

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateConfigMutation.mutateAsync(values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 常规扫码登录（步骤1）
  const handleQRCodeLogin = async () => {
    try {
      await getRegularQRCodeMutation.mutateAsync(deviceType);
    } catch (error) {
      console.error('扫码登录失败:', error);
    }
  };

  // 激活开放平台API - 直接用cookies激活
  const activateOpenApiMutation = useMutation({
    mutationFn: pan115Api.activateOpenApi,
    onSuccess: (data: any) => {
      if (data.success) {
        setOpenApiActivated(true);
        
        if (data.has_space_info) {
          message.success({
            content: data.message || '✅ 开放平台API已激活！',
            duration: 4,
          });
        } else {
          message.warning({
            content: data.message || '⚠️ API已激活，但空间信息需要稍后刷新',
            duration: 5,
          });
        }
        
        // 刷新配置
        queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
      }
    },
    onError: (error) => {
      const err = error as any;
      setOpenApiActivated(false);
      const errorMsg = err.response?.data?.detail || err.message || '获取授权码失败';
      message.error({
        content: `❌ ${errorMsg}`,
        duration: 5,
        style: { whiteSpace: 'pre-line' }
      });
    },
  });

  // 轮询获取访问令牌
  const pollDeviceTokenMutation = useMutation({
    mutationFn: ({ deviceCode, codeVerifier, qrcodeToken }: { deviceCode: string; codeVerifier: string; qrcodeToken?: any }) =>
      pan115Api.pollDeviceToken(deviceCode, codeVerifier, qrcodeToken),
    onSuccess: (data: any) => {
      if (data.success && data.status === 'authorized') {
        // 授权成功
        setAuthStatus('authorized');
        stopAuthPolling();
        setOpenApiActivated(true);
        
        message.success({
          content: '✅ 开放平台API授权成功！',
          duration: 3,
        });
        
        // 刷新配置
        queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
        
        // 2秒后关闭弹窗
        setTimeout(() => {
          setAuthModalVisible(false);
        }, 2000);
      } else if (data.status === 'pending') {
        // 继续等待
        setAuthStatus('pending');
      } else if (data.status === 'error' || data.status === 'expired') {
        // 错误或过期
        setAuthStatus(data.status);
        stopAuthPolling();
        message.error({
          content: data.message || '授权失败',
          duration: 5,
        });
      }
    },
    onError: (error) => {
      const err = error as any;
      console.error('轮询错误:', err);
      // 轮询失败不显示错误,继续等待下次轮询
    },
  });

  // 开始OAuth授权轮询
  const startAuthPolling = (deviceCode: string, codeVerifier: string, qrcodeToken: any, interval: number = 2) => {
    stopAuthPolling(); // 先停止之前的轮询
    setAuthPolling(true);
    authPollingCountRef.current = 0;
    
    const maxCount = 150; // 最大轮询次数 (150次 * 2秒 = 5分钟)
    
    const poll = () => {
      authPollingCountRef.current += 1;
      
      if (authPollingCountRef.current > maxCount) {
        stopAuthPolling();
        setAuthStatus('expired');
        message.error('二维码已过期,请重新激活');
        return;
      }
      
      pollDeviceTokenMutation.mutate({ deviceCode, codeVerifier, qrcodeToken });
      
      authPollingTimerRef.current = setTimeout(poll, interval * 1000);
    };
    
    // 立即执行第一次轮询
    poll();
  };

  // 停止OAuth授权轮询
  const stopAuthPolling = () => {
    if (authPollingTimerRef.current) {
      clearTimeout(authPollingTimerRef.current);
      authPollingTimerRef.current = null;
    }
    setAuthPolling(false);
  };

  // 组件卸载时清理OAuth轮询
  useEffect(() => {
    return () => {
      stopAuthPolling();
    };
  }, []);

  const handleOpenApiToggle = async (checked: boolean) => {
    if (!checked) {
      // 关闭开放平台API
      setOpenApiActivated(false);
      message.info('已关闭开放平台API');
      return;
    }

    // 激活开放平台API
    try {
      const values = await form.validateFields(['pan115_app_id', 'pan115_request_interval']);
      console.log('📝 激活开放平台API，表单值:', values);
      
      // 1. 先保存AppID和请求间隔
      await updateConfigMutation.mutateAsync(values);
      
      // 2. 调用后端API激活开放平台
      activateOpenApiMutation.mutate();
    } catch (error) {
      console.error('激活开放平台API失败:', error);
      setOpenApiActivated(false);
    }
  };

  // 获取二维码状态描述
  const getQRCodeStatusText = () => {
    switch (qrcodeStatus) {
      case 'waiting':
        return '等待扫码...';
      case 'scanned':
        return '已扫码，请在手机上确认';
      case 'confirmed':
        return '登录成功！';
      case 'expired':
        return '二维码已过期';
      default:
        return '未知状态';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <Space>
            <QrcodeOutlined />
            <span>115网盘配置</span>
          </Space>
        }
        extra={
          config?.is_configured && (
            <Button
              icon={<SyncOutlined />}
              onClick={() => testConnectionMutation.mutate()}
              loading={testConnectionMutation.isPending}
            >
              刷新信息
            </Button>
          )
        }
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            pan115_request_interval: 1.0,
          }}
        >
          {/* 显示当前登录用户信息 */}
          {config?.pan115_user_id && (
            <Alert
              message={
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                    <CheckCircleOutlined style={{ fontSize: 18, color: '#52c41a', marginRight: 8 }} />
                    <Text strong style={{ fontSize: 15 }}>115网盘账号已连接</Text>
                  </div>
                  
                  <Space direction="vertical" style={{ width: '100%' }} size={8}>
                    {/* 用户信息行 */}
                    <div style={{ 
                      display: 'grid', 
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                      gap: '12px 24px',
                      padding: '8px 0',
                      borderTop: '1px solid rgba(82, 196, 26, 0.2)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <Text type="secondary" style={{ minWidth: 70 }}>用户ID</Text>
                        <Text strong>{config.user_info?.user_id || config.pan115_user_id}</Text>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <Text type="secondary" style={{ minWidth: 70 }}>会员等级</Text>
                        <Text strong style={{ color: config.user_info?.is_vip ? '#ff9800' : '#666' }}>
                          {config.user_info?.vip_name || (config.user_info?.is_vip ? `VIP${config.user_info?.vip_level || ''} 会员` : '普通用户')}
                        </Text>
                      </div>
                      {config.user_info?.mobile && (
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <Text type="secondary" style={{ minWidth: 70 }}>绑定手机</Text>
                          <Text>{config.user_info.mobile}</Text>
                        </div>
                      )}
                    </div>

                    {/* 空间信息行 */}
                    {config.user_info?.space && config.user_info.space.total > 0 && (
                      <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                        gap: '12px 24px',
                        padding: '8px 0',
                        borderTop: '1px solid rgba(82, 196, 26, 0.2)'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <Text type="secondary" style={{ minWidth: 70 }}>总空间</Text>
                          <Text strong style={{ color: '#1890ff' }}>{formatFileSize(config.user_info.space.total)}</Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <Text type="secondary" style={{ minWidth: 70 }}>已使用</Text>
                          <Text strong>{formatFileSize(config.user_info.space.used)}</Text>
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            ({((config.user_info.space.used / config.user_info.space.total) * 100).toFixed(1)}%)
                          </Text>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <Text type="secondary" style={{ minWidth: 70 }}>剩余</Text>
                          <Text strong style={{ color: '#52c41a' }}>{formatFileSize(config.user_info.space.remain)}</Text>
                        </div>
                      </div>
                    )}

                    {/* 状态标签 */}
                    <div style={{ 
                      display: 'flex', 
                      gap: 12, 
                      flexWrap: 'wrap',
                      padding: '8px 0',
                      borderTop: '1px solid rgba(82, 196, 26, 0.2)'
                    }}>
                      <div style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center',
                        padding: '4px 12px',
                        background: 'rgba(82, 196, 26, 0.1)',
                        borderRadius: 4,
                        fontSize: 12
                      }}>
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 6 }} />
                        <Text style={{ color: '#52c41a', fontWeight: 500 }}>Cookie已保存</Text>
                      </div>
                      {config.open_api_activated && (
                        <div style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center',
                          padding: '4px 12px',
                          background: 'rgba(24, 144, 255, 0.1)',
                          borderRadius: 4,
                          fontSize: 12
                        }}>
                          <CheckCircleOutlined style={{ color: '#1890ff', marginRight: 6 }} />
                          <Text style={{ color: '#1890ff', fontWeight: 500 }}>OpenAPI已激活</Text>
                        </div>
                      )}
                    </div>
                  </Space>
                </div>
              }
              type="success"
              showIcon={false}
              style={{ 
                marginBottom: 16,
                background: 'linear-gradient(135deg, #f6ffed 0%, #f0f9ff 100%)',
                border: '1px solid #b7eb8f',
                borderRadius: 8
              }}
            />
          )}

          {/* 步骤1：扫码登录按钮 */}
          <Form.Item label="步骤1：登录115账号">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Select
                  value={deviceType}
                  onChange={setDeviceType}
                  style={{ width: 260 }}
                  placeholder="选择设备类型"
                >
                  <Select.Option value="qandroid">🤖 115生活 - Android</Select.Option>
                  <Select.Option value="qios">📱 115生活 - iOS</Select.Option>
                  <Select.Option value="android">🤖 115网盘 - Android</Select.Option>
                  <Select.Option value="ios">📱 115网盘 - iOS</Select.Option>
                  <Select.Option value="ipad">📱 115网盘 - iPad</Select.Option>
                  <Select.Option value="web">🌐 网页版</Select.Option>
                  <Select.Option value="harmony">🔷 鸿蒙系统</Select.Option>
                  <Select.Option value="alipaymini">💳 支付宝小程序</Select.Option>
                  <Select.Option value="wechatmini">💬 微信小程序</Select.Option>
                </Select>
                <Button
                  type="primary"
                  icon={<QrcodeOutlined />}
                  onClick={handleQRCodeLogin}
                  loading={getRegularQRCodeMutation.isPending}
                >
                  扫码登录
                </Button>
              </Space>
              {config?.pan115_user_id && (
                <Button
                  onClick={() => testCookiesMutation.mutate()}
                  loading={testCookiesMutation.isPending}
                  icon={<InfoCircleOutlined />}
                  style={{ marginTop: 8 }}
                >
                  检测可用性
                </Button>
              )}
            </Space>
          </Form.Item>

          <Divider />

          {/* 步骤2：启用开放平台API（可选） */}
          <Form.Item label="步骤2：启用115开放平台API（可选）">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <input
                  type="checkbox"
                  id="use-open-api"
                  checked={useOpenApi}
                  onChange={(e) => setUseOpenApi(e.target.checked)}
                  style={{ marginRight: 8 }}
                />
                <label htmlFor="use-open-api">启用115开放平台API（需要AppID）</label>
              </div>

              {useOpenApi && (
                <>
                  <Form.Item
                    label="115开放平台AppID"
                    name="pan115_app_id"
                    rules={[
                      { required: useOpenApi, message: '请输入115开放平台AppID' },
                      { pattern: /^\d+$/, message: 'AppID必须是数字' },
                    ]}
                    tooltip="从115开放平台获取的应用ID"
                    style={{ marginBottom: 8, marginTop: 12 }}
                  >
                    <Input 
                      placeholder="请输入您的AppID（纯数字）" 
                      disabled={isLoading}
                      style={{ maxWidth: 400 }}
                    />
                  </Form.Item>

                  <Form.Item
                    label="115开放平台AppSecret"
                    name="pan115_app_secret"
                    rules={[
                      { required: useOpenApi, message: '请输入115开放平台AppSecret' },
                    ]}
                    tooltip="从115开放平台获取的应用密钥，用于API签名验证"
                    style={{ marginBottom: 8 }}
                  >
                    <Input.Password 
                      placeholder="请输入您的AppSecret" 
                      disabled={isLoading}
                      style={{ maxWidth: 400 }}
                      autoComplete="off"
                    />
                  </Form.Item>

                  <Form.Item
                    label="API请求间隔（秒）"
                    name="pan115_request_interval"
                    tooltip="避免触发115 API限流，建议设置为1.0秒"
                    style={{ marginBottom: 8 }}
                  >
                    <InputNumber
                      min={0.5}
                      max={10}
                      step={0.5}
                      disabled={isLoading}
                      style={{ width: 200 }}
                    />
                  </Form.Item>

                  <Form.Item
                    label="使用代理"
                    name="pan115_use_proxy"
                    valuePropName="checked"
                    tooltip="115是国内服务,通常不需要代理。仅当您的网络环境需要通过代理访问115时才启用"
                    style={{ marginBottom: 8 }}
                  >
                    <Switch 
                      disabled={isLoading}
                      checkedChildren="是"
                      unCheckedChildren="否"
                    />
                  </Form.Item>

                  <Form.Item label="是否启用OPENAPI">
                    <Space align="center">
                      <Switch
                        checked={openApiActivated}
                        onChange={handleOpenApiToggle}
                        loading={activateOpenApiMutation.isPending || updateConfigMutation.isPending}
                        disabled={!config?.pan115_user_id || !form.getFieldValue('pan115_app_id')}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                      {openApiActivated && (
                        <Text type="success" style={{ marginLeft: 8 }}>
                          <CheckCircleOutlined /> 已激活
                        </Text>
                      )}
                      {!openApiActivated && config?.pan115_user_id && form.getFieldValue('pan115_app_id') && (
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          未激活
                        </Text>
                      )}
                    </Space>
                  </Form.Item>
                  
                  {!config?.pan115_user_id && (
                    <Alert
                      message="请先完成步骤1的扫码登录"
                      type="warning"
                      showIcon
                      style={{ marginTop: 8 }}
                    />
                  )}
                  
                  {config?.pan115_user_id && !form.getFieldValue('pan115_app_id') && (
                    <Alert
                      message="请先填写AppID"
                      type="info"
                      showIcon
                      style={{ marginTop: 8 }}
                    />
                  )}
                  
                  {openApiActivated && (
                    <Alert
                      message="✅ 开放平台API工作流程"
                      description={
                        <div style={{ fontSize: '13px' }}>
                          <p>1️⃣ 扫码登录获取 cookies → 保存到 /config/115-cookies.txt</p>
                          <p>2️⃣ 输入AppID并启用开关 → 系统用 cookies + AppID 获取 access_token</p>
                          <p>3️⃣ 使用 access_token 调用开放平台API → 获取更稳定的空间信息</p>
                        </div>
                      }
                      type="info"
                      showIcon
                      style={{ marginTop: 12 }}
                    />
                  )}
                </>
              )}
            </Space>
          </Form.Item>

        </Form>

        {/* 配置说明 - 放在最下面 */}
        <Alert
          message="115网盘配置说明"
          description={
            <div>
              <p><strong>步骤1：扫码登录115</strong></p>
              <p style={{ marginLeft: 20 }}>• 选择您手机上安装的115应用对应的设备类型</p>
              <p style={{ marginLeft: 20 }}>• 点击"扫码登录"按钮，使用对应的115应用扫码</p>
              <p style={{ marginLeft: 20 }}>• 这将获取基础登录凭证（cookies）</p>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <p><strong>步骤2（可选）：启用115开放平台API</strong></p>
              <p style={{ marginLeft: 20 }}>• 如需使用开放平台API功能，请启用此选项</p>
              <p style={{ marginLeft: 20 }}>• 在 <Link href="https://www.yuque.com/115yun/open" target="_blank">115开放平台</Link> 申请AppID</p>
              <p style={{ marginLeft: 20 }}>• 填写AppID后，系统将自动使用已登录的账号激活开放平台API</p>
              <p style={{ marginLeft: 20 }}>• 开放平台API凭证更稳定，有效期更长</p>
            </div>
          }
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginTop: 24 }}
        />
      </Card>

      {/* 二维码Modal */}
      <Modal
        title="115网盘扫码登录"
        open={qrcodeModalVisible}
        onCancel={() => {
          setQrcodeModalVisible(false);
          stopPolling();
        }}
        footer={null}
        width={400}
        centered
      >
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          {qrcodeUrl ? (
            <>
              <div style={{ 
                display: 'inline-block', 
                padding: '16px', 
                backgroundColor: '#ffffff',
                borderRadius: '8px'
              }}>
                <QRCode 
                  value={qrcodeUrl} 
                  size={200}
                  color="#000000"
                  bgColor="#ffffff"
                />
              </div>
              <div style={{ marginTop: 24 }}>
                <Space direction="vertical" align="center">
                  <Text strong style={{ fontSize: 16 }}>
                    {polling ? (
                      <Space>
                        <Spin size="small" />
                        {getQRCodeStatusText()}
                      </Space>
                    ) : (
                      getQRCodeStatusText()
                    )}
                  </Text>
                  {qrcodeStatus === 'waiting' && (
                    <Text type="secondary">请使用115 APP扫描二维码</Text>
                  )}
                  {qrcodeStatus === 'scanned' && (
                    <Text type="warning">请在手机上点击确认登录</Text>
                  )}
                  {qrcodeStatus === 'confirmed' && (
                    <Text type="success">登录成功，正在保存凭据...</Text>
                  )}
                  {qrcodeStatus === 'expired' && (
                    <Button onClick={handleQRCodeLogin}>重新获取二维码</Button>
                  )}
                </Space>
              </div>
            </>
          ) : (
            <Spin tip="正在获取二维码..." />
          )}
        </div>
      </Modal>

      {/* OAuth 2.0 授权Modal */}
      <Modal
        title="115开放平台授权"
        open={authModalVisible}
        onCancel={() => {
          stopAuthPolling();
          setAuthModalVisible(false);
        }}
        footer={[
          <Button key="cancel" onClick={() => {
            stopAuthPolling();
            setAuthModalVisible(false);
          }}>
            {authStatus === 'authorized' ? '关闭' : '取消'}
          </Button>,
        ]}
        width={500}
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          {authStatus === 'pending' && (
            <>
              <Alert
                message="请使用115 APP扫描二维码"
                description="扫码后将自动激活开放平台API并获取访问令牌"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />
              
              {/* 二维码 */}
              <div style={{ 
                background: '#f5f5f5', 
                padding: '24px', 
                borderRadius: '8px',
                marginBottom: 24,
                display: 'flex',
                justifyContent: 'center'
              }}>
                {authVerificationUri && (
                  <QRCode
                    value={authVerificationUri}
                    size={200}
                    style={{ border: '8px solid white' }}
                  />
                )}
              </div>

              <Space direction="vertical" align="center" size="small">
                <Spin />
                <Text type="secondary">
                  等待扫码中... ({authPollingCountRef.current}/150)
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  使用与登录时相同的115 APP扫码
                </Text>
              </Space>
            </>
          )}

          {authStatus === 'authorized' && (
            <Space direction="vertical" align="center" size="large">
              <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a' }} />
              <Text style={{ fontSize: 18 }}>授权成功！</Text>
              <Text type="secondary">开放平台API已激活,即将关闭...</Text>
            </Space>
          )}

          {authStatus === 'error' && (
            <Space direction="vertical" align="center" size="large">
              <Alert
                message="授权失败"
                description="请检查网络连接或重试"
                type="error"
                showIcon
              />
              <Button type="primary" onClick={() => setAuthModalVisible(false)}>
                关闭
              </Button>
            </Space>
          )}

          {authStatus === 'expired' && (
            <Space direction="vertical" align="center" size="large">
              <Alert
                message="授权超时"
                description="授权码已过期,请重新激活"
                type="warning"
                showIcon
              />
              <Button type="primary" onClick={() => {
                setAuthModalVisible(false);
                handleOpenApiToggle(true);
              }}>
                重新激活
              </Button>
            </Space>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Pan115Settings;

