/**
 * 资源监控主页面
 */
import React, { useState } from 'react';
import { Card, Tabs, message } from 'antd';
import { FileTextOutlined, DatabaseOutlined } from '@ant-design/icons';
import RuleList from './RuleList';
import RecordList from './RecordList';

const { TabPane } = Tabs;

const ResourceMonitor: React.FC = () => {
  const [activeTab, setActiveTab] = useState('rules');

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'rules',
              label: (
                <span>
                  <FileTextOutlined />
                  监控规则
                </span>
              ),
              children: <RuleList />,
            },
            {
              key: 'records',
              label: (
                <span>
                  <DatabaseOutlined />
                  资源记录
                </span>
              ),
              children: <RecordList />,
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default ResourceMonitor;

