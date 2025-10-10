import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const MonitorRuleFormTest: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={4}>测试页面</Title>
        <p>如果你能看到这个，说明路由和基本组件是正常的。</p>
      </Card>
    </div>
  );
};

export default MonitorRuleFormTest;

