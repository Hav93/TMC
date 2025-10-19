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

const Pan115Settings: React.FC = () => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const [qrcodeModalVisible, setQrcodeModalVisible] = useState(false);
  const [qrcodeUrl, setQrcodeUrl] = useState('');
  const [qrcodeToken, setQrcodeToken] = useState('');
  const [qrcodeTokenData, setQrcodeTokenData] = useState<any>(null); // 完整的token数据
  const [qrcodeStatus, setQrcodeStatus] = useState<'waiting' | 'scanned' | 'confirmed' | 'expired'>('waiting');
  const [polling, setPolling] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [useOpenApi, setUseOpenApi] = useState(false); // 是否使用115开放平台API
  const [deviceType, setDeviceType] = useState('qandroid'); // 设备类型

  // 获取配置
  const { data: config, isLoading } = useQuery({
    queryKey: ['pan115Config'],
    queryFn: pan115Api.getConfig,
  });

  // 更新配置
  const updateConfigMutation = useMutation({
    mutationFn: pan115Api.updateConfig,
    onSuccess: () => {
      message.success('115网盘配置已保�?);
      queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
    },
    onError: (error: any) => {
      message.error(`保存失败: ${error.response?.data?.detail || error.message}`);
    },
  });

  // 获取开放平台API二维�?  const getQRCodeMutation = useMutation({
    mutationFn: (appId: string) => pan115Api.getQRCode(appId),
    onSuccess: (data: any) => {
      setQrcodeUrl(data.qrcode_url);
      setQrcodeToken(data.qrcode_token);
      setQrcodeStatus('waiting');
      setQrcodeModalVisible(true);
      startPolling(data.qrcode_token);
      message.success('请使�?15 APP扫码登录');
    },
    onError: (error: any) => {
      console.error('�?获取二维码错误详�?', error);
      console.error('�?响应数据:', error.response?.data);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
      message.error(`获取二维码失�? ${errorMsg}`);
    },
  });

  // 获取常规115二维�?  const getRegularQRCodeMutation = useMutation({
    mutationFn: (deviceType: string) => pan115Api.getRegularQRCode(deviceType),
    onSuccess: (data: any) => {
      setQrcodeUrl(data.qrcode_url);
      setQrcodeToken(data.qrcode_token);
      setQrcodeTokenData(data.qrcode_token_data); // 保存完整的token数据
      setQrcodeStatus('waiting');
      setQrcodeModalVisible(true);
      startPolling(data.qrcode_token_data); // 传递完整数�?      message.success('请使�?15 APP扫码登录');
    },
    onError: (error: any) => {
      console.error('�?获取常规二维码错�?', error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
      message.error(`获取二维码失�? ${errorMsg}`);
    },
  });

  // 测试连接
  const testConnectionMutation = useMutation({
    mutationFn: pan115Api.testConnection,
    onSuccess: (data: any) => {
      message.success(data.message || '连接成功');
    },
    onError: (error: any) => {
      message.error(`连接失败: ${error.response?.data?.detail || error.message}`);
    },
  });

  // 加载配置到表�?  useEffect(() => {
    if (config) {
      form.setFieldsValue({
        pan115_app_id: config.pan115_app_id || '',
        pan115_request_interval: config.pan115_request_interval || 1.0,
      });
    }
  }, [config, form]);

  // 开始轮询二维码状�?  const startPolling = (tokenData: any) => {
    setPolling(true);
    
      const poll = async () => {
      try {
        // 使用常规方式检查状态，传递设备类�?        const result = await pan115Api.checkRegularQRCodeStatus(tokenData, deviceType);
        
        setQrcodeStatus(result.status);

        if (result.status === 'confirmed') {
          // 显示用户信息
          const userInfo = result.user_info || {};
          const userName = userInfo.user_name || userInfo.user_id || '未知用户';
          const vipLevel = userInfo.vip_name || (userInfo.is_vip 
            ? `VIP${userInfo.vip_level || ''} 会员` 
            : '普通用�?);
          
          message.success({
            content: `登录成功！用�? ${userName} (${vipLevel})`,
            duration: 5,
          });
          
          stopPolling();
          setQrcodeModalVisible(false);
          queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
        } else if (result.status === 'expired') {
          message.error('二维码已过期，请重新获取');
          stopPolling();
        } else if (result.status === 'error') {
          message.error(result.message || '检查状态失�?);
          stopPolling();
        }
      } catch (error: any) {
        console.error('轮询二维码状态失�?', error);
        stopPolling();
      }
    };

    // 立即执行一�?    poll();

    // �?秒轮询一�?    pollingTimerRef.current = setInterval(poll, 2000);
  };

  // 停止轮询
  const stopPolling = () => {
    setPolling(false);
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  };

  // 组件卸载时清�?  useEffect(() => {
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

  // 常规扫码登录（步�?�?  const handleQRCodeLogin = async () => {
    try {
      await getRegularQRCodeMutation.mutateAsync(deviceType);
    } catch (error) {
      console.error('扫码登录失败:', error);
    }
  };

  // 激活开放平台API（步�?�?  const handleActivateOpenApi = async () => {
    try {
      const values = await form.validateFields(['pan115_app_id', 'pan115_request_interval']);
      console.log('📝 激活开放平台API，表单�?', values);
      
      // 保存AppID和请求间�?      await updateConfigMutation.mutateAsync(values);
      
      // TODO: 调用后端API，使用现有cookies + AppID自动激活开放平�?      message.success('开放平台API配置已保�?);
    } catch (error) {
      console.error('激活开放平台API失败:', error);
    }
  };

  // 获取二维码状态描�?  const getQRCodeStatusText = () => {
    switch (qrcodeStatus) {
      case 'waiting':
        return '等待扫码...';
      case 'scanned':
        return '已扫码，请在手机上确�?;
      case 'confirmed':
        return '登录成功�?;
      case 'expired':
        return '二维码已过期';
      default:
        return '未知状�?;
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
              测试连接
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
          {config?.is_configured && config?.user_info && (
            <Alert
              message="当前登录用户"
              description={
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <Text strong>用户ID�?/Text>
                    <Text>{config.user_info.user_id}</Text>
                  </div>
                  <div>
                    <Text strong>用户名：</Text>
                    <Text>{config.user_info.user_name || '未设�?}</Text>
                  </div>
                  <div>
                    <Text strong>会员等级�?/Text>
                    <Text>
                      {config.user_info.vip_name || (config.user_info.is_vip 
                        ? `VIP${config.user_info.vip_level || ''} 会员` 
                        : '普通用�?)}
                    </Text>
                  </div>
                  {config.user_info.space && (
                    <>
                      <div>
                        <Text strong>总空间：</Text>
                        <Text>{(config.user_info.space.total / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                      <div>
                        <Text strong>已用空间�?/Text>
                        <Text>{(config.user_info.space.used / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                      <div>
                        <Text strong>剩余空间�?/Text>
                        <Text>{(config.user_info.space.remain / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                    </>
                  )}
                  {config.user_info.email && (
                    <div>
                      <Text strong>邮箱�?/Text>
                      <Text>{config.user_info.email}</Text>
                    </div>
                  )}
                  {config.user_info.mobile && (
                    <div>
                      <Text strong>手机�?/Text>
                      <Text>{config.user_info.mobile}</Text>
                    </div>
                  )}
                </Space>
              }
              type="success"
              icon={<CheckCircleOutlined />}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* 步骤1：扫码登录按�?*/}
          <Form.Item label="步骤1：登�?15账号">
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
                  <Select.Option value="web">🌐 网页�?/Select.Option>
                  <Select.Option value="harmony">🔷 鸿蒙系统</Select.Option>
                  <Select.Option value="alipaymini">💳 支付宝小程序</Select.Option>
                  <Select.Option value="wechatmini">💬 微信小程�?/Select.Option>
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
                <Alert
                  message={`已登录：UID=${config.pan115_user_id}`}
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                />
              )}
            </Space>
          </Form.Item>

          <Divider />

          {/* 步骤2：启用开放平台API（可选） */}
          <Form.Item label="步骤2：启�?15开放平台API（可选）">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <input
                  type="checkbox"
                  id="use-open-api"
                  checked={useOpenApi}
                  onChange={(e) => setUseOpenApi(e.target.checked)}
                  style={{ marginRight: 8 }}
                />
                <label htmlFor="use-open-api">启用115开放平台API（需要AppID�?/label>
              </div>

              {useOpenApi && (
                <>
                  <Form.Item
                    label="115开放平台AppID"
                    name="pan115_app_id"
                    rules={[
                      { required: useOpenApi, message: '请输�?15开放平台AppID' },
                      { pattern: /^\d+$/, message: 'AppID必须是数�? },
                    ]}
                    tooltip="�?15开放平台获取的应用ID"
                    style={{ marginBottom: 8, marginTop: 12 }}
                  >
                    <Input 
                      placeholder="请输入您的AppID（纯数字�? 
                      disabled={isLoading}
                      style={{ maxWidth: 400 }}
                    />
                  </Form.Item>

                  <Form.Item
                    label="API请求间隔（秒�?
                    name="pan115_request_interval"
                    tooltip="避免触发115 API限流，建议设置为1.0�?
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

                  <Button
                    type="primary"
                    onClick={handleActivateOpenApi}
                    loading={updateConfigMutation.isPending}
                    disabled={!config?.pan115_user_id}
                  >
                    激活开放平台API
                  </Button>
                  {!config?.pan115_user_id && (
                    <Alert
                      message="请先完成步骤1的扫码登�?
                      type="warning"
                      showIcon
                      style={{ marginTop: 8 }}
                    />
                  )}
                </>
              )}
            </Space>
          </Form.Item>

          {config?.is_configured && (
            <>
              <Divider />
              <Alert
                message="已配�?15网盘"
                description={
                  <div>
                    <p>User ID: {config.pan115_user_id}</p>
                    <p>User Key: {config.pan115_user_key}</p>
                  </div>
                }
                type="success"
                icon={<CheckCircleOutlined />}
                style={{ marginBottom: 16 }}
              />
            </>
          )}

        </Form>

        {/* 配置说明 - 放在最下面 */}
        <Alert
          message="115网盘配置说明"
          description={
            <div>
              <p><strong>步骤1：扫码登�?15</strong></p>
              <p style={{ marginLeft: 20 }}>�?选择您手机上安装�?15应用对应的设备类�?/p>
              <p style={{ marginLeft: 20 }}>�?点击"扫码登录"按钮，使用对应的115应用扫码</p>
              <p style={{ marginLeft: 20 }}>�?这将获取基础登录凭证（cookies�?/p>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <p><strong>步骤2（可选）：启�?15开放平台API</strong></p>
              <p style={{ marginLeft: 20 }}>�?如需使用开放平台API功能，请启用此选项</p>
              <p style={{ marginLeft: 20 }}>�?�?<Link href="https://www.yuque.com/115yun/open" target="_blank">115开放平�?/Link> 申请AppID</p>
              <p style={{ marginLeft: 20 }}>�?填写AppID后，系统将自动使用已登录的账号激活开放平台API</p>
              <p style={{ marginLeft: 20 }}>�?开放平台API凭证更稳定，有效期更�?/p>
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
                    <Text type="secondary">请使�?15 APP扫描二维�?/Text>
                  )}
                  {qrcodeStatus === 'scanned' && (
                    <Text type="warning">请在手机上点击确认登�?/Text>
                  )}
                  {qrcodeStatus === 'confirmed' && (
                    <Text type="success">登录成功，正在保存凭�?..</Text>
                  )}
                  {qrcodeStatus === 'expired' && (
                    <Button onClick={handleQRCodeLogin}>重新获取二维�?/Button>
                  )}
                </Space>
              </div>
            </>
          ) : (
            <Spin tip="正在获取二维�?.." />
          )}
        </div>
      </Modal>
    </div>
  );
};

export default Pan115Settings;


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
