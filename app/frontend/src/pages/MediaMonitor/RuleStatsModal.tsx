import React from 'react';
import { Modal, Descriptions, Statistic, Row, Col, Progress, Tag, Spin } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { mediaMonitorApi } from '../../services/mediaMonitor';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  DownloadOutlined,
  CloudOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import type { MediaMonitorRule } from '../../types/media';

interface RuleStatsModalProps {
  visible: boolean;
  rule: MediaMonitorRule | null;
  onClose: () => void;
}

const RuleStatsModal: React.FC<RuleStatsModalProps> = ({ visible, rule, onClose }) => {
  // 获取规则统计
  const { data: statsData, isLoading } = useQuery({
    queryKey: ['rule-stats', rule?.id],
    queryFn: () => rule ? mediaMonitorApi.getRuleStats(rule.id) : Promise.resolve(null),
    enabled: visible && !!rule,
    refetchInterval: 5000, // 5秒刷新一次
  });

  const stats = statsData?.stats;

  // 格式化时间
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '从未下载';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  return (
    <Modal
      title={
        <div>
          <span style={{ marginRight: 8 }}>📊 规则统计</span>
          {rule && (
            <>
              <Tag color={rule.is_active ? 'success' : 'default'}>
                {rule.is_active ? '启用中' : '已禁用'}
              </Tag>
              <span style={{ fontSize: 14, fontWeight: 'normal' }}>{rule.name}</span>
            </>
          )}
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
        </div>
      ) : (
        <>
          {/* 统计卡片 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Statistic
                title="总下载数"
                value={stats?.total_downloaded || 0}
                prefix={<DownloadOutlined />}
                suffix="个"
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="总大小"
                value={stats?.total_size_gb || 0}
                suffix="GB"
                precision={2}
                prefix={<CloudOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="失败数"
                value={stats?.failed_downloads || 0}
                suffix="个"
                prefix={<CloseCircleOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col span={6}>
              <div>
                <div style={{ fontSize: 14, color: '#999', marginBottom: 8 }}>成功率</div>
                <Progress
                  type="circle"
                  percent={stats?.success_rate || 100}
                  width={80}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </div>
            </Col>
          </Row>

          {/* 详细信息 */}
          <Descriptions bordered column={2}>
            <Descriptions.Item label="规则ID">
              {stats?.rule_id}
            </Descriptions.Item>
            <Descriptions.Item label="规则名称">
              {stats?.rule_name}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              {stats?.is_active ? (
                <Tag icon={<CheckCircleOutlined />} color="success">
                  启用中
                </Tag>
              ) : (
                <Tag color="default">已禁用</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="成功率">
              <Tag color={stats?.success_rate >= 95 ? 'success' : stats?.success_rate >= 80 ? 'warning' : 'error'}>
                {stats?.success_rate}%
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="总下载量">
              {stats?.total_downloaded || 0} 个文件
            </Descriptions.Item>
            <Descriptions.Item label="总大小">
              {stats?.total_size_mb || 0} MB ({stats?.total_size_gb || 0} GB)
            </Descriptions.Item>
            <Descriptions.Item label="失败下载">
              {stats?.failed_downloads || 0} 个
            </Descriptions.Item>
            <Descriptions.Item label="总尝试次数">
              {(stats?.total_downloaded || 0) + (stats?.failed_downloads || 0)} 次
            </Descriptions.Item>
            <Descriptions.Item label="最后下载时间" span={2}>
              <ClockCircleOutlined style={{ marginRight: 8 }} />
              {formatDate(stats?.last_download_at || null)}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间" span={2}>
              {formatDate(stats?.created_at || null)}
            </Descriptions.Item>
          </Descriptions>

          {/* 性能提示 */}
          {stats && (
            <div style={{ marginTop: 16, padding: 12, background: '#f0f2f5', borderRadius: 4 }}>
              {stats.success_rate >= 95 ? (
                <div style={{ color: '#52c41a' }}>
                  ✅ <strong>性能优秀</strong>: 该规则运行稳定，成功率高于 95%
                </div>
              ) : stats.success_rate >= 80 ? (
                <div style={{ color: '#faad14' }}>
                  ⚠️ <strong>性能一般</strong>: 建议检查规则配置或网络连接
                </div>
              ) : (
                <div style={{ color: '#cf1322' }}>
                  ❌ <strong>性能较差</strong>: 成功率低于 80%，建议检查规则设置
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Modal>
  );
};

export default RuleStatsModal;

