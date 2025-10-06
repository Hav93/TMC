export interface MessageLog {
  id: number;
  rule_id: number;
  rule_name: string;
  source_chat_id: string;
  source_chat_name: string;
  target_chat_id: string;
  target_chat_name: string;
  message_id: number;
  message_text: string;
  status: 'success' | 'failed' | 'pending';
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface LogsListResponse {
  items: MessageLog[];
  total: number;
  page: number;
  limit: number;
}

export interface LogsListParams {
  page?: number;
  limit?: number;
  rule_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
  _t?: number;
}

