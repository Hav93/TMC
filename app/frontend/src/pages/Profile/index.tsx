import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Avatar, 
  Upload, 
  message, 
  Divider,
  Space,
  Modal
} from 'antd';
import { 
  UserOutlined, 
  MailOutlined, 
  LockOutlined, 
  CameraOutlined 
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { updateProfile, changePassword } from '../../services/auth';
import { useThemeContext } from '../../theme';

const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const { colors } = useThemeContext();
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(user?.avatar || null);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);

  // 处理头像上传（转换为Base64）
  const handleAvatarChange = (info: any) => {
    const file = info.file.originFileObj || info.file;
    
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        setAvatarUrl(base64);
        profileForm.setFieldsValue({ avatar: base64 });
      };
      reader.readAsDataURL(file);
    }
  };

  // 更新个人信息
  const handleProfileSubmit = async (values: any) => {
    try {
      setLoading(true);
      const updateData: any = {};
      
      if (values.email) updateData.email = values.email;
      if (values.full_name) updateData.full_name = values.full_name;
      if (avatarUrl && avatarUrl !== user?.avatar) updateData.avatar = avatarUrl;
      
      await updateProfile(updateData);
      await refreshUser();
      message.success('个人信息更新成功！');
    } catch (error: any) {
      message.error(error.message || '更新失败');
    } finally {
      setLoading(false);
    }
  };

  // 修改密码
  const handlePasswordSubmit = async (values: any) => {
    try {
      setPasswordLoading(true);
      await changePassword({
        old_password: values.old_password,
        new_password: values.new_password
      });
      message.success('密码修改成功！');
      passwordForm.resetFields();
      setPasswordModalVisible(false);
    } catch (error: any) {
      message.error(error.message || '密码修改失败');
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Card title="个人信息管理">
        {/* 头像区域 */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Upload
            name="avatar"
            showUploadList={false}
            beforeUpload={() => false}
            onChange={handleAvatarChange}
            accept="image/*"
          >
            <div style={{ cursor: 'pointer', display: 'inline-block', position: 'relative' }}>
              <Avatar 
                size={120} 
                src={avatarUrl} 
                icon={<UserOutlined />}
                style={{ 
                  backgroundColor: user?.is_admin ? '#f56a00' : colors.info,
                }}
              />
              <div style={{
                position: 'absolute',
                bottom: 0,
                right: 0,
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: colors.info,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '3px solid #fff',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              }}>
                <CameraOutlined style={{ color: '#fff', fontSize: 16 }} />
              </div>
            </div>
          </Upload>
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 20, fontWeight: 600 }}>{user?.username}</div>
            <div style={{ color: colors.textSecondary, marginTop: 4 }}>
              {user?.is_admin ? '🛡️ 管理员' : '👤 普通用户'}
            </div>
          </div>
        </div>

        <Divider />

        {/* 基本信息表单 */}
        <Form
          form={profileForm}
          layout="vertical"
          initialValues={{
            email: user?.email,
            full_name: user?.full_name,
          }}
          onFinish={handleProfileSubmit}
        >
          <Form.Item
            label="用户名"
            name="username"
          >
            <Input 
              value={user?.username} 
              disabled 
              prefix={<UserOutlined />}
            />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}
          >
            <Input 
              prefix={<MailOutlined />}
              placeholder="请输入邮箱"
            />
          </Form.Item>

          <Form.Item
            label="全名"
            name="full_name"
          >
            <Input 
              prefix={<UserOutlined />}
              placeholder="请输入全名"
            />
          </Form.Item>

          <Form.Item hidden name="avatar">
            <Input />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
              >
                保存更改
              </Button>
              <Button 
                onClick={() => setPasswordModalVisible(true)}
                icon={<LockOutlined />}
              >
                修改密码
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 修改密码Modal */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordSubmit}
        >
          <Form.Item
            label="旧密码"
            name="old_password"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />}
              placeholder="请输入旧密码"
            />
          </Form.Item>

          <Form.Item
            label="新密码"
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />}
              placeholder="请输入新密码（至少6位）"
            />
          </Form.Item>

          <Form.Item
            label="确认新密码"
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
            <Input.Password 
              prefix={<LockOutlined />}
              placeholder="请再次输入新密码"
            />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setPasswordModalVisible(false);
                passwordForm.resetFields();
              }}>
                取消
              </Button>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={passwordLoading}
              >
                确认修改
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProfilePage;

