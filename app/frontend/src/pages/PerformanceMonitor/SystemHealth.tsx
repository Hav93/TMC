import React from 'react';
import { Card, Row, Col, Alert, Space, Typography, Tag, Badge } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import type { PerformanceStats } from '../../services/performance';

const { Title, Text } = Typography;

interface SystemHealthProps {
  stats: PerformanceStats;
  loading?: boolean;
}

type HealthStatus = 'healthy' | 'warning' | 'critical';

interface HealthCheck {
  name: string;
  status: HealthStatus;
  message: string;
  details?: string;
}

/**
 * 系统健康状态组件
 * 
 * 功能：
 * - 检查各组件健康状态
 * - 显示警告和错误
 * - 提供优化建议
 */
const SystemHealth: React.FC<SystemHealthProps> = ({ stats, loading }) => {
  // 健康检查逻辑
  const performHealthChecks = (): HealthCheck[] => {
    const checks: HealthCheck[] = [];

    // 检查缓存使用率
    if (stats.message_cache.usage_percent > 90) {
      checks.push({
        name: '消息缓存',
        status: 'critical',
        message: '缓存使用率过高',
        details: `当前使用率 ${stats.message_cache.usage_percent.toFixed(1)}%，建议增加缓存容量或清理缓存`,
      });
    } else if (stats.message_cache.usage_percent > 70) {
      checks.push({
        name: '消息缓存',
        status: 'warning',
        message: '缓存使用率较高',
        details: `当前使用率 ${stats.message_cache.usage_percent.toFixed(1)}%`,
      });
    } else {
      checks.push({
        name: '消息缓存',
        status: 'healthy',
        message: '运行正常',
        details: `使用率 ${stats.message_cache.usage_percent.toFixed(1)}%`,
      });
    }

    // 检查缓存命中率
    const cacheHitRate = parseFloat(stats.message_cache.hit_rate);
    if (cacheHitRate < 50) {
      checks.push({
        name: '缓存命中率',
        status: 'warning',
        message: '命中率偏低',
        details: `当前命中率 ${stats.message_cache.hit_rate}，可能需要调整缓存策略`,
      });
    } else {
      checks.push({
        name: '缓存命中率',
        status: 'healthy',
        message: '命中率良好',
        details: `当前命中率 ${stats.message_cache.hit_rate}`,
      });
    }

    // 检查重试队列
    if (stats.retry_queue.current_queue_size > 50) {
      checks.push({
        name: '重试队列',
        status: 'critical',
        message: '队列积压严重',
        details: `当前队列大小 ${stats.retry_queue.current_queue_size}，请检查失败原因`,
      });
    } else if (stats.retry_queue.current_queue_size > 10) {
      checks.push({
        name: '重试队列',
        status: 'warning',
        message: '队列有积压',
        details: `当前队列大小 ${stats.retry_queue.current_queue_size}`,
      });
    } else {
      checks.push({
        name: '重试队列',
        status: 'healthy',
        message: '运行正常',
        details: `队列大小 ${stats.retry_queue.current_queue_size}`,
      });
    }

    // 检查重试成功率
    const retrySuccessRate = parseFloat(stats.retry_queue.success_rate);
    if (retrySuccessRate < 70) {
      checks.push({
        name: '重试成功率',
        status: 'critical',
        message: '成功率过低',
        details: `当前成功率 ${stats.retry_queue.success_rate}，请检查失败任务`,
      });
    } else if (retrySuccessRate < 85) {
      checks.push({
        name: '重试成功率',
        status: 'warning',
        message: '成功率偏低',
        details: `当前成功率 ${stats.retry_queue.success_rate}`,
      });
    } else {
      checks.push({
        name: '重试成功率',
        status: 'healthy',
        message: '成功率良好',
        details: `当前成功率 ${stats.retry_queue.success_rate}`,
      });
    }

    // 检查批量写入器
    if (stats.batch_writer.current_queue_size > 100) {
      checks.push({
        name: '批量写入器',
        status: 'warning',
        message: '队列积压',
        details: `当前队列大小 ${stats.batch_writer.current_queue_size}，可能需要手动刷新`,
      });
    } else {
      checks.push({
        name: '批量写入器',
        status: 'healthy',
        message: '运行正常',
        details: `队列大小 ${stats.batch_writer.current_queue_size}`,
      });
    }

    // 检查批量写入错误
    if (stats.batch_writer.total_errors > 0) {
      checks.push({
        name: '批量写入错误',
        status: 'warning',
        message: '存在写入错误',
        details: `累计错误 ${stats.batch_writer.total_errors} 次`,
      });
    }

    // 检查持久化错误
    if (stats.retry_queue.persistence_errors > 0) {
      checks.push({
        name: '队列持久化',
        status: 'warning',
        message: '持久化失败',
        details: `累计失败 ${stats.retry_queue.persistence_errors} 次，请检查磁盘空间和权限`,
      });
    }

    // 检查消息处理时间
    if (stats.message_dispatcher.avg_processing_time > 1000) {
      checks.push({
        name: '消息处理性能',
        status: 'warning',
        message: '处理速度较慢',
        details: `平均耗时 ${stats.message_dispatcher.avg_processing_time.toFixed(2)}ms`,
      });
    } else {
      checks.push({
        name: '消息处理性能',
        status: 'healthy',
        message: '处理速度正常',
        details: `平均耗时 ${stats.message_dispatcher.avg_processing_time.toFixed(2)}ms`,
      });
    }

    return checks;
  };

  const healthChecks = performHealthChecks();

  // 统计健康状态
  const healthyStat = healthChecks.filter(c => c.status === 'healthy').length;
  const warningStat = healthChecks.filter(c => c.status === 'warning').length;
  const criticalStat = healthChecks.filter(c => c.status === 'critical').length;

  // 整体健康状态
  const overallStatus: HealthStatus = 
    criticalStat > 0 ? 'critical' : 
    warningStat > 0 ? 'warning' : 
    'healthy';

  // 状态图标和颜色
  const getStatusIcon = (status: HealthStatus) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14', fontSize: 16 }} />;
      case 'critical':
        return <CloseCircleOutlined style={{ color: '#f5222d', fontSize: 16 }} />;
    }
  };

  const getStatusColor = (status: HealthStatus) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
    }
  };

  const getStatusText = (status: HealthStatus) => {
    switch (status) {
      case 'healthy':
        return '健康';
      case 'warning':
        return '警告';
      case 'critical':
        return '严重';
    }
  };

  return (
    <div>
      {/* 整体健康状态 */}
      <Card size="small" style={{ marginBottom: 16 }} loading={loading}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space size="large">
            {getStatusIcon(overallStatus)}
            <div>
              <Title level={4} style={{ margin: 0 }}>
                系统整体状态: {getStatusText(overallStatus)}
              </Title>
              <Text type="secondary">
                健康: {healthyStat} | 警告: {warningStat} | 严重: {criticalStat}
              </Text>
            </div>
          </Space>

          {/* 整体状态提示 */}
          {overallStatus === 'critical' && (
            <Alert
              message="系统存在严重问题"
              description="请立即检查下方的严重问题并采取措施"
              type="error"
              showIcon
              icon={<CloseCircleOutlined />}
            />
          )}
          {overallStatus === 'warning' && (
            <Alert
              message="系统存在警告"
              description="建议检查下方的警告项并进行优化"
              type="warning"
              showIcon
              icon={<WarningOutlined />}
            />
          )}
          {overallStatus === 'healthy' && (
            <Alert
              message="系统运行正常"
              description="所有组件运行状态良好"
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
            />
          )}
        </Space>
      </Card>

      {/* 详细健康检查 */}
      <Card title="详细健康检查" size="small" loading={loading}>
        <Row gutter={[16, 16]}>
          {healthChecks.map((check, index) => (
            <Col xs={24} sm={12} md={8} key={index}>
              <Card size="small" style={{ height: '100%' }}>
                <Space direction="vertical" style={{ width: '100%' }} size="small">
                  <Space>
                    {getStatusIcon(check.status)}
                    <Text strong>{check.name}</Text>
                    <Tag color={getStatusColor(check.status)}>
                      {getStatusText(check.status)}
                    </Tag>
                  </Space>
                  <Text>{check.message}</Text>
                  {check.details && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      <InfoCircleOutlined /> {check.details}
                    </Text>
                  )}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 优化建议 */}
      {(warningStat > 0 || criticalStat > 0) && (
        <Card title="优化建议" size="small" style={{ marginTop: 16 }} loading={loading}>
          <Space direction="vertical" style={{ width: '100%' }}>
            {stats.message_cache.usage_percent > 80 && (
              <Alert
                message="缓存容量建议"
                description="考虑增加缓存容量（max_size参数）或清理缓存"
                type="info"
                showIcon
              />
            )}
            {parseFloat(stats.message_cache.hit_rate) < 60 && (
              <Alert
                message="缓存策略建议"
                description="缓存命中率较低，考虑增加TTL时间或优化缓存键设计"
                type="info"
                showIcon
              />
            )}
            {stats.retry_queue.current_queue_size > 10 && (
              <Alert
                message="重试队列建议"
                description="队列有积压，检查失败任务的原因并解决根本问题"
                type="info"
                showIcon
              />
            )}
            {stats.batch_writer.current_queue_size > 50 && (
              <Alert
                message="批量写入建议"
                description="考虑手动刷新批量写入器或调整刷新间隔"
                type="info"
                showIcon
              />
            )}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default SystemHealth;

