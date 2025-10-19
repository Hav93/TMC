import React from 'react';
import { Row, Col, Card, Statistic, Progress, Space, Typography, Tag } from 'antd';
import {
  DatabaseOutlined,
  FilterOutlined,
  SyncOutlined,
  SaveOutlined,
  MessageOutlined,
} from '@ant-design/icons';
import type { PerformanceStats } from '../../services/performance';
import MetricsCard from './MetricsCard';

const { Title, Text } = Typography;

interface RealtimeDashboardProps {
  stats: PerformanceStats;
  loading?: boolean;
}

/**
 * 实时监控仪表板组件
 * 
 * 功能：
 * - 显示所有性能指标
 * - 实时更新数据
 * - 可视化展示
 */
const RealtimeDashboard: React.FC<RealtimeDashboardProps> = ({ stats, loading }) => {
  // 计算缓存使用率颜色
  const getCacheUsageStatus = (percent: number): 'success' | 'exception' | 'normal' => {
    if (percent < 70) return 'success';
    if (percent < 90) return 'normal';
    return 'exception';
  };

  // 计算命中率颜色
  const getHitRateColor = (rate: string): string => {
    const percent = parseFloat(rate);
    if (percent >= 80) return '#52c41a';
    if (percent >= 60) return '#faad14';
    return '#f5222d';
  };

  return (
    <div>
      {/* 消息分发器统计 - 优先显示 */}
      <Card
        title={
          <Space>
            <MessageOutlined style={{ color: '#fa8c16' }} />
            <span>📨 消息分发器</span>
          </Space>
        }
        size="small"
        loading={loading}
        bodyStyle={{ padding: '16px' }}
        style={{ marginBottom: 16 }}
      >
        {/* 总体统计 */}
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={8}>
            <MetricsCard
              title="总消息数"
              value={stats.message_dispatcher.total_messages}
              tooltip="累计处理的消息数"
            />
          </Col>
          <Col xs={24} sm={8}>
            <MetricsCard
              title="平均处理时间"
              value={stats.message_dispatcher.avg_processing_time}
              suffix="ms"
              precision={2}
              tooltip="消息处理的平均耗时"
              valueStyle={{ 
                color: stats.message_dispatcher.avg_processing_time > 500 ? '#faad14' : '#52c41a' 
              }}
            />
          </Col>
          <Col xs={24} sm={8}>
            <MetricsCard
              title="处理器数量"
              value={Object.keys(stats.message_dispatcher.processors).length}
              tooltip="已注册的消息处理器数量"
            />
          </Col>
        </Row>

        {/* 处理器详情 */}
        <div style={{ marginTop: 8 }}>
          <Title level={5} style={{ marginBottom: 12 }}>📋 处理器详情</Title>
          {Object.keys(stats.message_dispatcher.processors || {}).length > 0 ? (
            <Row gutter={[12, 12]}>
              {Object.entries(stats.message_dispatcher.processors).map(([name, processor]) => (
                <Col xs={24} sm={12} lg={8} key={name}>
                  <Card 
                    size="small" 
                    style={{ 
                      background: 'linear-gradient(135deg, rgba(24,144,255,0.05) 0%, rgba(24,144,255,0.02) 100%)',
                      borderLeft: '3px solid #1890ff'
                    }}
                    bodyStyle={{ padding: '12px' }}
                  >
                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      <Text strong style={{ fontSize: 14 }}>{name}</Text>
                      <Space size="small" wrap>
                        <Tag color="blue">处理: {processor.processed}</Tag>
                        <Tag color="success">成功: {processor.success}</Tag>
                        <Tag color="error">失败: {processor.failed}</Tag>
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        ⚡ 平均耗时: {processor.avg_time.toFixed(2)}ms
                      </Text>
                      <Progress
                        percent={processor.processed > 0 ? (processor.success / processor.processed) * 100 : 0}
                        size="small"
                        status={processor.failed > 0 ? 'exception' : 'success'}
                        format={(percent) => `${percent?.toFixed(1)}%`}
                        strokeColor={processor.failed > 0 ? '#f5222d' : '#52c41a'}
                      />
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Card size="small" style={{ textAlign: 'center', padding: '24px' }}>
              <Text type="secondary">
                <MessageOutlined style={{ fontSize: 32, marginBottom: 8, display: 'block' }} />
                暂无处理器数据
                <div style={{ fontSize: 12, marginTop: 8 }}>
                  处理器会在有消息处理时自动显示
                </div>
              </Text>
            </Card>
          )}
        </div>
      </Card>

      {/* 核心指标概览 - 使用Row布局统一高度 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 消息缓存统计 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <DatabaseOutlined style={{ color: '#1890ff' }} />
                <span>💾 消息缓存</span>
              </Space>
            }
            size="small"
            style={{ height: '100%', minHeight: '280px' }}
            bodyStyle={{ padding: '16px', height: 'calc(100% - 49px)' }}
            loading={loading}
          >
            <Row gutter={[12, 12]}>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="缓存大小"
                  value={stats.message_cache.total_size}
                  suffix={`/ ${stats.message_cache.max_size}`}
                  tooltip="当前缓存条目数 / 最大容量"
                  progress={{
                    percent: stats.message_cache.usage_percent,
                    status: getCacheUsageStatus(stats.message_cache.usage_percent),
                  }}
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="命中率"
                  value={stats.message_cache.hit_rate}
                  valueStyle={{ color: getHitRateColor(stats.message_cache.hit_rate) }}
                  tooltip="缓存命中次数 / 总请求次数"
                  extra={
                    <Space size="small">
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        命中: {stats.message_cache.hits}
                      </Text>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        未命中: {stats.message_cache.misses}
                      </Text>
                    </Space>
                  }
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="驱逐次数"
                  value={stats.message_cache.evictions}
                  tooltip="由于容量限制而被移除的缓存条目数"
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="过期次数"
                  value={stats.message_cache.expirations}
                  tooltip="由于TTL过期而被移除的缓存条目数"
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 过滤引擎统计 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <FilterOutlined style={{ color: '#52c41a' }} />
                <span>🔍 过滤引擎</span>
              </Space>
            }
            size="small"
            style={{ height: '100%', minHeight: '280px' }}
            bodyStyle={{ padding: '16px', height: 'calc(100% - 49px)' }}
            loading={loading}
          >
            <Row gutter={[12, 12]}>
              <Col xs={24}>
                <MetricsCard
                  title="总匹配次数"
                  value={stats.filter_engine.total_matches}
                  tooltip="过滤引擎执行的总匹配次数"
                />
              </Col>
              <Col xs={12}>
                <MetricsCard
                  title="正则缓存"
                  value={stats.filter_engine.regex_cache_size}
                  suffix={`/ ${stats.filter_engine.max_regex_cache}`}
                  tooltip="已编译的正则表达式缓存数"
                  progress={{
                    percent: (stats.filter_engine.regex_cache_size / stats.filter_engine.max_regex_cache) * 100,
                    status: 'normal',
                  }}
                />
              </Col>
              <Col xs={12}>
                <MetricsCard
                  title="缓存命中率"
                  value={stats.filter_engine.cache_hit_rate}
                  valueStyle={{ color: getHitRateColor(stats.filter_engine.cache_hit_rate) }}
                  tooltip="正则表达式缓存命中率"
                  extra={
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      编译次数: {stats.filter_engine.regex_compilations}
                    </Text>
                  }
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 队列和写入器 - 第二行 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {/* 重试队列统计 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SyncOutlined style={{ color: '#722ed1' }} spin />
                <span>🔄 重试队列</span>
              </Space>
            }
            size="small"
            style={{ height: '100%', minHeight: '280px' }}
            bodyStyle={{ padding: '16px', height: 'calc(100% - 49px)' }}
            loading={loading}
          >
            <Row gutter={[12, 12]}>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="队列大小"
                  value={stats.retry_queue.current_queue_size}
                  tooltip="当前等待重试的任务数"
                  valueStyle={{ 
                    color: stats.retry_queue.current_queue_size > 10 ? '#faad14' : '#52c41a' 
                  }}
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="成功率"
                  value={stats.retry_queue.success_rate}
                  valueStyle={{ color: getHitRateColor(stats.retry_queue.success_rate) }}
                  tooltip="重试成功次数 / 总重试次数"
                  extra={
                    <Space size="small">
                      <Tag color="success">成功: {stats.retry_queue.total_success}</Tag>
                      <Tag color="error">失败: {stats.retry_queue.total_failed}</Tag>
                    </Space>
                  }
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="总添加"
                  value={stats.retry_queue.total_added}
                  tooltip="累计添加到队列的任务数"
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="持久化错误"
                  value={stats.retry_queue.persistence_errors}
                  tooltip="磁盘持久化失败次数"
                  valueStyle={{ 
                    color: stats.retry_queue.persistence_errors > 0 ? '#f5222d' : '#52c41a' 
                  }}
                  extra={
                    stats.retry_queue.last_persistence && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        最后保存: {new Date(stats.retry_queue.last_persistence).toLocaleString('zh-CN')}
                      </Text>
                    )
                  }
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 批量写入器统计 */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <SaveOutlined style={{ color: '#13c2c2' }} />
                <span>💿 批量写入器</span>
              </Space>
            }
            size="small"
            style={{ height: '100%', minHeight: '280px' }}
            bodyStyle={{ padding: '16px', height: 'calc(100% - 49px)' }}
            loading={loading}
          >
            <Row gutter={[12, 12]}>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="队列大小"
                  value={stats.batch_writer.current_queue_size}
                  tooltip="当前等待写入的操作数"
                  valueStyle={{ 
                    color: stats.batch_writer.current_queue_size > 50 ? '#faad14' : '#52c41a' 
                  }}
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="总操作数"
                  value={stats.batch_writer.total_operations}
                  tooltip="累计处理的数据库操作数"
                  extra={
                    <Space size="small">
                      <Tag color="blue">插入: {stats.batch_writer.total_inserts}</Tag>
                      <Tag color="green">更新: {stats.batch_writer.total_updates}</Tag>
                    </Space>
                  }
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="刷新次数"
                  value={stats.batch_writer.total_flushes}
                  tooltip="批量写入数据库的次数"
                />
              </Col>
              <Col xs={12} sm={12}>
                <MetricsCard
                  title="错误次数"
                  value={stats.batch_writer.total_errors}
                  tooltip="批量写入失败次数"
                  valueStyle={{ 
                    color: stats.batch_writer.total_errors > 0 ? '#f5222d' : '#52c41a' 
                  }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default RealtimeDashboard;

