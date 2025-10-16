/**
 * 115网盘API服务
 */
import { apiClient } from './api';

export interface Pan115Config {
  pan115_app_id?: string;
  pan115_user_id?: string;
  pan115_user_key?: string;
  pan115_request_interval?: number;
  is_configured?: boolean;
  user_info?: {
    user_id?: string;
    user_name?: string;
    vip_name?: string;
    is_vip?: boolean;
    vip_level?: number;
    space?: {
      total: number;
      used: number;
      remain: number;
    };
    email?: string;
    mobile?: string;
    [key: string]: any;
  };
}

export interface Pan115QRCodeResponse {
  success: boolean;
  qrcode_token: string;
  qrcode_url: string;
  expires_in: number;
}

export interface Pan115QRCodeStatusResponse {
  success: boolean;
  status: 'waiting' | 'scanned' | 'confirmed' | 'expired' | 'error';
  user_id?: string;
  user_key?: string;
  user_info?: {
    user_id?: string;
    user_name?: string;
    [key: string]: any;
  };
  message?: string;
}

const pan115Api = {
  /**
   * 获取115网盘配置
   */
  getConfig: async () => {
    const response = await apiClient.get<Pan115Config>('/api/pan115/config');
    return response.data;
  },

  /**
   * 更新115网盘配置
   */
  updateConfig: async (data: {
    pan115_app_id?: string;
    pan115_user_id?: string;
    pan115_user_key?: string;
    pan115_request_interval?: number;
  }) => {
    const response = await apiClient.post('/api/pan115/config', data);
    return response.data;
  },

  /**
   * 获取115登录二维码
   */
  getQRCode: async (appId: string) => {
    const response = await apiClient.post<Pan115QRCodeResponse>('/api/pan115/qrcode', {
      app_id: appId
    });
    return response.data;
  },

  /**
   * 检查二维码扫码状态
   */
  checkQRCodeStatus: async (qrcodeToken: string, appId: string) => {
    const response = await apiClient.post<Pan115QRCodeStatusResponse>('/api/pan115/qrcode/status', {
      qrcode_token: qrcodeToken,
      app_id: appId
    });
    return response.data;
  },

  /**
   * 测试115网盘连接
   */
  testConnection: async () => {
    const response = await apiClient.post<{ success: boolean; message: string; user_info?: any }>('/api/pan115/test');
    return response.data;
  },

  /**
   * 获取常规115登录二维码（不使用开放平台API）
   */
  getRegularQRCode: async (deviceType: string = 'qandroid') => {
    const response = await apiClient.post<Pan115QRCodeResponse>('/api/pan115/regular-qrcode', {
      app: deviceType  // 修正：后端使用 app 参数
    });
    return response.data;
  },

  /**
   * 检查常规115二维码扫码状态
   */
  checkRegularQRCodeStatus: async (qrcodeTokenData: any, deviceType: string) => {
    const response = await apiClient.post<Pan115QRCodeStatusResponse>('/api/pan115/regular-qrcode/status', {
      qrcode_token: qrcodeTokenData,  // 修正：后端使用 qrcode_token 参数
      app: deviceType  // 修正：后端使用 app 参数
    });
    return response.data;
  },
};

export default pan115Api;

