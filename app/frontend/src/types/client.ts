// Client相关类型
export interface TelegramClient {
  id: string;
  type: 'user' | 'bot';
  phone: string;
  session_file: string;
  is_active: boolean;
  last_active?: string;
  running?: boolean;
  connected?: boolean;
}

export interface UserInfo {
  id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
}

export interface AddClientRequest {
  client_id: string;
  client_type: 'user' | 'bot';
  api_id?: string;
  api_hash?: string;
  phone?: string;
  bot_token?: string;
  admin_user_id?: string;
}

export interface ClientLoginRequest {
  client_id: string;
  code?: string;
  password?: string;
  phone_code_hash?: string;
}

export interface ApiError {
  response?: {
    data?: {
      message?: string;
    };
  };
  message?: string;
}
