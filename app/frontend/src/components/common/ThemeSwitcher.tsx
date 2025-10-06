import React from 'react';
import { Button, Tooltip } from 'antd';
import { BulbFilled, BulbOutlined } from '@ant-design/icons';
import { useThemeContext } from '../../theme';

const ThemeSwitcher: React.FC = () => {
  const { themeType, colors, toggleTheme } = useThemeContext();

  const handleClick = (e: React.MouseEvent<HTMLElement>) => {
    toggleTheme(e);
  };

  return (
    <Tooltip title={`切换到${themeType === 'light' ? '夜间' : '日间'}模式`}>
      <Button
        type="text"
        icon={themeType === 'light' ? <BulbFilled /> : <BulbOutlined />}
        onClick={handleClick}
        style={{
          fontSize: '20px',
          color: themeType === 'light' ? colors.warning : colors.info,
          width: '40px',
          height: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease-out',
        }}
      />
    </Tooltip>
  );
};

export default ThemeSwitcher;

