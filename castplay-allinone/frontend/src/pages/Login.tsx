/**
 * 登录页面
 */
import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useStore } from '../store';

const { Title } = Typography;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setUser = useStore((state) => state.setUser);
  const setNotification = useStore((state) => state.setNotification);

  const handleFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const response: any = await login(values);

      if (response.access_token) {
        // 保存 token
        localStorage.setItem('token', response.access_token);

        // 保存用户信息
        setUser(response.user);

        // 显示成功消息
        message.success('登录成功');

        // 跳转到首页
        navigate('/');
      }
    } catch (error: any) {
      console.error('Login error:', error);
      setNotification({
        message: error.message || error.detail || '登录失败，请重试',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  // 检查是否已登录
  const token = localStorage.getItem('token');
  if (token) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f0f2f5',
      }}>
        <Card style={{ width: 400 }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={3}>CastPlay 管理后台</Title>
            <p style={{ color: '#888' }}>您已登录，正在跳转...</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: '#f0f2f5',
    }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3}>CastPlay 管理后台</Title>
          <p style={{ color: '#888' }}>请登录您的管理员账号</p>
        </div>
        <Form
          name="login"
          initialValues={{ username: '', password: '' }}
          onFinish={handleFinish}
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
      </Card>
    </div>
  );
};

export default LoginPage;
