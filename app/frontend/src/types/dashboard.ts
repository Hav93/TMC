// Dashboard数据类型
export interface DashboardStats {
  active_rules: number;
  total_rules: number;
  success_rate: number;
  today_messages: number;
}

export interface RecentActivity {
  id: string;
  message: string;
  time: string;
  type: 'success' | 'error' | 'info';
}

export interface SystemOverview {
  cpu_usage: number;
  memory_usage: number;
  uptime: string;
  telegram_status: 'connected' | 'disconnected';
}

// 周统计数据类型
export interface WeeklyDayStats {
  date: string;
  day: string;
  weekday: string;
  total: number;
  success: number;
  failed: number;
  ruleStats: Record<string, number>;
}

export interface WeeklyChartData {
  day: string;
  count: number;
  type: string;
  weekday: string;
}

export interface TodayChartData {
  rule: string;
  count: number;
  type: string;
}

export interface PieChartDataItem {
  name: string;
  value: number;
  id: string;
}

export interface TooltipPayload {
  dataKey: string;
  name: string;
  value: number;
  color: string;
  payload: Record<string, unknown>;
}

export interface BarChartGroupedData {
  day: string;
  [ruleName: string]: string | number;
}
