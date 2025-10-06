import React, { useMemo, memo } from 'react';
import { Row, Col, Card, Typography, Space, Button, Spin, Table } from 'antd';
import {
  MessageOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SettingOutlined,
  ReloadOutlined,
  BarChartOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import dayjs from 'dayjs';
import type { WeeklyDayStats, TodayChartData, PieChartDataItem, BarChartGroupedData } from '../../types/dashboard';

// Services
// import { systemApi } from '../../services/system';
// import { dashboardApi } from '../../services/dashboard';
import { rulesApi } from '../../services/rules';
import { logsApi } from '../../services/logs';

// Components
import StatsCard from './components/StatsCard';

const { Title, Text } = Typography;

// 性能优化：memo化StatsCard组件
const MemoizedStatsCard = memo(StatsCard);

// 性能优化：memo化Table列配置
const logTableColumns = [
  {
    title: '规则',
    dataIndex: 'rule_name',
    key: 'rule_name',
    width: 100,
    render: (text: string) => (
      <span className="text-info" style={{ fontWeight: 'bold' }}>
        {text || '未知规则'}
      </span>
    ),
  },
  {
    title: '消息内容',
    dataIndex: 'message_text',
    key: 'message_text',
    ellipsis: true,
    render: (text: string) => (
      <span className="text-primary">
        {text && text.length > 30 ? `${text.slice(0, 30)}...` : text || '无内容'}
      </span>
    ),
  },
  {
    title: '时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 80,
    render: (text: string) => (
      <span className="text-secondary" style={{ fontSize: '12px' }}>
        {text ? dayjs(text).format('HH:mm') : '-'}
      </span>
    ),
  },
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // 规则数据查询 - 必须先定义
  const { data: rules = [], isLoading: rulesLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: () => rulesApi.list(),
    refetchInterval: 60000, // 1分钟刷新
    retry: 1,
  });

  // 今日日志查询
  const { data: todayLogs = [], isLoading: todayLogsLoading } = useQuery({
    queryKey: ['today-logs'],
    queryFn: async () => {
      try {
        const today = dayjs().format('YYYY-MM-DD');
        console.log('🔍 Dashboard 查询今日日志:', { today, start_date: today, end_date: today });
        const logs = await logsApi.list({
          page: 1,
          limit: 1000,
          start_date: today,
          end_date: today,
        });
        console.log('📊 Dashboard 收到日志数据:', { total: logs.total, items: logs.items?.length || 0 });
        return logs.items || [];
      } catch (error) {
        console.error('❌ 获取今日日志失败:', error);
        return [];
      }
    },
    refetchInterval: 60000, // 60秒刷新
    retry: 1,
  });

  // 统计数据 - 直接计算
  const stats = React.useMemo(() => {
    try {
      const activeRules = Array.isArray(rules) ? rules.filter(rule => rule?.is_active).length : 0;
      const totalRules = Array.isArray(rules) ? rules.length : 0;
      const todayMessages = Array.isArray(todayLogs) ? todayLogs.length : 0;
      const successMessages = Array.isArray(todayLogs) ? todayLogs.filter(log => log?.status === 'success').length : 0;
      const successRate = todayMessages > 0 ? Math.round((successMessages / todayMessages) * 100) : 0;

      return {
        active_rules: activeRules,
        total_rules: totalRules,
        success_rate: successRate,
        today_messages: todayMessages,
      };
    } catch (error) {
      console.error('计算统计数据失败:', error);
      return {
        active_rules: 0,
        total_rules: 0,
        success_rate: 0,
        today_messages: 0,
      };
    }
  }, [rules, todayLogs]);
  
  const statsLoading = rulesLoading || todayLogsLoading;

  // 增强版系统状态查询（TMC始终使用增强模式）
  const { data: enhancedStatus } = useQuery({
    queryKey: ['enhanced-status'],
    queryFn: async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/system/enhanced-status', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });
        if (!response.ok) {
          throw new Error('Failed to fetch enhanced status');
        }
        const data = await response.json();
        // 确保 enhanced_mode 始终为 true，因为 TMC 只支持增强模式
        return { ...data, enhanced_mode: true };
      } catch (error) {
        // 即使 API 失败也返回增强模式
        console.warn('Enhanced status API failed, using default:', error);
        return {
          enhanced_mode: true,  // 始终为 true
          total_clients: 0,
          running_clients: 0,
          connected_clients: 0
        };
      }
    },
    refetchInterval: 15000,
    retry: 1,
  });

  // 近七日统计查询
  const { data: weeklyStats, isLoading: weeklyStatsLoading, error: logsError } = useQuery({
    queryKey: ['weekly-stats'],
    queryFn: async () => {
      const days: string[] = [];
      const statsData: WeeklyDayStats[] = [];
      
      // 获取过去7天的数据
      for (let i = 6; i >= 0; i--) {
        const date = dayjs().subtract(i, 'day').format('YYYY-MM-DD');
        days.push(date);
        
        try {
          const dayLogs = await logsApi.list({
            page: 1,
            limit: 1000,
            start_date: date,
            end_date: date,
          });
          
          statsData.push({
            date,
            day: dayjs(date).format('MM-DD'),
            weekday: dayjs(date).format('ddd'),
            total: dayLogs.items.length,
            success: dayLogs.items.filter(log => log.status === 'success').length,
            failed: dayLogs.items.filter(log => log.status === 'failed').length,
            ruleStats: {},
          });
        } catch (error) {
          console.error(`获取 ${date} 数据失败:`, error);
          statsData.push({
            date,
            day: dayjs(date).format('MM-DD'),
            weekday: dayjs(date).format('ddd'),
            total: 0,
            success: 0,
            failed: 0,
            ruleStats: {},
          });
        }
      }
      
      // 等待所有异步操作完成，然后生成图表数据
      const enhancedStats = await Promise.all(statsData.map(async dayData => {
        try {
          const dayLogs = await logsApi.list({
            page: 1,
            limit: 1000,
            start_date: dayData.date,
            end_date: dayData.date,
          });
          
          const dayRuleStats: { [rule: string]: number } = {};
          dayLogs.items.forEach(log => {
            const ruleName = log.rule_name || '未知规则';
            dayRuleStats[ruleName] = (dayRuleStats[ruleName] || 0) + 1;
          });
          
          return {
            ...dayData,
            ruleStats: dayRuleStats,
          };
        } catch (error) {
          console.error(`处理 ${dayData.date} 规则统计失败:`, error);
          return {
            ...dayData,
            ruleStats: {},
          };
        }
      }));
      
      // 收集所有规则名称
      const allRulesSet = new Set<string>();
      enhancedStats.forEach(dayData => {
        Object.keys(dayData.ruleStats).forEach(rule => allRulesSet.add(rule));
      });
      
      const allRulesList = Array.from(allRulesSet);
      
      // 生成图表数据 - 确保数据格式正确
      const chartData = enhancedStats.flatMap(dayData => {
        if (allRulesList.length === 0) {
          // 如果没有真实数据，生成固定的示例数据（避免随机数导致的不一致）
          const sampleData = [
            { type: '示例规则A', baseCount: 8 },
            { type: '示例规则B', baseCount: 5 },
            { type: '示例规则C', baseCount: 3 },
          ];
          
          return sampleData.map(sample => ({
            day: String(dayData.day),
            count: sample.baseCount + Math.floor(Math.sin(dayData.day.charCodeAt(0)) * 5), // 基于日期的固定变化
            type: sample.type,
            weekday: String(dayData.weekday),
          }));
        }
        
        // 有真实数据时，只显示有数据的规则（过滤掉0值）
        return allRulesList
          .map(ruleName => ({
            day: String(dayData.day),
            count: Number(dayData.ruleStats[ruleName] || 0),
            type: String(ruleName),
            weekday: String(dayData.weekday),
          }))
          .filter(item => item.count > 0); // 只显示有数据的项目
      });
      
      return {
        days,
        stats: enhancedStats,
        chartData,
        allRules: allRulesList,
      };
    },
    refetchInterval: 300000, // 5分钟刷新
    retry: 1,
  });

  // 获取今日统计数据
  const { data: todayStats, isLoading: todayStatsLoading } = useQuery({
    queryKey: ['today-stats'],
    queryFn: async () => {
      const today = dayjs().format('YYYY-MM-DD');
      const allLogs = await logsApi.list({
        page: 1,
        limit: 1000, // 获取更多数据用于统计
        start_date: today,
        end_date: today,
      });
      
      // 按规则统计消息数量
      const ruleStats = allLogs.items.reduce((acc: Record<string, number>, log: any) => {
        const ruleName = log.rule_name || '未知规则';
        acc[ruleName] = (acc[ruleName] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      // 转换为图表数据格式
      const chartData: TodayChartData[] = Object.entries(ruleStats).map(([rule, count]) => ({
        rule: String(rule),
        count: Number(count),
        type: '消息数量',
      }));

      return {
        totalMessages: allLogs.items.length,
        ruleStats,
        chartData,
        logs: allLogs.items.slice(0, 20), // 最近20条用于显示
      };
    },
    refetchInterval: 60000, // 60秒刷新
    retry: 1,
  });

  // 性能优化：使用useMemo缓存计算结果
  const computedStats = useMemo(() => {
    // 使用 stats 中已计算好的数据，确保数据一致性
    const activeRules = stats?.active_rules || 0;
    const totalRules = stats?.total_rules || 0;
    const successRate = stats?.success_rate || 0;
    const todayMessages = stats?.today_messages || 0;
    
    return { activeRules, totalRules, successRate, todayMessages };
  }, [stats]);
  
  const { activeRules, totalRules, successRate, todayMessages } = computedStats;

  // 错误处理
  if (logsError) {
    console.error('API Errors:', { logsError });
  }

  // 如果所有数据都在加载中，显示加载状态
  if (statsLoading && rulesLoading && weeklyStatsLoading) {
    return (
      <div style={{ 
        padding: '0 16px', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Spin size="large" />
        <Text className="text-primary" style={{ marginLeft: 16 }}>正在加载数据...</Text>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', maxWidth: 'none' }}>


      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="今日消息"
            value={todayMessages}
            icon={<MessageOutlined />}
            color="#1890ff"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="转发成功率"
            value={successRate}
            suffix="%"
            icon={<CheckCircleOutlined />}
            color="#52c41a"
            loading={statsLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="活跃规则"
            value={activeRules}
            icon={<ClockCircleOutlined />}
            color="#faad14"
            loading={rulesLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <MemoizedStatsCard
            title="总规则数"
            value={totalRules}
            icon={<SettingOutlined />}
            color="#722ed1"
            loading={rulesLoading}
          />
        </Col>
      </Row>

      {/* 系统状态 */}
      <Card className="glass-card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} className="text-primary" style={{ margin: 0 }}>
            🔧 系统状态
            {enhancedStatus?.enhanced_mode && (
              <span style={{ 
                marginLeft: '8px', 
                fontSize: '12px', 
                background: '#52c41a', 
                color: 'var(--color-text-primary)', 
                padding: '2px 8px', 
                borderRadius: '4px' 
              }}>
                增强模式
              </span>
            )}
          </Title>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
            loading={statsLoading}
          >
            刷新
          </Button>
        </div>
        
        <Row gutter={[16, 16]}>
          {/* TMC只使用增强模式 - 移除了传统模式显示 */}
          <Col xs={24} sm={6} md={6}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div className="text-primary" style={{ fontSize: '14px', marginBottom: '4px' }}>
                客户端总数
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: '#1890ff' }}>
                  🔗 {enhancedStatus?.total_clients || 0}
                </span>
              </div>
              <div className="text-secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                多客户端管理
              </div>
            </div>
          </Col>
          <Col xs={24} sm={6} md={6}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div className="text-primary" style={{ fontSize: '14px', marginBottom: '4px' }}>
                运行中客户端
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: (enhancedStatus?.running_clients || 0) > 0 ? '#52c41a' : '#faad14' }}>
                  ⚡ {enhancedStatus?.running_clients || 0}
                </span>
              </div>
              <div className="text-secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                独立事件循环
              </div>
            </div>
          </Col>
          <Col xs={24} sm={6} md={6}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div className="text-primary" style={{ fontSize: '14px', marginBottom: '4px' }}>
                已连接客户端
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: (enhancedStatus?.connected_clients || 0) > 0 ? '#52c41a' : '#ff4d4f' }}>
                  ✅ {enhancedStatus?.connected_clients || 0}
                </span>
              </div>
              <div className="text-secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                实时监听中
              </div>
            </div>
          </Col>
          <Col xs={24} sm={6} md={6}>
            <div style={{ 
              padding: '12px', 
              textAlign: 'center',
              minHeight: '80px'
            }}>
              <div className="text-primary" style={{ fontSize: '14px', marginBottom: '4px' }}>
                规则运行状态
              </div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                <span style={{ color: activeRules > 0 ? '#52c41a' : '#faad14' }}>
                  {activeRules > 0 ? '🟢 活跃' : '🟡 待激活'}
                </span>
              </div>
              <div className="text-secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                {activeRules}/{totalRules} 规则活跃
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 今日统计图表和日志表格 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 今日规则统计图表 - 圆环图 */}
        <Col xs={24} lg={12}>
        <Card
          className="glass-card"
          title={
            <span className="text-primary">
              <BarChartOutlined style={{ marginRight: 8 }} />
              今日统计
            </span>
          }
          style={{ height: 400 }}
        >
            {todayStatsLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                <Spin size="large" />
              </div>
            ) : todayStats?.chartData?.length ? (
              <div style={{ position: 'relative', height: 300 }}>
                {/* 左上角标签统计 */}
                <div style={{ 
                  position: 'absolute', 
                  top: 20, 
                  left: 20, 
                  zIndex: 10,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}>
                  {todayStats.chartData.map((item: TodayChartData, index: number) => {
                    const colors = ['#00D4FF', '#52c41a', '#fa8c16', '#eb2f96'];
                    const color = colors[index % colors.length];
                    return (
                      <div key={item.rule} style={{ 
                        display: 'flex', 
                        alignItems: 'center',
                        fontSize: '15px',
                        color: 'var(--color-text-primary)',
                        fontWeight: '500'
                      }}>
                        <div style={{ 
                          width: 10, 
                          height: 10, 
                          backgroundColor: color,
                          borderRadius: '50%',
                          marginRight: 10
                        }} />
                        <span style={{ 
                          color: 'var(--color-text-primary)',
                        }}>
                          {item.rule}: {item.count}
                        </span>
                      </div>
                    );
                  })}
                </div>
                
                {/* 使用Recharts圆环图 */}
                <div style={{ position: 'relative', height: '300px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={(() => {
                          // 健壮的饼图数据转换
                          const convertPieData = (rawData: TodayChartData[]): PieChartDataItem[] => {
                            if (!Array.isArray(rawData) || rawData.length === 0) {
                              return [];
                            }

                            return rawData.map((item, index) => {
                              try {
                                const name = String(item?.rule || `规则${index + 1}`);
                                const value = Number(item?.count || 0);
                                
                                return {
                                  name: name.trim(),
                                  value: value,
                                  id: `pie-${index}` // 添加唯一ID
                                };
                              } catch (error) {
                                return {
                                  name: `规则${index + 1}`,
                                  value: 0,
                                  id: `pie-${index}`
                                };
                              }
                            }).filter(item => item.value > 0); // 过滤掉0值
                          };

                          return convertPieData(todayStats.chartData || []);
                        })()}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {/* 动态颜色分配 */}
                        {(() => {
                          const colors = ['#00D4FF', '#52c41a', '#fa8c16', '#eb2f96', '#722ed1', '#13c2c2', '#f5222d'];
                          const data = todayStats?.chartData || [];
                          
                          return data.map((_entry: TodayChartData, index: number) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={colors[index % colors.length]}
                              stroke="none"
                            />
                          ));
                        })()}
                      </Pie>
                      
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'var(--tooltip-bg)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '8px',
                          color: 'var(--color-text-primary)',
                          fontSize: '15px',
                          fontWeight: '500',
                          backdropFilter: 'blur(12px)',
                          boxShadow: 'var(--shadow-medium)',
                        }}
                        formatter={(value: number, name: string) => [
                          <span className="text-primary" style={{ fontSize: '15px', fontWeight: '600' }}>
                            {value}条消息
                          </span>, 
                          <span className="text-primary" style={{ fontSize: '14px', fontWeight: '500' }}>
                            {name}
                          </span>
                        ]}
                        labelStyle={{ 
                          color: 'var(--color-text-primary)', 
                          fontWeight: 'bold',
                          fontSize: '16px',
                        }}
                      />
                      
                      <Legend
                        verticalAlign="bottom"
                        height={40}
                        iconType="circle"
                        wrapperStyle={{
                          color: 'var(--color-text-primary)',
                          fontSize: '15px',
                          fontWeight: '500',
                          paddingTop: '12px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  
                  {/* 中心统计文字 */}
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    pointerEvents: 'none'
                  }}>
                    <div style={{
                      color: 'var(--color-text-primary)',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      marginBottom: '4px'
                    }}>
                      总计
                    </div>
                    <div style={{
                      color: '#00D4FF',
                      fontSize: '20px',
                      fontWeight: 'bold'
                    }}>
                      {todayStats?.chartData ? 
                        todayStats.chartData.reduce((sum: number, item: any) => sum + (item.count || 0), 0) : 0
                      }
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '100px 20px',
                color: 'var(--color-text-secondary)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
                <div style={{ fontSize: '16px' }}>今日暂无数据</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 今日日志列表 */}
        <Col xs={24} lg={12}>
          <Card
            className="glass-card"
            style={{ height: 400 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Title level={4} className="text-primary" style={{ margin: 0 }}>
                <UnorderedListOutlined style={{ marginRight: 8 }} />
                今日日志
              </Title>
              <Space>
                <Text className="text-secondary" style={{ fontSize: '14px' }}>
                  今日 {todayMessages} 条
                </Text>
                <Button
                  type="text"
                  size="small"
                  style={{ color: '#1890ff' }}
                  onClick={() => navigate('/logs')}
                >
                  查看全部
                </Button>
              </Space>
            </div>

            {todayStatsLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 280 }}>
                <Spin size="large" />
              </div>
            ) : (
              <Table
                dataSource={todayStats?.logs || []}
                size="small"
                pagination={false}
                scroll={{ y: 280 }}
                rowKey="id"
                columns={logTableColumns}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 近七日统计图 */}
      <Card className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} className="text-primary" style={{ margin: 0 }}>
            📊 近七日统计
          </Title>
          <Space>
            <Text className="text-secondary" style={{ fontSize: '14px' }}>
              总计 {weeklyStats?.stats?.reduce((sum, day) => sum + (day.total || 0), 0) || 0} 条
            </Text>
            <Button
              type="text"
              size="small"
              style={{ color: '#1890ff' }}
              onClick={() => navigate('/logs')}
            >
              查看详情
            </Button>
          </Space>
        </div>
        
        {weeklyStatsLoading ? (
          <div style={{ textAlign: 'center', padding: '100px 20px' }}>
            <Spin size="large" />
            <div className="text-secondary" style={{ marginTop: '16px' }}>
              正在加载统计数据...
            </div>
          </div>
        ) : weeklyStats?.chartData?.length ? (
          <div className="recharts-fallback-container">
            <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={(() => {
                const rawData = weeklyStats.chartData || [];
                
                if (!Array.isArray(rawData) || rawData.length === 0) {
                  return [];
                }

                // 按日期分组数据
                const groupedByDay: Record<string, BarChartGroupedData> = {};
                
                rawData.forEach((item) => {
                  const day = String(item?.day || '');
                  const count = Number(item?.count || 0);
                  const type = String(item?.type || '未知规则');
                  
                  if (count <= 0 || !day) return;
                  
                  if (!groupedByDay[day]) {
                    groupedByDay[day] = { day };
                  }
                  
                  // 累加同一天同一规则的数据
                  if (groupedByDay[day][type]) {
                    const currentValue = groupedByDay[day][type];
                    groupedByDay[day][type] = (typeof currentValue === 'number' ? currentValue : 0) + count;
                  } else {
                    groupedByDay[day][type] = count;
                  }
                });
                
                return Object.values(groupedByDay);
              })()}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              barCategoryGap="20%"
            >
              <CartesianGrid 
                strokeDasharray="3 3" 
                stroke="var(--color-border-light)" 
                vertical={false} // 只显示水平网格线
              />
              <XAxis 
                dataKey="day" 
                axisLine={false}
                tickLine={false}
                tick={{ 
                  fill: 'var(--color-text-primary)', 
                  fontSize: 13, 
                  fontWeight: 600,
                  textAnchor: 'middle'
                }}
              />
              <YAxis 
                axisLine={false}
                tickLine={false}
                tick={{ 
                  fill: 'var(--color-text-secondary)', 
                  fontSize: 12 
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tooltip-bg)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--color-text-primary)',
                  fontSize: '15px',
                  fontWeight: '500',
                  backdropFilter: 'blur(12px)',
                  boxShadow: 'var(--shadow-medium)',
                }}
                cursor={false}
                content={(props) => {
                  if (!props.active || !props.payload || !props.payload.length) {
                    return null;
                  }
                  
                  const label = props.label || '未知日期';
                  
                  return (
                    <div style={{
                      backgroundColor: 'var(--tooltip-bg)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      color: 'var(--color-text-primary)',
                      fontSize: '15px',
                      fontWeight: '500',
                      backdropFilter: 'blur(12px)',
                      boxShadow: 'var(--shadow-medium)',
                      padding: '12px 16px'
                    }}>
                      <div style={{ 
                        color: 'var(--color-text-primary)', 
                        fontWeight: 'bold',
                        fontSize: '16px',
                        marginBottom: '8px'
                      }}>
                        {label}
                      </div>
                      {props.payload.map((entry: any, index: number) => {
                        const ruleName = entry.dataKey || entry.name || '未知规则';
                        const value = entry.value || 0;
                        const color = entry.color || '#1890ff';
                        
                        return (
                          <div key={index} style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            marginBottom: index === (props.payload?.length ?? 0) - 1 ? 0 : '4px'
                          }}>
                            <div style={{
                              width: '8px',
                              height: '8px',
                              backgroundColor: color,
                              marginRight: '8px',
                              borderRadius: '2px'
                            }} />
                            <span style={{ 
                              color: 'var(--color-text-primary)', 
                              fontSize: '14px', 
                              fontWeight: '500',
                              marginRight: '8px'
                            }}>
                              {ruleName}:
                            </span>
                            <span style={{ 
                              color: 'var(--color-text-primary)', 
                              fontSize: '15px', 
                              fontWeight: '600' 
                            }}>
                              {value}条消息
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  );
                }}
              />
              {/* 动态生成Bar组件 */}
              {(() => {
                const colors = ['#f59e0b', '#06b6d4', '#10b981', '#8b5cf6', '#ef4444', '#fa8c16', '#722ed1'];
                const rawData = weeklyStats.chartData || [];
                
                // 提取所有规则类型
                const ruleTypes = new Set<string>();
                rawData.forEach(item => {
                  const type = item?.type;
                  if (type && typeof type === 'string') {
                    ruleTypes.add(type);
                  }
                });
                
                const typesList = Array.from(ruleTypes).sort();
                
                if (typesList.length === 0) {
                  return <Bar key="empty" dataKey="empty" fill={colors[0]} />;
                }
                
                return typesList.map((ruleType, index) => (
                  <Bar
                    key={`bar-${ruleType}-${index}`}
                    dataKey={ruleType}
                    fill={colors[index % colors.length]}
                    radius={[6, 6, 0, 0]}
                    maxBarSize={8}
                    name={ruleType}
                  />
                ));
              })()}
            </BarChart>
          </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            color: 'var(--color-text-secondary)'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
            <div style={{ fontSize: '16px', marginBottom: '8px' }}>近七日暂无数据</div>
            <div style={{ fontSize: '14px' }}>转发规则执行后，统计将显示在这里</div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;