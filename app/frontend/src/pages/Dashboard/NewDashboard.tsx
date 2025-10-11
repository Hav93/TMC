import React from 'react';
import { Row, Col, Card, Statistic, Typography, Space, Button, Tag, Progress, Spin, Alert } from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloudOutlined,
  FolderOutlined,
  FileOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  AudioOutlined,
  FileTextOutlined,
  WarningOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import dayjs from 'dayjs';
import { dashboardApi } from '../../services/dashboard';
import type { DashboardOverview, DashboardInsights } from '../../services/dashboard';

const { Title, Text } = Typography;

// 颜色配置
const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#f5222d',
  purple: '#722ed1',
  cyan: '#13c2c2',
  
  // 文件类型颜色
  video: '#f5222d',
  image: '#52c41a',
  audio: '#faad14',
  document: '#1890ff',
  
  // 图表颜色
  chartColors: ['#1890ff', '#722ed1', '#52c41a', '#faad14', '#f5222d', '#13c2c2'],
};

const NewDashboard: React.FC = () => {
  const navigate = useNavigate();

  // 获取仪表盘总览数据
  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useQuery<DashboardOverview>({
    queryKey: ['dashboard-overview'],
    queryFn: () => dashboardApi.getOverview(),
    refetchInterval: 30000, // 30秒刷新
    retry: 2,
  });

  // 获取智能洞察
  const { data: insights, isLoading: insightsLoading } = useQuery<DashboardInsights>({
    queryKey: ['dashboard-insights'],
    queryFn: () => dashboardApi.getInsights(),
    refetchInterval: 60000, // 60秒刷新
    retry: 2,
  });

  // 加载状态
  if (overviewLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载仪表盘数据..." />
      </div>
    );
  }

  // 错误状态
  if (!overview) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="数据加载失败"
          description="无法获取仪表盘数据，请检查后端服务是否正常运行"
          type="error"
          showIcon
          action={
            <Button size="small" danger onClick={() => refetchOverview()}>
              重试
            </Button>
          }
        />
      </div>
    );
  }

  // 系统状态标签
  const getSystemStatusTag = (status: string) => {
    const statusConfig = {
      normal: { color: 'success', text: '正常', icon: <CheckCircleOutlined /> },
      warning: { color: 'warning', text: '警告', icon: <WarningOutlined /> },
      busy: { color: 'processing', text: '繁忙', icon: <ClockCircleOutlined /> },
    };
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.normal;
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };

  // 准备文件类型饼图数据
  const fileTypeChartData = Object.entries(overview.file_type_distribution).map(([type, data]) => ({
    name: type === 'video' ? '视频' : type === 'image' ? '图片' : type === 'audio' ? '音频' : '文档',
    value: data.count,
    size: data.size_gb,
  })).filter(item => item.value > 0);

  // 准备趋势图数据
  const prepareTrendData = (trend: Array<{ date: string; count: number }>) => {
    return trend.map(item => ({
      date: dayjs(item.date).format('MM-DD'),
      count: item.count,
    }));
  };

  const forwardTrendData = prepareTrendData(overview.forward_module.trend);
  const mediaTrendData = prepareTrendData(overview.media_module.trend);

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 系统总览卡片 */}
      <Card 
        style={{ marginBottom: 16 }}
        bodyStyle={{ padding: '16px 24px' }}
      >
        <Row align="middle" justify="space-between">
          <Col>
            <Space size="large">
              <Text strong style={{ fontSize: 16 }}>🎯 系统总览</Text>
              <Text type="secondary">
                {overview.system_overview.total_rules}个规则 | 
                {overview.system_overview.active_rules}个活跃 | 
                {overview.system_overview.today_downloads}个下载 | 
                {overview.system_overview.total_storage_gb}GB存储
              </Text>
              {getSystemStatusTag(overview.system_overview.system_status)}
            </Space>
          </Col>
          <Col>
            <Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                最后更新: {dayjs().format('HH:mm:ss')}
              </Text>
              <Button 
                icon={<ReloadOutlined />} 
                size="small"
                onClick={() => refetchOverview()}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 双栏模块卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 消息转发模块 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>📨 消息转发</span>
              </Space>
            }
            extra={
              <Button 
                type="link" 
                size="small"
                onClick={() => navigate('/rules')}
              >
                管理规则 <RightOutlined />
              </Button>
            }
            style={{ height: '100%' }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="今日转发"
                  value={overview.forward_module.today_count}
                  suffix="条"
                  valueStyle={{ color: COLORS.primary }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="活跃规则"
                  value={`${overview.forward_module.active_rules} / ${overview.forward_module.total_rules}`}
                  valueStyle={{ color: COLORS.success }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="成功率"
                  value={overview.forward_module.success_rate}
                  suffix="%"
                  prefix={overview.forward_module.success_rate >= 90 ? <CheckCircleOutlined /> : <WarningOutlined />}
                  valueStyle={{ 
                    color: overview.forward_module.success_rate >= 90 ? COLORS.success : COLORS.warning 
                  }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="处理中"
                  value={overview.forward_module.processing_count}
                  suffix="条"
                  valueStyle={{ color: COLORS.warning }}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 媒体监控模块 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <span>📥 媒体监控</span>
              </Space>
            }
            extra={
              <Button 
                type="link" 
                size="small"
                onClick={() => navigate('/media-monitor')}
              >
                管理监控 <RightOutlined />
              </Button>
            }
            style={{ height: '100%' }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="今日下载"
                  value={overview.media_module.today_count}
                  suffix="个"
                  valueStyle={{ color: COLORS.purple }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="活跃监控"
                  value={`${overview.media_module.active_rules} / ${overview.media_module.total_rules}`}
                  valueStyle={{ color: COLORS.success }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="成功率"
                  value={overview.media_module.success_rate}
                  suffix="%"
                  prefix={overview.media_module.success_rate >= 90 ? <CheckCircleOutlined /> : <WarningOutlined />}
                  valueStyle={{ 
                    color: overview.media_module.success_rate >= 90 ? COLORS.success : COLORS.warning 
                  }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="存储使用"
                  value={overview.media_module.storage_gb}
                  suffix="GB"
                  valueStyle={{ color: COLORS.cyan }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 消息转发趋势 */}
        <Col xs={24} lg={12}>
          <Card title="📈 近7日消息转发" bodyStyle={{ padding: '20px' }}>
            {forwardTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={forwardTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill={COLORS.primary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
                <div>暂无数据</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 媒体下载趋势 */}
        <Col xs={24} lg={12}>
          <Card title="📥 近7日媒体下载" bodyStyle={{ padding: '20px' }}>
            {mediaTrendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={mediaTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill={COLORS.purple} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
                <div>暂无数据</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 详细统计 */}
      <Row gutter={[16, 16]}>
        {/* 文件类型分布 */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="📁 文件类型分布" bodyStyle={{ padding: '20px' }}>
            {fileTypeChartData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={fileTypeChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {fileTypeChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS.chartColors[index % COLORS.chartColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 16 }}>
                  {fileTypeChartData.map((item, index) => (
                    <div key={index} style={{ marginBottom: 8 }}>
                      <Space>
                        <div style={{ 
                          width: 12, 
                          height: 12, 
                          background: COLORS.chartColors[index % COLORS.chartColors.length],
                          borderRadius: 2
                        }} />
                        <Text>{item.name}</Text>
                        <Text type="secondary">{item.value}个 ({item.size}GB)</Text>
                      </Space>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                <FileOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>暂无文件</div>
              </div>
            )}
          </Card>
        </Col>

        {/* 存储分布 */}
        <Col xs={24} sm={12} lg={8}>
          <Card title="☁️ 存储分布" bodyStyle={{ padding: '20px' }}>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Progress
                type="circle"
                percent={Math.round(overview.storage_distribution.cloud_percentage)}
                format={() => `${overview.storage_distribution.cloud_percentage.toFixed(1)}%`}
                strokeColor={{
                  '0%': COLORS.cyan,
                  '100%': COLORS.purple,
                }}
                width={120}
              />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">云端占比</Text>
              </div>
            </div>
            <div>
              <Row gutter={16} style={{ marginBottom: 12 }}>
                <Col span={12}>
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">本地存储</Text>
                    <Text strong>{overview.storage_distribution.local.size_gb} GB</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {overview.storage_distribution.local.count} 个文件
                    </Text>
                  </Space>
                </Col>
                <Col span={12}>
                  <Space direction="vertical" size={0}>
                    <Text type="secondary">云端存储</Text>
                    <Text strong>{overview.storage_distribution.cloud.size_gb} GB</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {overview.storage_distribution.cloud.count} 个文件
                    </Text>
                  </Space>
                </Col>
              </Row>
              <div style={{ 
                background: '#f5f5f5', 
                padding: '12px', 
                borderRadius: 4,
                marginTop: 16
              }}>
                <Space direction="vertical" size={0} style={{ width: '100%' }}>
                  <Text type="secondary">总存储</Text>
                  <Text strong style={{ fontSize: 18 }}>
                    {overview.storage_distribution.total_gb} GB
                  </Text>
                </Space>
              </div>
            </div>
          </Card>
        </Col>

        {/* 快速洞察 */}
        <Col xs={24} sm={24} lg={8}>
          <Card 
            title="🎯 快速洞察" 
            bodyStyle={{ padding: '20px' }}
            loading={insightsLoading}
          >
            {insights ? (
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {/* 今日高峰 */}
                {insights.peak_hour && (
                  <div>
                    <Space>
                      <div style={{ fontSize: 24 }}>🔥</div>
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>今日下载高峰</Text>
                        <div>
                          <Text strong>{insights.peak_hour}</Text>
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            ({insights.peak_count}个)
                          </Text>
                        </div>
                      </div>
                    </Space>
                  </div>
                )}

                {/* 最活跃规则 */}
                {insights.most_active_rule && (
                  <div>
                    <Space>
                      <div style={{ fontSize: 24 }}>⭐</div>
                      <div>
                        <Text type="secondary" style={{ fontSize: 12 }}>最活跃规则</Text>
                        <div>
                          <Text strong>{insights.most_active_rule}</Text>
                          <Text type="secondary" style={{ marginLeft: 8 }}>
                            ({insights.most_active_count}个)
                          </Text>
                        </div>
                      </div>
                    </Space>
                  </div>
                )}

                {/* 存储预警 */}
                {insights.storage_warning && (
                  <div>
                    <Space align="start">
                      <div style={{ fontSize: 24 }}>
                        {insights.storage_warning.should_warn ? '⚠️' : '💾'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>存储状态</Text>
                        <div>
                          <Progress 
                            percent={Math.round(insights.storage_warning.usage_percentage)} 
                            size="small"
                            status={insights.storage_warning.should_warn ? 'exception' : 'normal'}
                          />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {insights.storage_warning.current_usage_gb.toFixed(1)} / {insights.storage_warning.total_capacity_gb} GB
                          </Text>
                        </div>
                        {insights.storage_warning.should_warn && (
                          <Text type="warning" style={{ fontSize: 12 }}>
                            预计 {insights.storage_warning.days_until_80_percent} 天后达到80%
                          </Text>
                        )}
                      </div>
                    </Space>
                  </div>
                )}

                {/* 收藏文件 */}
                <div>
                  <Space>
                    <div style={{ fontSize: 24 }}>⭐</div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12 }}>收藏文件</Text>
                      <div>
                        <Text strong>{overview.other_stats.starred_count}</Text>
                        <Text type="secondary" style={{ marginLeft: 8 }}>个</Text>
                      </div>
                    </div>
                  </Space>
                </div>
              </Space>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>💡</div>
                <div>暂无洞察数据</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default NewDashboard;

