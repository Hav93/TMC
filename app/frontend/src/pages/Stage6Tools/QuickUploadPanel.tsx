/**
 * 秒传检测面板
 */
import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Input, Form, message, Descriptions, Tag } from 'antd';
import { ThunderboltOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import stage6Service from '../../services/stage6';

const QuickUploadPanel: React.FC = () => {
  const [form] = Form.useForm();
  const [checkResult, setCheckResult] = useState<any>(null);

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['quick-upload-stats'],
    queryFn: () => stage6Service.getQuickUploadStats(),
    refetchInterval: 30000,
  });

  // 检查秒传
  const checkMutation = useMutation({
    mutationFn: (file_path: string) => stage6Service.checkQuickUpload(file_path),
    onSuccess: (data) => {
      setCheckResult(data);
      if (data.is_quick) {
        message.success('✅ 文件支持秒传！');
      } else {
        message.info('⚠️ 文件不支持秒传');
      }
    },
    onError: () => {
      message.error('检测失败');
    },
  });

  const handleCheck = (values: { file_path: string }) => {
    checkMutation.mutate(values.file_path);
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总检测次数"
              value={stats?.total_checks || 0}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="秒传成功"
              value={stats?.quick_success || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="秒传失败"
              value={stats?.quick_failed || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats?.success_rate || '0%'}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="节省时间"
              value={stats?.total_time_saved || '0秒'}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="节省带宽"
              value={stats?.total_bandwidth_saved || '0 B'}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="平均检测时间"
              value={stats?.avg_check_time || '< 5秒'}
            />
          </Card>
        </Col>
      </Row>

      {/* 检测表单 */}
      <Card title="秒传检测" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleCheck} layout="inline">
          <Form.Item
            name="file_path"
            rules={[{ required: true, message: '请输入文件路径' }]}
            style={{ flex: 1 }}
          >
            <Input
              placeholder="输入文件路径，例如：/path/to/file.mp4"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<ThunderboltOutlined />}
              size="large"
              loading={checkMutation.isPending}
            >
              检测秒传
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 检测结果 */}
      {checkResult && (
        <Card
          title="检测结果"
          extra={
            checkResult.is_quick ? (
              <Tag color="success" icon={<CheckCircleOutlined />}>
                支持秒传
              </Tag>
            ) : (
              <Tag color="warning" icon={<CloseCircleOutlined />}>
                不支持秒传
              </Tag>
            )
          }
        >
          <Descriptions column={2} bordered>
            <Descriptions.Item label="文件路径">
              {checkResult.file_path}
            </Descriptions.Item>
            <Descriptions.Item label="文件大小">
              {formatSize(checkResult.file_size)}
            </Descriptions.Item>
            <Descriptions.Item label="SHA1哈希" span={2}>
              <code>{checkResult.sha1}</code>
            </Descriptions.Item>
            <Descriptions.Item label="检测耗时">
              {checkResult.check_time.toFixed(2)}秒
            </Descriptions.Item>
            <Descriptions.Item label="秒传状态">
              {checkResult.is_quick ? (
                <Tag color="success">✅ 可秒传</Tag>
              ) : (
                <Tag color="default">⚠️ 需正常上传</Tag>
              )}
            </Descriptions.Item>
            {checkResult.error && (
              <Descriptions.Item label="错误信息" span={2}>
                <Tag color="error">{checkResult.error}</Tag>
              </Descriptions.Item>
            )}
          </Descriptions>
        </Card>
      )}
    </div>
  );
};

export default QuickUploadPanel;

