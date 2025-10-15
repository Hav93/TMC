/**
 * STRM生成面板
 */
import React, { useState } from 'react';
import { Card, Button, Input, Form, message, Space, Switch, Select, Alert } from 'antd';
import { PlayCircleOutlined, FileAddOutlined } from '@ant-design/icons';
import { useMutation } from '@tanstack/react-query';
import stage6Service from '../../services/stage6';

const { TextArea } = Input;
const { Option } = Select;

const StrmGeneratorPanel: React.FC = () => {
  const [simpleForm] = Form.useForm();
  const [advancedForm] = Form.useForm();
  const [result, setResult] = useState<any>(null);

  // 简单生成
  const simpleMutation = useMutation({
    mutationFn: (values: { media_url: string; output_dir: string; filename: string }) =>
      stage6Service.generateStrmSimple(values.media_url, values.output_dir, values.filename),
    onSuccess: (data) => {
      setResult(data);
      message.success('STRM文件生成成功');
    },
  });

  // 高级生成
  const advancedMutation = useMutation({
    mutationFn: (values: any) => stage6Service.generateStrm(values),
    onSuccess: (data) => {
      setResult(data);
      message.success('STRM/NFO文件生成成功');
    },
  });

  const handleSimpleGenerate = (values: any) => {
    simpleMutation.mutate(values);
  };

  const handleAdvancedGenerate = (values: any) => {
    advancedMutation.mutate(values);
  };

  return (
    <div>
      <Alert
        message="STRM文件说明"
        description="STRM文件是一种流媒体快捷方式，可以让Emby、Jellyfin、Plex等媒体服务器直接播放115网盘中的文件，无需下载到本地。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {/* 简单生成 */}
      <Card title="🚀 快速生成" style={{ marginBottom: 16 }}>
        <Form form={simpleForm} onFinish={handleSimpleGenerate} layout="vertical">
          <Form.Item
            name="media_url"
            label="媒体URL"
            rules={[{ required: true, message: '请输入媒体URL' }]}
          >
            <Input
              placeholder="例如：https://115.com/s/abc123?password=xyz"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="output_dir"
            label="输出目录"
            rules={[{ required: true, message: '请输入输出目录' }]}
          >
            <Input placeholder="例如：/media/movies" size="large" />
          </Form.Item>
          <Form.Item
            name="filename"
            label="文件名（不含扩展名）"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input placeholder="例如：The Matrix (1999)" size="large" />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlayCircleOutlined />}
              loading={simpleMutation.isPending}
            >
              生成STRM
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 高级生成 */}
      <Card title="⚙️ 高级生成（含NFO元数据）">
        <Form form={advancedForm} onFinish={handleAdvancedGenerate} layout="vertical">
          <Form.Item
            name="media_url"
            label="媒体URL"
            rules={[{ required: true, message: '请输入媒体URL' }]}
          >
            <Input placeholder="媒体文件的URL" size="large" />
          </Form.Item>
          <Form.Item
            name="output_dir"
            label="输出目录"
            rules={[{ required: true, message: '请输入输出目录' }]}
          >
            <Input placeholder="STRM文件保存路径" size="large" />
          </Form.Item>
          <Form.Item
            name="filename"
            label="文件名"
            rules={[{ required: true, message: '请输入文件名' }]}
          >
            <Input placeholder="文件名（不含扩展名）" size="large" />
          </Form.Item>

          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item
              name="include_nfo"
              label="生成NFO元数据文件"
              valuePropName="checked"
              initialValue={false}
            >
              <Switch />
            </Form.Item>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.include_nfo !== currentValues.include_nfo
              }
            >
              {({ getFieldValue }) =>
                getFieldValue('include_nfo') ? (
                  <>
                    <Form.Item name="nfo_type" label="NFO类型" initialValue="movie">
                      <Select>
                        <Option value="movie">电影</Option>
                        <Option value="tvshow">电视剧</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item name="title" label="标题">
                      <Input placeholder="媒体标题" />
                    </Form.Item>
                    <Form.Item name="year" label="年份">
                      <Input type="number" placeholder="发行年份" />
                    </Form.Item>
                    <Form.Item name="plot" label="剧情简介">
                      <TextArea rows={3} placeholder="剧情描述" />
                    </Form.Item>
                    <Form.Item name="genre" label="类型">
                      <Input placeholder="例如：动作/科幻" />
                    </Form.Item>
                    <Form.Item name="rating" label="评分">
                      <Input type="number" step="0.1" placeholder="0-10" />
                    </Form.Item>
                  </>
                ) : null
              }
            </Form.Item>
          </Space>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<FileAddOutlined />}
              loading={advancedMutation.isPending}
            >
              生成STRM + NFO
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 生成结果 */}
      {result && (
        <Card title="✅ 生成结果" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            {result.strm && (
              <div>
                <strong>STRM文件路径：</strong>
                <br />
                <code>{result.strm}</code>
              </div>
            )}
            {result.nfo && (
              <div>
                <strong>NFO文件路径：</strong>
                <br />
                <code>{result.nfo}</code>
              </div>
            )}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default StrmGeneratorPanel;

