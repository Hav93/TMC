/**
 * 智能重命名面板
 */
import React, { useState } from 'react';
import { Card, Button, Input, Form, message, Descriptions, Table, Space, Select, Tag } from 'antd';
import { EditOutlined, FileTextOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import stage6Service from '../../services/stage6';

const { TextArea } = Input;
const { Option } = Select;

const SmartRenamePanel: React.FC = () => {
  const [parseForm] = Form.useForm();
  const [renameForm] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [parseResult, setParseResult] = useState<any>(null);
  const [renameResult, setRenameResult] = useState<any>(null);
  const [batchResult, setBatchResult] = useState<any>(null);

  // 获取模板
  const { data: templates } = useQuery({
    queryKey: ['rename-templates'],
    queryFn: () => stage6Service.getRenameTemplates(),
  });

  // 解析文件名
  const parseMutation = useMutation({
    mutationFn: (filename: string) => stage6Service.parseFilename(filename),
    onSuccess: (data) => {
      setParseResult(data);
      message.success('解析成功');
    },
  });

  // 重命名单个文件
  const renameMutation = useMutation({
    mutationFn: (values: { filename: string; template?: string }) =>
      stage6Service.renameFile(values.filename, values.template),
    onSuccess: (data) => {
      setRenameResult(data);
      message.success('重命名成功');
    },
  });

  // 批量重命名
  const batchRenameMutation = useMutation({
    mutationFn: (values: { filenames: string[]; template?: string }) =>
      stage6Service.batchRenameFiles(values.filenames, values.template),
    onSuccess: (data) => {
      setBatchResult(data);
      message.success(`批量重命名完成，共处理 ${data.total} 个文件`);
    },
  });

  const handleParse = (values: { filename: string }) => {
    parseMutation.mutate(values.filename);
  };

  const handleRename = (values: any) => {
    renameMutation.mutate(values);
  };

  const handleBatchRename = (values: any) => {
    const filenames = values.filenames.split('\n').filter((f: string) => f.trim());
    batchRenameMutation.mutate({ filenames, template: values.template });
  };

  const batchColumns = [
    {
      title: '原文件名',
      dataIndex: 'original',
      key: 'original',
      ellipsis: true,
    },
    {
      title: '新文件名',
      dataIndex: 'renamed',
      key: 'renamed',
      ellipsis: true,
    },
  ];

  const batchDataSource = batchResult
    ? Object.entries(batchResult.renamed).map(([original, renamed]) => ({
        original,
        renamed,
        key: original,
      }))
    : [];

  return (
    <div>
      {/* 解析文件名 */}
      <Card title="📝 解析文件名" style={{ marginBottom: 16 }}>
        <Form form={parseForm} onFinish={handleParse} layout="vertical">
          <Form.Item
            name="filename"
            label="文件名"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input
              placeholder="例如：The.Matrix.1999.1080p.BluRay.x264.mkv"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<FileTextOutlined />}
              loading={parseMutation.isPending}
            >
              解析
            </Button>
          </Form.Item>
        </Form>

        {parseResult && (
          <Descriptions column={2} bordered style={{ marginTop: 16 }}>
            <Descriptions.Item label="媒体类型">
              <Tag color="blue">{parseResult.media_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="标题">{parseResult.title}</Descriptions.Item>
            {parseResult.year && (
              <Descriptions.Item label="年份">{parseResult.year}</Descriptions.Item>
            )}
            {parseResult.season && (
              <Descriptions.Item label="季">S{parseResult.season}</Descriptions.Item>
            )}
            {parseResult.episode && (
              <Descriptions.Item label="集">E{parseResult.episode}</Descriptions.Item>
            )}
            {parseResult.resolution && (
              <Descriptions.Item label="分辨率">
                <Tag color="green">{parseResult.resolution}</Tag>
              </Descriptions.Item>
            )}
            {parseResult.codec && (
              <Descriptions.Item label="编码">
                <Tag>{parseResult.codec}</Tag>
              </Descriptions.Item>
            )}
            {parseResult.audio && (
              <Descriptions.Item label="音频">
                <Tag>{parseResult.audio}</Tag>
              </Descriptions.Item>
            )}
            {parseResult.source && (
              <Descriptions.Item label="来源">
                <Tag>{parseResult.source}</Tag>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="扩展名">{parseResult.extension}</Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      {/* 单文件重命名 */}
      <Card title="✏️ 单文件重命名" style={{ marginBottom: 16 }}>
        <Form form={renameForm} onFinish={handleRename} layout="vertical">
          <Form.Item
            name="filename"
            label="文件名"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input placeholder="例如：movie.2024.1080p.mkv" size="large" />
          </Form.Item>
          <Form.Item name="template" label="重命名模板">
            <Select placeholder="选择模板（可选）" allowClear>
              {templates && (
                <>
                  <Option value={templates.movie}>电影模板: {templates.movie}</Option>
                  <Option value={templates.tv}>电视剧模板: {templates.tv}</Option>
                  <Option value={templates.simple}>简单模板: {templates.simple}</Option>
                  <Option value={templates.detailed}>详细模板: {templates.detailed}</Option>
                </>
              )}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<EditOutlined />}
              loading={renameMutation.isPending}
            >
              重命名
            </Button>
          </Form.Item>
        </Form>

        {renameResult && (
          <Card type="inner" title="重命名结果" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <strong>原文件名：</strong>
                <br />
                <code>{renameResult.original}</code>
              </div>
              <div>
                <strong>新文件名：</strong>
                <br />
                <code style={{ color: '#52c41a' }}>{renameResult.renamed}</code>
              </div>
            </Space>
          </Card>
        )}
      </Card>

      {/* 批量重命名 */}
      <Card title="⚡ 批量重命名">
        <Form form={batchForm} onFinish={handleBatchRename} layout="vertical">
          <Form.Item
            name="filenames"
            label="文件名列表（每行一个）"
            rules={[{ required: true, message: '请输入文件名列表' }]}
          >
            <TextArea
              rows={6}
              placeholder="例如：&#10;movie1.2024.1080p.mkv&#10;movie2.2024.720p.mp4&#10;..."
            />
          </Form.Item>
          <Form.Item name="template" label="重命名模板">
            <Select placeholder="选择模板（可选）" allowClear>
              {templates && (
                <>
                  <Option value={templates.movie}>电影模板</Option>
                  <Option value={templates.tv}>电视剧模板</Option>
                  <Option value={templates.simple}>简单模板</Option>
                  <Option value={templates.detailed}>详细模板</Option>
                </>
              )}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<ThunderboltOutlined />}
              loading={batchRenameMutation.isPending}
            >
              批量重命名
            </Button>
          </Form.Item>
        </Form>

        {batchResult && (
          <Table
            dataSource={batchDataSource}
            columns={batchColumns}
            pagination={{ pageSize: 10 }}
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    </div>
  );
};

export default SmartRenamePanel;

