/**
 * 阶段6工具集主页面
 */
import React, { useState } from 'react';
import { Card, Tabs, Typography } from 'antd';
import {
  FilterOutlined,
  ThunderboltOutlined,
  EditOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import AdFilterPanel from './AdFilterPanel';
import QuickUploadPanel from './QuickUploadPanel';
import SmartRenamePanel from './SmartRenamePanel';
import StrmGeneratorPanel from './StrmGeneratorPanel';
import OfflineDownload from './OfflineDownload';

const { Title, Paragraph } = Typography;

const Stage6Tools: React.FC = () => {
  const [activeTab, setActiveTab] = useState('ad-filter');

  const tabItems = [
    {
      key: 'ad-filter',
      label: (
        <span>
          <FilterOutlined />
          广告过滤
        </span>
      ),
      children: <AdFilterPanel />,
    },
    {
      key: 'quick-upload',
      label: (
        <span>
          <ThunderboltOutlined />
          秒传检测
        </span>
      ),
      children: <QuickUploadPanel />,
    },
    {
      key: 'smart-rename',
      label: (
        <span>
          <EditOutlined />
          智能重命名
        </span>
      ),
      children: <SmartRenamePanel />,
    },
    {
      key: 'strm-generator',
      label: (
        <span>
          <PlayCircleOutlined />
          STRM生成
        </span>
      ),
      children: <StrmGeneratorPanel />,
    },
    {
      key: 'offline-download',
      label: (
        <span>
          <DownloadOutlined />
          离线下载
        </span>
      ),
      children: <OfflineDownload />,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={2}>🛠️ 高级工具集</Title>
        <Paragraph>
          借鉴115Bot的优秀功能，提供广告过滤、秒传检测、智能重命名和STRM生成等高级工具。
        </Paragraph>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
        />
      </Card>
    </div>
  );
};

export default Stage6Tools;

