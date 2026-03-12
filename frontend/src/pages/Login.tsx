/**
 * 登录页面
 */
import { useState } from 'react';
import { Form, Input, Button, Card, Typography, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useStore } from '../store';

const { Title } = Typography;

const LoginPage: React.FC = () => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useStore();

  const handleFinish = async (values: { username: string; password: string }) => {
    console.log('Login button clicked, values:', values);
    setLoading(true);
    try {
      const response: any = await login(values);
      console.log('Login response:', response);

      if (response.access_token) {
        // 保存 token
        localStorage.setItem('token', response.access_token);

        // 保存用户信息
        setUser(response.user);

        // 显示成功消息
        message.success('登录成功');

        console.log('Token saved, navigating to home...');

        // 尝试使用 navigate 而不是 window.location.href
        try {
          navigate('/');
          console.log('Navigate successful');
        } catch (navError) {
          console.error('Navigate error:', navError);
          // 如果 navigate 失败，回退到 window.location.href
          console.log('Falling back to window.location.href');
          window.location.href = '/';
        }
      }
    } catch (error: unknown) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : '登录失败，请重试';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
