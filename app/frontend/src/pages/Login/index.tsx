import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { login, getCurrentUser } from '../../services/auth';
import { useAuth } from '../../contexts/AuthContext';
import './styles.css';

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login: setAuthUser, isAuthenticated } = useAuth();

  // 如果已登录，重定向到首页
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const onFinish = async (values: { username: string; password: string }) => {
    try {
      setLoading(true);
      // 调用登录API
      await login(values);
      
      // 获取用户信息
      const user = await getCurrentUser();
      
      // 更新认证状态
      setAuthUser(user);
      
      message.success('登录成功！');
      
      // 重定向到之前的页面或首页
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (error: any) {
      message.error(error.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <Card className="login-card" title="系统登录">
        <div style={{ marginBottom: 24, textAlign: 'center' }}>
          <div style={{ 
            fontSize: 18, 
            fontWeight: 600, 
            marginBottom: 8,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8
          }}>
            <div style={{
              width: 32,
              height: 32,
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: 12,
              color: '#ffffff',
              boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)',
            }}>
              TMC
            </div>
            <span>Telegram Message Central</span>
          </div>
          <div style={{ fontSize: 13, opacity: 0.7 }}>
            仅限授权用户访问
          </div>
        </div>

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div style={{ 
          marginTop: 16, 
          textAlign: 'center', 
          fontSize: 12, 
          opacity: 0.6,
          borderTop: '1px solid rgba(0,0,0,0.06)',
          paddingTop: 16
        }}>
          首次使用默认账号：admin / admin123
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
