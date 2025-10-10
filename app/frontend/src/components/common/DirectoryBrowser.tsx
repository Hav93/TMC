/**
 * 目录浏览器组件
 * 支持 CloudDrive 远程目录和本地目录浏览
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
import { mediaSettingsApi, CloudDriveDirectory, LocalDirectory } from '../../services/mediaSettings';
import { useThemeContext } from '../../theme';

interface DirectoryBrowserProps {
  visible: boolean;
  onCancel: () => void;
  onSelect: (path: string) => void;
  type: 'clouddrive' | 'local';
  // CloudDrive 配置
  clouddriveUrl?: string;
  clouddriveUsername?: string | null;
  clouddrivePassword?: string | null;
  initialPath?: string;
}

export const DirectoryBrowser: React.FC<DirectoryBrowserProps> = ({
  visible,
  onCancel,
  onSelect,
  type,
  clouddriveUrl,
  clouddriveUsername,
  clouddrivePassword,
  initialPath = '/',
}) => {
  const { colors } = useThemeContext();
  const [directories, setDirectories] = useState<(CloudDriveDirectory | LocalDirectory)[]>([]);
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
      if (type === 'clouddrive') {
        if (!clouddriveUrl) {
          message.error('CloudDrive 服务地址未配置');
          return;
        }
        const result = await mediaSettingsApi.browseCloudDrive(
          clouddriveUrl,
          clouddriveUsername || null,
          clouddrivePassword || null,
          path
        );
        if (result.success) {
          setDirectories(result.directories);
          setCurrentPath(result.current_path);
        } else {
          message.error(result.message || '加载目录失败');
        }
      } else {
        const result = await mediaSettingsApi.getLocalDirectories(path);
        if (result.success) {
          setDirectories(result.directories);
          setCurrentPath(result.current_path);
          setParentPath(result.parent_path);
        }
      }
    } catch (error: any) {
      message.error(error.message || '加载目录失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始化和路径变化时加载
  useEffect(() => {
    if (visible) {
      loadDirectories(initialPath);
    }
  }, [visible]);

  // 处理目录点击
  const handleDirectoryClick = (dir: CloudDriveDirectory | LocalDirectory) => {
    loadDirectories(dir.path);
  };

  // 返回上级目录
  const handleGoUp = () => {
    if (type === 'clouddrive') {
      // CloudDrive: 解析父路径
      const parts = currentPath.split('/').filter(Boolean);
      parts.pop();
      const newPath = parts.length > 0 ? `/${parts.join('/')}` : '/';
      loadDirectories(newPath);
    } else {
      // Local: 使用 API 返回的父路径
      if (parentPath) {
        loadDirectories(parentPath);
      }
    }
  };

  // 返回根目录
  const handleGoHome = () => {
    loadDirectories(type === 'clouddrive' ? '/' : '/app');
  };

  // 确认选择
  const handleConfirm = () => {
    onSelect(currentPath);
    onCancel();
  };

  // 新建文件夹
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      message.warning('请输入文件夹名称');
      return;
    }

    setLoading(true);
    try {
      const newPath = `${currentPath}/${newFolderName}`.replace(/\/+/g, '/');
      
      if (type === 'clouddrive') {
        message.warning('CloudDrive 暂不支持创建文件夹');
        return;
      }
      
      // 调用本地文件夹创建 API（需要后端支持）
      const result = await mediaSettingsApi.createLocalDirectory(newPath);
      if (result.success) {
        message.success('文件夹创建成功');
        setNewFolderName('');
        setShowNewFolder(false);
        await loadDirectories(currentPath);
      } else {
        message.error(result.message || '创建文件夹失败');
      }
    } catch (error: any) {
      message.error(error.message || '创建文件夹失败');
    } finally {
      setLoading(false);
    }
  };

  // 重命名文件夹
  const handleRenameFolder = async (oldPath: string) => {
    if (!editFolderName.trim()) {
      message.warning('请输入新文件夹名称');
      return;
    }

    setLoading(true);
    try {
      if (type === 'clouddrive') {
        message.warning('CloudDrive 暂不支持重命名文件夹');
        return;
      }

      const parentDir = oldPath.substring(0, oldPath.lastIndexOf('/'));
      const newPath = `${parentDir}/${editFolderName}`.replace(/\/+/g, '/');
      
      const result = await mediaSettingsApi.renameLocalDirectory(oldPath, newPath);
      if (result.success) {
        message.success('文件夹重命名成功');
        setEditingFolder(null);
        setEditFolderName('');
        await loadDirectories(currentPath);
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
      if (type === 'clouddrive') {
        message.warning('CloudDrive 暂不支持删除文件夹');
        return;
      }

      const result = await mediaSettingsApi.deleteLocalDirectory(path);
      if (result.success) {
        message.success('文件夹删除成功');
        await loadDirectories(currentPath);
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
  const getBreadcrumbs = () => {
    const parts = currentPath.split('/').filter(Boolean);
    return [
      <Breadcrumb.Item key="root">
        <span onClick={handleGoHome} style={{ cursor: 'pointer' }}>
          <HomeOutlined /> {type === 'clouddrive' ? 'CloudDrive' : '根目录'}
        </span>
      </Breadcrumb.Item>,
      ...parts.map((part, index) => {
        const path = `/${parts.slice(0, index + 1).join('/')}`;
        return (
          <Breadcrumb.Item key={path}>
            <span onClick={() => loadDirectories(path)} style={{ cursor: 'pointer' }}>
              {part}
            </span>
          </Breadcrumb.Item>
        );
      }),
    ];
  };

  return (
    <>
      <style>{`
        .directory-browser-item {
          cursor: pointer !important;
          padding: 12px 16px !important;
          border-radius: 4px !important;
          transition: background-color 0.2s !important;
        }
        .directory-browser-item:hover {
          background-color: ${colors.bgSecondary} !important;
        }
      `}</style>
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <FolderOpenOutlined style={{ marginRight: 8 }} />
            <span>选择目录</span>
          </div>
        }
        open={visible}
        onCancel={onCancel}
        width={700}
        closeIcon={
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 16, cursor: 'pointer' }}>×</span>
            <Button
              type="text"
              icon={<ReloadOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                loadDirectories(currentPath);
              }}
              loading={loading}
              title="刷新"
              size="small"
            />
          </div>
        }
        footer={[
          <Button key="back" onClick={onCancel}>
            取消
          </Button>,
          <Button key="submit" type="primary" onClick={handleConfirm}>
            选择当前目录
          </Button>,
        ]}
      >
      {/* 面包屑导航 */}
      <div style={{ marginBottom: 16 }}>
        <Breadcrumb>{getBreadcrumbs()}</Breadcrumb>
      </div>

      {/* 当前路径显示 */}
      <Input
        value={currentPath}
        readOnly
        addonBefore="当前路径"
        style={{ marginBottom: 16 }}
      />

      {/* 新建文件夹输入框 */}
      {showNewFolder && type === 'local' && (
        <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
          <Input
            placeholder="输入文件夹名称"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onPressEnter={handleCreateFolder}
            autoFocus
          />
          <Button type="primary" onClick={handleCreateFolder} loading={loading}>
            确认
          </Button>
          <Button onClick={() => {
            setShowNewFolder(false);
            setNewFolderName('');
          }}>
            取消
          </Button>
        </div>
      )}

      {/* 目录列表 */}
      <Spin spinning={loading}>
        <div style={{ minHeight: 300, maxHeight: 400, overflow: 'auto' }}>
          <List
            dataSource={directories}
            locale={{ emptyText: '此目录为空' }}
            renderItem={(dir) => (
              <List.Item
                className="directory-browser-item"
                style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 16px'
                }}
              >
                <div 
                  style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12 }}
                  onClick={() => handleDirectoryClick(dir)}
                >
                  <FolderOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                  {type === 'local' && editingFolder === dir.path ? (
                    <Input
                      value={editFolderName}
                      onChange={(e) => setEditFolderName(e.target.value)}
                      onPressEnter={() => handleRenameFolder(dir.path)}
                      onBlur={() => setEditingFolder(null)}
                      autoFocus
                      onClick={(e) => e.stopPropagation()}
                      style={{ maxWidth: 300 }}
                    />
                  ) : (
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500 }}>{dir.name}</div>
                      <div style={{ fontSize: 12, opacity: 0.6 }}>路径: {dir.path}</div>
                    </div>
                  )}
                </div>
                
                {type === 'local' && (
                  <Space size="small" onClick={(e) => e.stopPropagation()}>
                    <Button
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      title="重命名"
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingFolder(dir.path);
                        setEditFolderName(dir.name);
                      }}
                    />
                    <Popconfirm
                      title="确认删除"
                      description={`确定要删除文件夹 "${dir.name}" 吗？`}
                      onConfirm={(e) => {
                        e?.stopPropagation();
                        handleDeleteFolder(dir.path);
                      }}
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<DeleteOutlined />}
                        danger
                        title="删除"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  </Space>
                )}
              </List.Item>
            )}
          />
        </div>
      </Spin>

      {/* 快捷操作 */}
      <div style={{ marginTop: 16, display: 'flex', gap: 8, justifyContent: 'space-between' }}>
        <Space>
          <Button
            icon={<HomeOutlined />}
            onClick={handleGoHome}
            disabled={currentPath === (type === 'clouddrive' ? '/' : '/app')}
          >
            根目录
          </Button>
          <Button
            onClick={handleGoUp}
            disabled={currentPath === (type === 'clouddrive' ? '/' : '/app')}
          >
            上级目录
          </Button>
        </Space>
        
        {type === 'local' && (
          <Button
            type="primary"
            icon={<FolderAddOutlined />}
            onClick={() => setShowNewFolder(true)}
            disabled={showNewFolder}
          >
            新建文件夹
          </Button>
        )}
      </div>
    </Modal>
    </>
  );
};

