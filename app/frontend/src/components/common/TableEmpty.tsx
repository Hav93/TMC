import React from 'react';

interface TableEmptyProps {
  icon?: string;
  title?: string;
  description?: string;
}

const TableEmpty: React.FC<TableEmptyProps> = ({ 
  icon = '📋', 
  title = '暂无数据',
  description 
}) => {
  return (
    <div className="table-empty-state">
      <div className="table-empty-icon">{icon}</div>
      <div className="table-empty-title">{title}</div>
      {description && <div className="table-empty-description">{description}</div>}
    </div>
  );
};

export default TableEmpty;

