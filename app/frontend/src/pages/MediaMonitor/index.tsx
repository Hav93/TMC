import React from 'react';
import { Routes, Route } from 'react-router-dom';
import MonitorRulesList from './MonitorRulesList';
import MonitorRuleForm from './MonitorRuleForm';

const MediaMonitorPage: React.FC = () => {
  return (
    <Routes>
      <Route index element={<MonitorRulesList />} />
      <Route path="new" element={<MonitorRuleForm />} />
      <Route path=":id/edit" element={<MonitorRuleForm />} />
    </Routes>
  );
};

export default MediaMonitorPage;

