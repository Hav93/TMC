/**
 * 本地目录浏览器组件
 * 仅支持本地目录浏览
 */
import React, { useState, useEffect } from 'react';
import { Modal, List, Button, Spin, message, Input, Breadcrumb, Popconfirm, Space } from 'antd';
import {
  FolderOutlined,
  HomeOutlined,
  ReloadOutlined,
  FolderOpenOutlined,
  FolderAddOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { mediaSettingsApi, LocalDirectory } from '../../services/mediaSettings';
import { useThemeContext } from '../../theme';

interface DirectoryBrowserProps {
  visible: boolean;
  onCancel: () => void;
  onSelect: (path: string) => void;
  initialPath?: string;
}

export const DirectoryBrowser: React.FC<DirectoryBrowserProps> = ({
  visible,
  onCancel,
  onSelect,
  initialPath = '/app',
}) => {
  const { colors } = useThemeContext();
  const [directories, setDirectories] = useState<LocalDirectory[]>([]);
  const [currentPath, setCurrentPath] = useState<string>(initialPath);
  const [loading, setLoading] = useState(false);
  const [parentPath, setParentPath] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [editingFolder, setEditingFolder] = useState<string | null>(null);
  const [editFolderName, setEditFolderName] = useState('');

  // 加载目录列表
  const loadDirectories = async (path: string) => {
    setLoading(true);
    try {
      const result = await mediaSettingsApi.getLocalDirectories(path);
      
      if (result.success) {
        setDirectories(result.directories || []);
        setCurrentPath(result.current_path);
        setParentPath(result.parent_path);
      } else {
        message.error(result.message || '加载目录失败');
      }
    } catch (error: any) {
      message.error(error.message || '加载目录失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    if (visible) {
      loadDirectories(currentPath);
    }
  }, [visible]);

  // 处理目录点击
  const handleDirectoryClick = (dir: LocalDirectory) => {
    loadDirectories(dir.path);
  };

  // 返回上级目录
  const handleGoUp = () => {
    if (parentPath) {
      loadDirectories(parentPath);
    }
  };

  // 返回根目录
  const handleGoHome = () => {
    loadDirectories('/app');
  };

  // 创建新文件夹
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      message.warning('请输入文件夹名称');
      return;
    }

    setLoading(true);
    try {
      const newPath = `${currentPath}/${newFolderName}`.replace(/\/+/g, '/');
      
      const result = await mediaSettingsApi.createLocalDirectory(newPath);
      
      if (result.success) {
        message.success('文件夹创建成功');
        setNewFolderName('');
        setShowNewFolder(false);
        loadDirectories(currentPath);
      } else {
        message.error(result.message || '创建失败');
      }
    } catch (error: any) {
      message.error(error.message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  // 重命名文件夹
  const handleRenameFolder = async (oldPath: string) => {
    if (!editFolderName.trim()) {
      message.warning('请输入新名称');
      return;
    }

    setLoading(true);
    try {
      const parentDir = oldPath.substring(0, oldPath.lastIndexOf('/'));
      const newPath = `${parentDir}/${editFolderName}`.replace(/\/+/g, '/');
      
      const result = await mediaSettingsApi.renameLocalDirectory(oldPath, newPath);
      
      if (result.success) {
        message.success('重命名成功');
        setEditingFolder(null);
        setEditFolderName('');
        loadDirectories(currentPath);
      } else {
        message.error(result.message || '重命名失败');
      }
    } catch (error: any) {
      message.error(error.message || '重命名失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除文件夹
  const handleDeleteFolder = async (path: string) => {
    setLoading(true);
    try {
      const result = await mediaSettingsApi.deleteLocalDirectory(path);
      
      if (result.success) {
        message.success('删除成功');
        loadDirectories(currentPath);
      } else {
        message.error(result.message || '删除失败');
      }
    } catch (error: any) {
      message.error(error.message || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成面包屑
  const breadcrumbItems = () => {
    const parts = currentPath.split('/').filter(Boolean);
    const items = [
      <Breadcrumb.Item key="root">
        <span onClick={handleGoHome} style={{ cursor: 'pointer' }}>
          <HomeOutlined /> 根目录
        </span>
      </Breadcrumb.Item>,
    ];

    let accumulatedPath = '';
    parts.forEach((part, index) => {
      accumulatedPath += `/${part}`;
      const pathToNavigate = accumulatedPath;
      items.push(
        <Breadcrumb.Item key={index}>
          <span 
            onClick={() => loadDirectories(pathToNavigate)} 
            style={{ cursor: 'pointer' }}
          >
            {part}
          </span>
        </Breadcrumb.Item>
      );
    });

    return items;
  };

  return (
    <Modal
      title="选择本地目录"
      open={visible}
      onCancel={onCancel}
      width={800}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="select" type="primary" onClick={() => onSelect(currentPath)}>
          选择当前目录
        </Button>,
      ]}
      styles={{
        body: { 
          maxHeight: '60vh', 
          overflowY: 'auto',
          background: colors.cardBg 
        }
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb style={{ marginBottom: 12 }}>
          {breadcrumbItems()}
        </Breadcrumb>

        <Space>
          <Button
            icon={<HomeOutlined />}
            onClick={handleGoHome}
            disabled={currentPath === '/app'}
          >
            根目录
          </Button>
          <Button
            onClick={handleGoUp}
            disabled={currentPath === '/app'}
          >
            上级目录
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => loadDirectories(currentPath)}>
            刷新
          </Button>
          <Button 
            icon={<FolderAddOutlined />} 
            onClick={() => setShowNewFolder(true)}
            type="dashed"
          >
            新建文件夹
          </Button>
        </Space>

        {showNewFolder && (
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <Input
              placeholder="输入文件夹名称"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onPressEnter={handleCreateFolder}
              style={{ flex: 1 }}
            />
            <Button type="primary" onClick={handleCreateFolder}>
              创建
            </Button>
            <Button onClick={() => {
              setShowNewFolder(false);
              setNewFolderName('');
            }}>
              取消
            </Button>
          </div>
        )}
      </div>

      <Spin spinning={loading}>
        <List
          dataSource={directories}
          locale={{ emptyText: '当前目录为空' }}
          renderItem={(dir) => (
            <List.Item
              key={dir.path}
              style={{
                cursor: 'pointer',
                padding: '12px',
                background: colors.cardBg,
                borderRadius: '4px',
                marginBottom: '4px',
                border: `1px solid ${colors.borderColor}`,
              }}
              actions={[
                <Button
                  key="edit"
                  type="text"
                  icon={<EditOutlined />}
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingFolder(dir.path);
                    setEditFolderName(dir.name);
                  }}
                />,
                <Popconfirm
                  key="delete"
                  title="确定删除此文件夹？"
                  description="只能删除空文件夹"
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    handleDeleteFolder(dir.path);
                  }}
                  onCancel={(e) => e?.stopPropagation()}
                  okText="确认"
                  cancelText="取消"
                >
                  <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    size="small"
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>,
              ]}
            >
              {editingFolder === dir.path ? (
                <div style={{ display: 'flex', gap: 8, width: '100%' }} onClick={(e) => e.stopPropagation()}>
                  <Input
                    value={editFolderName}
                    onChange={(e) => setEditFolderName(e.target.value)}
                    onPressEnter={() => handleRenameFolder(dir.path)}
                    style={{ flex: 1 }}
                    autoFocus
                  />
                  <Button type="primary" size="small" onClick={() => handleRenameFolder(dir.path)}>
                    确认
                  </Button>
                  <Button size="small" onClick={() => {
                    setEditingFolder(null);
                    setEditFolderName('');
                  }}>
                    取消
                  </Button>
                </div>
              ) : (
                <div
                  style={{ display: 'flex', alignItems: 'center', width: '100%' }}
                  onClick={() => handleDirectoryClick(dir)}
                >
                  <FolderOutlined style={{ marginRight: 8, fontSize: 16, color: colors.primary }} />
                  <span style={{ flex: 1, color: colors.textPrimary }}>{dir.name}</span>
                  <span style={{ 
                    fontSize: 12, 
                    color: colors.textSecondary,
                    marginLeft: 16 
                  }}>
                    {new Date(dir.modified * 1000).toLocaleString('zh-CN')}
                  </span>
                </div>
              )}
            </List.Item>
          )}
        />
      </Spin>
    </Modal>
  );
};

export default DirectoryBrowser;
