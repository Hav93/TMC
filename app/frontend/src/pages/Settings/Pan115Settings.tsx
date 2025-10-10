/**
 * 115缃戠洏閰嶇疆椤甸潰
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
  const [qrcodeTokenData, setQrcodeTokenData] = useState<any>(null); // 瀹屾暣鐨則oken鏁版嵁
  const [qrcodeStatus, setQrcodeStatus] = useState<'waiting' | 'scanned' | 'confirmed' | 'expired'>('waiting');
  const [polling, setPolling] = useState(false);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [useOpenApi, setUseOpenApi] = useState(false); // 鏄惁浣跨敤115寮€鏀惧钩鍙癆PI
  const [deviceType, setDeviceType] = useState('qandroid'); // 璁惧绫诲瀷

  // 鑾峰彇閰嶇疆
  const { data: config, isLoading } = useQuery({
    queryKey: ['pan115Config'],
    queryFn: pan115Api.getConfig,
  });

  // 鏇存柊閰嶇疆
  const updateConfigMutation = useMutation({
    mutationFn: pan115Api.updateConfig,
    onSuccess: () => {
      message.success('115缃戠洏閰嶇疆宸蹭繚瀛?);
      queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
    },
    onError: (error: any) => {
      message.error(`淇濆瓨澶辫触: ${error.response?.data?.detail || error.message}`);
    },
  });

  // 鑾峰彇寮€鏀惧钩鍙癆PI浜岀淮鐮?  const getQRCodeMutation = useMutation({
    mutationFn: (appId: string) => pan115Api.getQRCode(appId),
    onSuccess: (data: any) => {
      setQrcodeUrl(data.qrcode_url);
      setQrcodeToken(data.qrcode_token);
      setQrcodeStatus('waiting');
      setQrcodeModalVisible(true);
      startPolling(data.qrcode_token);
      message.success('璇蜂娇鐢?15 APP鎵爜鐧诲綍');
    },
    onError: (error: any) => {
      console.error('鉂?鑾峰彇浜岀淮鐮侀敊璇鎯?', error);
      console.error('鉂?鍝嶅簲鏁版嵁:', error.response?.data);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '鏈煡閿欒';
      message.error(`鑾峰彇浜岀淮鐮佸け璐? ${errorMsg}`);
    },
  });

  // 鑾峰彇甯歌115浜岀淮鐮?  const getRegularQRCodeMutation = useMutation({
    mutationFn: (deviceType: string) => pan115Api.getRegularQRCode(deviceType),
    onSuccess: (data: any) => {
      setQrcodeUrl(data.qrcode_url);
      setQrcodeToken(data.qrcode_token);
      setQrcodeTokenData(data.qrcode_token_data); // 淇濆瓨瀹屾暣鐨則oken鏁版嵁
      setQrcodeStatus('waiting');
      setQrcodeModalVisible(true);
      startPolling(data.qrcode_token_data); // 浼犻€掑畬鏁存暟鎹?      message.success('璇蜂娇鐢?15 APP鎵爜鐧诲綍');
    },
    onError: (error: any) => {
      console.error('鉂?鑾峰彇甯歌浜岀淮鐮侀敊璇?', error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '鏈煡閿欒';
      message.error(`鑾峰彇浜岀淮鐮佸け璐? ${errorMsg}`);
    },
  });

  // 娴嬭瘯杩炴帴
  const testConnectionMutation = useMutation({
    mutationFn: pan115Api.testConnection,
    onSuccess: (data: any) => {
      message.success(data.message || '杩炴帴鎴愬姛');
    },
    onError: (error: any) => {
      message.error(`杩炴帴澶辫触: ${error.response?.data?.detail || error.message}`);
    },
  });

  // 鍔犺浇閰嶇疆鍒拌〃鍗?  useEffect(() => {
    if (config) {
      form.setFieldsValue({
        pan115_app_id: config.pan115_app_id || '',
        pan115_request_interval: config.pan115_request_interval || 1.0,
      });
    }
  }, [config, form]);

  // 寮€濮嬭疆璇簩缁寸爜鐘舵€?  const startPolling = (tokenData: any) => {
    setPolling(true);
    
      const poll = async () => {
      try {
        // 浣跨敤甯歌鏂瑰紡妫€鏌ョ姸鎬侊紝浼犻€掕澶囩被鍨?        const result = await pan115Api.checkRegularQRCodeStatus(tokenData, deviceType);
        
        setQrcodeStatus(result.status);

        if (result.status === 'confirmed') {
          // 鏄剧ず鐢ㄦ埛淇℃伅
          const userInfo = result.user_info || {};
          const userName = userInfo.user_name || userInfo.user_id || '鏈煡鐢ㄦ埛';
          const vipLevel = userInfo.vip_name || (userInfo.is_vip 
            ? `VIP${userInfo.vip_level || ''} 浼氬憳` 
            : '鏅€氱敤鎴?);
          
          message.success({
            content: `鐧诲綍鎴愬姛锛佺敤鎴? ${userName} (${vipLevel})`,
            duration: 5,
          });
          
          stopPolling();
          setQrcodeModalVisible(false);
          queryClient.invalidateQueries({ queryKey: ['pan115Config'] });
        } else if (result.status === 'expired') {
          message.error('浜岀淮鐮佸凡杩囨湡锛岃閲嶆柊鑾峰彇');
          stopPolling();
        } else if (result.status === 'error') {
          message.error(result.message || '妫€鏌ョ姸鎬佸け璐?);
          stopPolling();
        }
      } catch (error: any) {
        console.error('杞浜岀淮鐮佺姸鎬佸け璐?', error);
        stopPolling();
      }
    };

    // 绔嬪嵆鎵ц涓€娆?    poll();

    // 姣?绉掕疆璇竴娆?    pollingTimerRef.current = setInterval(poll, 2000);
  };

  // 鍋滄杞
  const stopPolling = () => {
    setPolling(false);
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  };

  // 缁勪欢鍗歌浇鏃舵竻鐞?  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  // 淇濆瓨閰嶇疆
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await updateConfigMutation.mutateAsync(values);
    } catch (error) {
      console.error('琛ㄥ崟楠岃瘉澶辫触:', error);
    }
  };

  // 甯歌鎵爜鐧诲綍锛堟楠?锛?  const handleQRCodeLogin = async () => {
    try {
      await getRegularQRCodeMutation.mutateAsync(deviceType);
    } catch (error) {
      console.error('鎵爜鐧诲綍澶辫触:', error);
    }
  };

  // 婵€娲诲紑鏀惧钩鍙癆PI锛堟楠?锛?  const handleActivateOpenApi = async () => {
    try {
      const values = await form.validateFields(['pan115_app_id', 'pan115_request_interval']);
      console.log('馃摑 婵€娲诲紑鏀惧钩鍙癆PI锛岃〃鍗曞€?', values);
      
      // 淇濆瓨AppID鍜岃姹傞棿闅?      await updateConfigMutation.mutateAsync(values);
      
      // TODO: 璋冪敤鍚庣API锛屼娇鐢ㄧ幇鏈塩ookies + AppID鑷姩婵€娲诲紑鏀惧钩鍙?      message.success('寮€鏀惧钩鍙癆PI閰嶇疆宸蹭繚瀛?);
    } catch (error) {
      console.error('婵€娲诲紑鏀惧钩鍙癆PI澶辫触:', error);
    }
  };

  // 鑾峰彇浜岀淮鐮佺姸鎬佹弿杩?  const getQRCodeStatusText = () => {
    switch (qrcodeStatus) {
      case 'waiting':
        return '绛夊緟鎵爜...';
      case 'scanned':
        return '宸叉壂鐮侊紝璇峰湪鎵嬫満涓婄‘璁?;
      case 'confirmed':
        return '鐧诲綍鎴愬姛锛?;
      case 'expired':
        return '浜岀淮鐮佸凡杩囨湡';
      default:
        return '鏈煡鐘舵€?;
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <Space>
            <QrcodeOutlined />
            <span>115缃戠洏閰嶇疆</span>
          </Space>
        }
        extra={
          config?.is_configured && (
            <Button
              icon={<SyncOutlined />}
              onClick={() => testConnectionMutation.mutate()}
              loading={testConnectionMutation.isPending}
            >
              娴嬭瘯杩炴帴
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
          {/* 鏄剧ず褰撳墠鐧诲綍鐢ㄦ埛淇℃伅 */}
          {config?.is_configured && config?.user_info && (
            <Alert
              message="褰撳墠鐧诲綍鐢ㄦ埛"
              description={
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  <div>
                    <Text strong>鐢ㄦ埛ID锛?/Text>
                    <Text>{config.user_info.user_id}</Text>
                  </div>
                  <div>
                    <Text strong>鐢ㄦ埛鍚嶏細</Text>
                    <Text>{config.user_info.user_name || '鏈缃?}</Text>
                  </div>
                  <div>
                    <Text strong>浼氬憳绛夌骇锛?/Text>
                    <Text>
                      {config.user_info.vip_name || (config.user_info.is_vip 
                        ? `VIP${config.user_info.vip_level || ''} 浼氬憳` 
                        : '鏅€氱敤鎴?)}
                    </Text>
                  </div>
                  {config.user_info.space && (
                    <>
                      <div>
                        <Text strong>鎬荤┖闂达細</Text>
                        <Text>{(config.user_info.space.total / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                      <div>
                        <Text strong>宸茬敤绌洪棿锛?/Text>
                        <Text>{(config.user_info.space.used / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                      <div>
                        <Text strong>鍓╀綑绌洪棿锛?/Text>
                        <Text>{(config.user_info.space.remain / 1024 / 1024 / 1024).toFixed(2)} GB</Text>
                      </div>
                    </>
                  )}
                  {config.user_info.email && (
                    <div>
                      <Text strong>閭锛?/Text>
                      <Text>{config.user_info.email}</Text>
                    </div>
                  )}
                  {config.user_info.mobile && (
                    <div>
                      <Text strong>鎵嬫満锛?/Text>
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

          {/* 姝ラ1锛氭壂鐮佺櫥褰曟寜閽?*/}
          <Form.Item label="姝ラ1锛氱櫥褰?15璐﹀彿">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Select
                  value={deviceType}
                  onChange={setDeviceType}
                  style={{ width: 260 }}
                  placeholder="閫夋嫨璁惧绫诲瀷"
                >
                  <Select.Option value="qandroid">馃 115鐢熸椿 - Android</Select.Option>
                  <Select.Option value="qios">馃摫 115鐢熸椿 - iOS</Select.Option>
                  <Select.Option value="android">馃 115缃戠洏 - Android</Select.Option>
                  <Select.Option value="ios">馃摫 115缃戠洏 - iOS</Select.Option>
                  <Select.Option value="ipad">馃摫 115缃戠洏 - iPad</Select.Option>
                  <Select.Option value="web">馃寪 缃戦〉鐗?/Select.Option>
                  <Select.Option value="harmony">馃敺 楦胯挋绯荤粺</Select.Option>
                  <Select.Option value="alipaymini">馃挸 鏀粯瀹濆皬绋嬪簭</Select.Option>
                  <Select.Option value="wechatmini">馃挰 寰俊灏忕▼搴?/Select.Option>
                </Select>
                <Button
                  type="primary"
                  icon={<QrcodeOutlined />}
                  onClick={handleQRCodeLogin}
                  loading={getRegularQRCodeMutation.isPending}
                >
                  鎵爜鐧诲綍
                </Button>
              </Space>
              {config?.pan115_user_id && (
                <Alert
                  message={`宸茬櫥褰曪細UID=${config.pan115_user_id}`}
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                />
              )}
            </Space>
          </Form.Item>

          <Divider />

          {/* 姝ラ2锛氬惎鐢ㄥ紑鏀惧钩鍙癆PI锛堝彲閫夛級 */}
          <Form.Item label="姝ラ2锛氬惎鐢?15寮€鏀惧钩鍙癆PI锛堝彲閫夛級">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <input
                  type="checkbox"
                  id="use-open-api"
                  checked={useOpenApi}
                  onChange={(e) => setUseOpenApi(e.target.checked)}
                  style={{ marginRight: 8 }}
                />
                <label htmlFor="use-open-api">鍚敤115寮€鏀惧钩鍙癆PI锛堥渶瑕丄ppID锛?/label>
              </div>

              {useOpenApi && (
                <>
                  <Form.Item
                    label="115寮€鏀惧钩鍙癆ppID"
                    name="pan115_app_id"
                    rules={[
                      { required: useOpenApi, message: '璇疯緭鍏?15寮€鏀惧钩鍙癆ppID' },
                      { pattern: /^\d+$/, message: 'AppID蹇呴』鏄暟瀛? },
                    ]}
                    tooltip="浠?15寮€鏀惧钩鍙拌幏鍙栫殑搴旂敤ID"
                    style={{ marginBottom: 8, marginTop: 12 }}
                  >
                    <Input 
                      placeholder="璇疯緭鍏ユ偍鐨凙ppID锛堢函鏁板瓧锛? 
                      disabled={isLoading}
                      style={{ maxWidth: 400 }}
                    />
                  </Form.Item>

                  <Form.Item
                    label="API璇锋眰闂撮殧锛堢锛?
                    name="pan115_request_interval"
                    tooltip="閬垮厤瑙﹀彂115 API闄愭祦锛屽缓璁缃负1.0绉?
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
                    婵€娲诲紑鏀惧钩鍙癆PI
                  </Button>
                  {!config?.pan115_user_id && (
                    <Alert
                      message="璇峰厛瀹屾垚姝ラ1鐨勬壂鐮佺櫥褰?
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
                message="宸查厤缃?15缃戠洏"
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

        {/* 閰嶇疆璇存槑 - 鏀惧湪鏈€涓嬮潰 */}
        <Alert
          message="115缃戠洏閰嶇疆璇存槑"
          description={
            <div>
              <p><strong>姝ラ1锛氭壂鐮佺櫥褰?15</strong></p>
              <p style={{ marginLeft: 20 }}>鈥?閫夋嫨鎮ㄦ墜鏈轰笂瀹夎鐨?15搴旂敤瀵瑰簲鐨勮澶囩被鍨?/p>
              <p style={{ marginLeft: 20 }}>鈥?鐐瑰嚮"鎵爜鐧诲綍"鎸夐挳锛屼娇鐢ㄥ搴旂殑115搴旂敤鎵爜</p>
              <p style={{ marginLeft: 20 }}>鈥?杩欏皢鑾峰彇鍩虹鐧诲綍鍑瘉锛坈ookies锛?/p>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <p><strong>姝ラ2锛堝彲閫夛級锛氬惎鐢?15寮€鏀惧钩鍙癆PI</strong></p>
              <p style={{ marginLeft: 20 }}>鈥?濡傞渶浣跨敤寮€鏀惧钩鍙癆PI鍔熻兘锛岃鍚敤姝ら€夐」</p>
              <p style={{ marginLeft: 20 }}>鈥?鍦?<Link href="https://www.yuque.com/115yun/open" target="_blank">115寮€鏀惧钩鍙?/Link> 鐢宠AppID</p>
              <p style={{ marginLeft: 20 }}>鈥?濉啓AppID鍚庯紝绯荤粺灏嗚嚜鍔ㄤ娇鐢ㄥ凡鐧诲綍鐨勮处鍙锋縺娲诲紑鏀惧钩鍙癆PI</p>
              <p style={{ marginLeft: 20 }}>鈥?寮€鏀惧钩鍙癆PI鍑瘉鏇寸ǔ瀹氾紝鏈夋晥鏈熸洿闀?/p>
            </div>
          }
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginTop: 24 }}
        />
      </Card>

      {/* 浜岀淮鐮丮odal */}
      <Modal
        title="115缃戠洏鎵爜鐧诲綍"
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
                    <Text type="secondary">璇蜂娇鐢?15 APP鎵弿浜岀淮鐮?/Text>
                  )}
                  {qrcodeStatus === 'scanned' && (
                    <Text type="warning">璇峰湪鎵嬫満涓婄偣鍑荤‘璁ょ櫥褰?/Text>
                  )}
                  {qrcodeStatus === 'confirmed' && (
                    <Text type="success">鐧诲綍鎴愬姛锛屾鍦ㄤ繚瀛樺嚟鎹?..</Text>
                  )}
                  {qrcodeStatus === 'expired' && (
                    <Button onClick={handleQRCodeLogin}>閲嶆柊鑾峰彇浜岀淮鐮?/Button>
                  )}
                </Space>
              </div>
            </>
          ) : (
            <Spin tip="姝ｅ湪鑾峰彇浜岀淮鐮?.." />
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
