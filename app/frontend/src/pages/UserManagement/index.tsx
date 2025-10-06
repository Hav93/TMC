import React, { useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Switch, 
  message,
  Popconfirm,
  Typography,
  Tooltip
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SafetyOutlined,
  LockOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../../services/users';
import type { User, CreateUserRequest, UpdateUserRequest } from '../../types/user';
import dayjs from 'dayjs';
import { useAuth } from '../../contexts/AuthContext';

const { Title, Text } = Typography;

const UserManagement: React.FC = () => {
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [resetPasswordModalVisible, setResetPasswordModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [addForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [resetPasswordForm] = Form.useForm();
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();

  // 获取用户列表
  const { data: usersData, isLoading, refetch } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(),
  });

  // 创建用户
  const createUserMutation = useMutation({
    mutationFn: (data: CreateUserRequest) => usersApi.create(data),
    onSuccess: () => {
      message.success('用户创建成功！');
      setAddModalVisible(false);
      addForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '创建用户失败');
    },
  });

  // 更新用户
  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) => 
      usersApi.update(id, data),
    onSuccess: () => {
      message.success('用户信息更新成功！');
      setEditModalVisible(false);
      setSelectedUser(null);
      editForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '更新用户失败');
    },
  });

  // 删除用户
  const deleteUserMutation = useMutation({
    mutationFn: (id: number) => usersApi.delete(id),
    onSuccess: () => {
      message.success('用户删除成功！');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '删除用户失败');
    },
  });

  // 重置密码
  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) => 
      usersApi.resetPassword(id, password),
    onSuccess: () => {
      message.success('密码重置成功！');
      setResetPasswordModalVisible(false);
      setSelectedUser(null);
      resetPasswordForm.resetFields();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '重置密码失败');
    },
  });

  // 处理创建用户
  const handleAddUser = async () => {
    try {
      const values = await addForm.validateFields();
      createUserMutation.mutate(values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 处理编辑用户
  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    editForm.setFieldsValue({
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
      is_admin: user.is_admin,
    });
    setEditModalVisible(true);
  };

  // 处理更新用户
  const handleUpdateUser = async () => {
    try {
      const values = await editForm.validateFields();
      if (selectedUser) {
        updateUserMutation.mutate({ id: selectedUser.id, data: values });
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 处理重置密码
  const handleResetPassword = (user: User) => {
    setSelectedUser(user);
    setResetPasswordModalVisible(true);
  };

  const handleResetPasswordSubmit = async () => {
    try {
      const values = await resetPasswordForm.validateFields();
      if (selectedUser) {
        resetPasswordMutation.mutate({ 
          id: selectedUser.id, 
          password: values.new_password 
        });
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <UserOutlined />
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.id === currentUser?.id && (
            <Tag color="blue">当前用户</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      render: (text: string) => text || <Text type="secondary">未设置</Text>,
    },
    {
      title: '全名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text: string) => text || <Text type="secondary">未设置</Text>,
    },
    {
      title: '角色',
      dataIndex: 'is_admin',
      key: 'is_admin',
      render: (is_admin: boolean) => (
        <Tag icon={<SafetyOutlined />} color={is_admin ? 'red' : 'default'}>
          {is_admin ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean) => (
        <Tag color={is_active ? 'success' : 'default'}>
          {is_active ? '激活' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (text: string) => 
        text ? dayjs(text).format('YYYY-MM-DD HH:mm') : <Text type="secondary">从未登录</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          <Tooltip title="重置密码">
            <Button
              type="text"
              icon={<LockOutlined />}
              onClick={() => handleResetPassword(record)}
            />
          </Tooltip>
          <Tooltip title={record.id === currentUser?.id ? '不能删除自己' : '删除'}>
            <Popconfirm
              title="确认删除"
              description={`确定要删除用户 "${record.username}" 吗？`}
              onConfirm={() => deleteUserMutation.mutate(record.id)}
              okText="删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
              disabled={record.id === currentUser?.id}
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                disabled={record.id === currentUser?.id}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '0 16px' }}>
      {/* 页面标题 */}
      <Card className="glass-card" style={{ marginBottom: '16px' }} bordered={false}>
        <Title level={3} style={{ 
          margin: 0, 
          color: 'var(--color-text-primary)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <SafetyOutlined />
          用户管理
        </Title>
        <Text style={{ 
          color: 'var(--color-text-secondary)', 
          fontSize: '14px'
        }}>
          管理系统用户账号，分配角色和权限
        </Text>
      </Card>

      {/* 用户列表 */}
      <Card
        className="glass-card"
        title={`用户列表 (${usersData?.total || 0})`}
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => refetch()}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAddModalVisible(true)}
            >
              添加用户
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={usersData?.users || []}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
      </Card>

      {/* 添加用户模态框 */}
      <Modal
        title={
          <span style={{ color: 'var(--color-text-primary)' }}>
            <PlusOutlined style={{ marginRight: 8 }} />
            添加用户
          </span>
        }
        open={addModalVisible}
        onOk={handleAddUser}
        onCancel={() => {
          setAddModalVisible(false);
          addForm.resetFields();
        }}
        confirmLoading={createUserMutation.isPending}
      >
        <Form
          form={addForm}
          layout="vertical"
          initialValues={{ is_admin: false }}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="请输入用户名" />
          </Form.Item>

          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入密码" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input placeholder="请输入邮箱（可选）" />
          </Form.Item>

          <Form.Item
            label="全名"
            name="full_name"
          >
            <Input placeholder="请输入全名（可选）" />
          </Form.Item>

          <Form.Item
            label="管理员权限"
            name="is_admin"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户模态框 */}
      <Modal
        title={
          <span style={{ color: 'var(--color-text-primary)' }}>
            <EditOutlined style={{ marginRight: 8 }} />
            编辑用户: {selectedUser?.username}
          </span>
        }
        open={editModalVisible}
        onOk={handleUpdateUser}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedUser(null);
          editForm.resetFields();
        }}
        confirmLoading={updateUserMutation.isPending}
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            label="邮箱"
            name="email"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>

          <Form.Item
            label="全名"
            name="full_name"
          >
            <Input placeholder="请输入全名" />
          </Form.Item>

          <Form.Item
            label="激活状态"
            name="is_active"
            valuePropName="checked"
          >
            <Switch checkedChildren="激活" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item
            label="管理员权限"
            name="is_admin"
            valuePropName="checked"
          >
            <Switch 
              checkedChildren="管理员" 
              unCheckedChildren="普通用户"
              disabled={selectedUser?.id === currentUser?.id}
            />
          </Form.Item>
          {selectedUser?.id === currentUser?.id && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              * 不能修改自己的管理员权限
            </Text>
          )}
        </Form>
      </Modal>

      {/* 重置密码模态框 */}
      <Modal
        title={
          <span style={{ color: 'var(--color-text-primary)' }}>
            <LockOutlined style={{ marginRight: 8 }} />
            重置密码: {selectedUser?.username}
          </span>
        }
        open={resetPasswordModalVisible}
        onOk={handleResetPasswordSubmit}
        onCancel={() => {
          setResetPasswordModalVisible(false);
          setSelectedUser(null);
          resetPasswordForm.resetFields();
        }}
        confirmLoading={resetPasswordMutation.isPending}
      >
        <Form
          form={resetPasswordForm}
          layout="vertical"
        >
          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码" />
          </Form.Item>

          <Form.Item
            label="确认密码"
            name="confirm_password"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请再次输入新密码" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;

