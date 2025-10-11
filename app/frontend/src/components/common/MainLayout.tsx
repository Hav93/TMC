import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Button,
  Avatar,
  Space,
  Dropdown,
  message,
} from 'antd';
import { useQuery } from '@tanstack/react-query';
import {
  DashboardOutlined,
  SettingOutlined,
  FileTextOutlined,
  MessageOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  ContainerOutlined,
  LogoutOutlined,
  SafetyOutlined,
  CloudDownloadOutlined,
  DownloadOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons';
import ThemeSwitcher from './ThemeSwitcher';
import { useAuth } from '../../contexts/AuthContext';
import { useThemeContext } from '../../theme';

const { Header, Sider } = Layout;

// 菜单项配置 - 按功能分组优化
const menuItems = [
  // 仪表板 - 入口
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表板',
    path: '/dashboard',
    title: '📊 仪表板',
    description: '系统运行状态和数据统计概览',
    group: 'overview',
  },
  
  // 消息转发 - 核心功能组
  {
    key: 'divider-1',
    type: 'divider',
    group: 'message',
  },
  {
    key: '/chats',
    icon: <MessageOutlined />,
    label: '聊天管理',
    path: '/chats',
    title: '💬 聊天管理',
    description: '管理群组和频道信息',
    group: 'message',
  },
  {
    key: '/rules',
    icon: <SettingOutlined />,
    label: '转发规则',
    path: '/rules',
    title: '⚙️ 转发规则',
    description: '配置和管理消息转发规则',
    group: 'message',
  },
  {
    key: '/system-logs',
    icon: <FileTextOutlined />,
    label: '消息日志',
    path: '/system-logs',
    title: '📝 消息日志',
    description: '查看消息转发历史记录',
    group: 'message',
  },
  
  // 媒体管理 - 扩展功能组
  {
    key: 'divider-2',
    type: 'divider',
    group: 'media',
  },
  {
    key: '/media-monitor',
    icon: <CloudDownloadOutlined />,
    label: '媒体监控',
    path: '/media-monitor',
    title: '📥 媒体监控',
    description: '自动下载和管理媒体文件',
    group: 'media',
  },
  {
    key: '/download-tasks',
    icon: <DownloadOutlined />,
    label: '下载任务',
    path: '/download-tasks',
    title: '⬇️ 下载任务',
    description: '查看媒体文件下载进度和队列',
    group: 'media',
  },
  {
    key: '/media-library',
    icon: <FolderOpenOutlined />,
    label: '媒体文件库',
    path: '/media-library',
    title: '📁 媒体文件库',
    description: '浏览和管理已下载的媒体文件',
    group: 'media',
  },
  {
    key: '/resource-monitor',
    icon: <LinkOutlined />,
    label: '资源监控',
    path: '/resource-monitor',
    title: '📚 资源监控',
    description: '监控Telegram消息中的资源链接并自动转存到115',
    group: 'media',
  },
  
  // 系统管理 - 系统功能组
  {
    key: 'divider-3',
    type: 'divider',
    group: 'system',
  },
  {
    key: '/clients',
    icon: <TeamOutlined />,
    label: '客户端管理',
    path: '/clients',
    title: '🤖 客户端管理',
    description: '管理Telegram客户端实例',
    group: 'system',
  },
  {
    key: '/container-logs',
    icon: <ContainerOutlined />,
    label: '容器日志',
    path: '/container-logs',
    title: '🐳 容器日志',
    description: '实时查看Docker容器运行日志',
    group: 'system',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
    path: '/settings',
    title: '🔧 系统设置',
    description: '配置系统参数和Bot设置',
    group: 'system',
  },
];

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { user, logout } = useAuth();

  // 获取系统信息
  const { data: systemInfo } = useQuery({
    queryKey: ['systemInfo'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/system/enhanced-status', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (!response.ok) {
        throw new Error('Failed to fetch system info');
      }
      return response.json();
    },
    refetchInterval: 30000, // 每30秒刷新一次
  });

  // 处理登出
  const handleLogout = async () => {
    try {
      await logout();
      message.success('已登出');
      navigate('/login');
    } catch (error) {
      console.error('登出失败:', error);
    }
  };

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => navigate('/profile'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
      danger: true,
    },
  ];

  // 菜单点击处理
  const handleMenuClick = (key: string) => {
    const item = menuItems.find(item => item.key === key && item.type !== 'divider');
    if (item && item.path) {
      navigate(item.path);
    }
  };

  // 获取当前选中的菜单
  const getSelectedKeys = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if (item.type !== 'divider' && item.key && path.startsWith(item.key)) {
        return [item.key];
      }
    }
    return ['/dashboard'];
  };

  // 获取当前页面信息
  const getCurrentPageInfo = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if (item.type !== 'divider' && item.key && path.startsWith(item.key)) {
        return { title: item.title, description: item.description };
      }
    }
    return { title: '📊 仪表板', description: '系统运行状态和数据统计概览' };
  };

  const currentPageInfo = getCurrentPageInfo();

  return (
    <div className="main-layout-wrapper" style={{ height: '100vh', overflow: 'hidden' }}>
      {/* 固定的侧边栏 */}
      <Sider
        className="fixed-sidebar"
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        width={240}
        collapsedWidth={80}
        style={{
          position: 'fixed',
          left: 0,
          top: 0,
          height: '100vh',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Logo区域 (TMC v1.1) */}
        <div
          className="sidebar-logo"
          style={{
            minHeight: sidebarCollapsed ? 64 : 88,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: sidebarCollapsed ? '16px 8px' : '16px 24px',
            gap: 4,
          }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: sidebarCollapsed ? 0 : 12,
          }}>
            {/* TMC Logo */}
            <div
              className="sidebar-logo-icon"
              style={{
                width: sidebarCollapsed ? 32 : 36,
                height: sidebarCollapsed ? 32 : 36,
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 'bold',
                fontSize: sidebarCollapsed ? 14 : 16,
                color: '#ffffff',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
              }}
            >
              <span style={{ color: '#ffffff', fontWeight: 'bold' }}>TMC</span>
            </div>
            {!sidebarCollapsed && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                <span className="sidebar-logo-text" style={{ 
                  fontSize: 16, 
                  fontWeight: 700,
                  lineHeight: 1.2,
                  color: '#fff', // TMC保持白色
                }}>
                  TMC
                </span>
                <span className="sidebar-logo-subtitle" style={{ 
                  fontSize: 10, 
                  fontWeight: 400,
                  lineHeight: 1.2,
                  // Message Central根据主题调整颜色
                  color: 'var(--color-text-secondary)',
                  opacity: 0.85,
                }}>
                  Message Central
                </span>
              </div>
            )}
          </div>
          
          <div className="sidebar-version" style={{ 
            fontSize: sidebarCollapsed ? 10 : 11, 
            opacity: 0.9, 
            textAlign: 'center',
            fontWeight: 500,
          }}>
            v{systemInfo?.version || '1.1.0'}
          </div>
        </div>

        {/* 菜单区域 - 占用剩余空间 */}
        <div style={{ flex: 1, overflow: 'auto' }}>
          <Menu
            mode="inline"
            selectedKeys={getSelectedKeys()}
            style={{
              border: 'none',
              background: 'transparent',
              height: '100%',
            }}
            items={menuItems.map(item => {
              // 处理分隔线
              if (item.type === 'divider') {
                return {
                  key: item.key,
                  type: 'divider' as const,
                  style: { margin: '8px 0' },
                };
              }
              // 处理普通菜单项
              return {
                key: item.key,
                icon: item.icon,
                label: item.label,
                onClick: () => handleMenuClick(item.key),
              };
            })}
          />
        </div>

        {/* 折叠/展开按钮 - 绝对底部位置 */}
        <div
          className="sidebar-footer"
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            padding: '16px',
            display: 'flex',
            justifyContent: 'center',
          }}
        >
          <Button
            className="sidebar-collapse-btn"
            type="text"
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              fontSize: 16,
              width: 40,
              height: 40,
              borderRadius: '8px',
              transition: 'all 0.3s ease',
            }}
          />
        </div>
      </Sider>

      {/* 右侧主区域：header + content */}
      <div
        style={{
          marginLeft: sidebarCollapsed ? 80 : 240,
          width: `calc(100vw - ${sidebarCollapsed ? 80 : 240}px)`,
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          transition: 'margin-left 0.3s ease, width 0.3s ease',
        }}
      >
        {/* 顶部导航栏 - 不再fixed，在正常文档流中 */}
        <Header 
          className="layout-header"
          style={{
            height: 64,
            flexShrink: 0,
            zIndex: 11,
            padding: 0,
          }}
        >
          <div className="header-content" style={{ padding: '0 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            {/* 左侧：页面信息（占更多空间） */}
            <div style={{ flex: 1, maxWidth: 'calc(100% - 200px)' }}>
              <div className="header-title" style={{ 
                fontSize: 20, 
                fontWeight: 600,
                display: 'block',
                lineHeight: 1.2,
              }}>
                {currentPageInfo.title}
              </div>
              <div className="header-description" style={{ 
                fontSize: 13, 
                opacity: 0.85, 
                marginTop: 2,
                lineHeight: 1.3,
              }}>
                {currentPageInfo.description}
              </div>
            </div>

            {/* 右侧：主题切换器和用户信息 */}
            <Space align="center" size={16}>
              <ThemeSwitcher />
              
              {/* 用户信息下拉菜单 */}
              <Dropdown 
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                trigger={['click']}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: 12, 
                  cursor: 'pointer',
                  padding: '4px 12px',
                  borderRadius: '8px',
                  transition: 'background 0.3s ease',
                }}
                className="user-info-dropdown">
                  <Avatar
                    size={36}
                    src={user?.avatar}
                    icon={<UserOutlined />}
                    style={{ 
                      fontSize: 16,
                      backgroundColor: user?.is_admin ? '#f56a00' : '#1890ff',
                    }}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span style={{ fontSize: 14, fontWeight: 500, lineHeight: 1.2 }}>
                      {user?.username || '用户'}
                    </span>
                    {user?.is_admin && (
                      <span style={{ 
                        fontSize: 11, 
                        opacity: 0.7, 
                        lineHeight: 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                      }}>
                        <SafetyOutlined style={{ fontSize: 10 }} />
                        管理员
                      </span>
                    )}
                  </div>
                </div>
              </Dropdown>
            </Space>
          </div>
        </Header>

        {/* 主内容区域 - 自然在header下方，可以滚动 */}
        <div
          className="main-content-area"
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px',
            background: 'transparent',
          }}
        >
          <div className="fade-in">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainLayout;