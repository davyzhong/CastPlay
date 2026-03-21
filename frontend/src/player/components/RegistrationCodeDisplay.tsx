/**
 * 注册码显示组件
 * 未注册设备启动时显示生产配置的注册码，支持复制到剪贴板
 */
import React, { useState, useEffect } from 'react';
import { Button, message, Typography, Space, Card } from 'antd';
import { CopyOutlined, CheckOutlined, ReloadOutlined } from '@ant-design/icons';
import { useRegistrationCode } from '../hooks/useRegistrationCode';

const { Title, Text, Paragraph } = Typography;

interface RegistrationCodeDisplayProps {
  /** 注册成功回调 */
  onRegistered?: () => void;
  /** 自定义样式 */
  style?: React.CSSProperties;
}

export const RegistrationCodeDisplay: React.FC<RegistrationCodeDisplayProps> = ({
  onRegistered,
  style,
}) => {
  const {
    registrationCode,
    isRegistered,
    hasRegistrationCode,
    copyRegistrationCode,
  } = useRegistrationCode();

  const [copied, setCopied] = useState(false);
  const [checking, setChecking] = useState(false);

  // 如果已注册，触发回调
  useEffect(() => {
    if (isRegistered && onRegistered) {
      onRegistered();
    }
  }, [isRegistered, onRegistered]);

  // 处理复制操作
  const handleCopy = async () => {
    const success = await copyRegistrationCode();
    if (success) {
      setCopied(true);
      message.success('注册码已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    } else {
      message.error('复制失败，请手动复制');
    }
  };

  // 检查注册状态
  const handleCheckRegistration = async () => {
    setChecking(true);
    // 等待一段时间让后台检查注册状态
    // 实际注册是通过 useDeviceRegistration hook 自动完成的
    setTimeout(() => {
      setChecking(false);
      if (isRegistered) {
        message.success('设备已成功注册');
      } else {
        message.info('设备尚未注册，请等待后台管理员完成注册');
      }
    }, 1000);
  };

  // 格式化注册码显示（分组显示，便于阅读）
  const formatCode = (code: string): string => {
    if (!code) return '';
    // 如果已经是 CP-XXXX-XXXX-XXXX 格式，直接返回
    if (code.match(/^CP-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$/i)) {
      return code;
    }
    // 否则按 4 字符分组
    return code.replace(/(.{4})/g, '$1-').replace(/-$/, '');
  };

  // 如果没有注册码或已注册，不显示
  if (!hasRegistrationCode || isRegistered) {
    return null;
  }

  const formattedCode = formatCode(registrationCode);

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        zIndex: 999,
        ...style,
      }}
    >
      <Card
        style={{
          maxWidth: 500,
          width: '90%',
          textAlign: 'center',
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: 16,
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 标题 */}
          <div>
            <Title level={3} style={{ marginBottom: 8 }}>
              设备注册码
            </Title>
            <Text type="secondary">
              请将以下注册码提供给后台管理员以完成设备注册
            </Text>
          </div>

          {/* 注册码显示 */}
          <div
            style={{
              background: '#f5f5f5',
              borderRadius: 12,
              padding: '24px 32px',
              border: '2px dashed #d9d9d9',
            }}
          >
            <Text
              style={{
                fontSize: 32,
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontWeight: 'bold',
                letterSpacing: 2,
                color: '#1890ff',
                wordBreak: 'break-all',
              }}
              copyable={false}
            >
              {formattedCode}
            </Text>
          </div>

          {/* 操作按钮 */}
          <Space size="middle">
            <Button
              type="primary"
              size="large"
              icon={copied ? <CheckOutlined /> : <CopyOutlined />}
              onClick={handleCopy}
              style={{
                minWidth: 140,
                height: 48,
                borderRadius: 8,
              }}
            >
              {copied ? '已复制' : '复制注册码'}
            </Button>

            <Button
              size="large"
              icon={<ReloadOutlined spin={checking} />}
              onClick={handleCheckRegistration}
              style={{
                minWidth: 140,
                height: 48,
                borderRadius: 8,
              }}
            >
              {checking ? '检查中...' : '检查注册状态'}
            </Button>
          </Space>

          {/* 提示信息 */}
          <Paragraph
            type="secondary"
            style={{
              fontSize: 13,
              marginBottom: 0,
              padding: '12px 16px',
              background: '#fffbe6',
              borderRadius: 8,
              border: '1px solid #ffe58f',
            }}
          >
            💡 提示：注册码是设备的唯一标识，请联系后台管理员在设备管理页面输入此注册码完成绑定。
          </Paragraph>
        </Space>
      </Card>
    </div>
  );
};
