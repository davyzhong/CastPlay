/**
 * 服务器配置对话框组件
 * 首次启动或点击设置按钮时显示，用于配置服务器地址
 */
import React, { useState, useCallback, useEffect } from 'react';
import { Modal, Input, Button, message, Spin } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { useServerConfig } from '../hooks/useServerConfig';
import { validateAddress, buildServerUrl } from '../services/AddressValidator';

interface ServerConfigDialogProps {
  /** 是否显示对话框 */
  visible: boolean;
  /** 配置完成回调 */
  onConfigured: () => void;
  /** 取消/关闭回调 */
  onCancel?: () => void;
  /** 是否为首次配置（不可取消） */
  isInitialSetup?: boolean;
}

type TestState = 'idle' | 'testing' | 'success' | 'error';

export const ServerConfigDialog: React.FC<ServerConfigDialogProps> = ({
  visible,
  onConfigured,
  onCancel,
  isInitialSetup = false,
}) => {
  const { config, saveConfig } = useServerConfig();
  const [address, setAddress] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [testState, setTestState] = useState<TestState>('idle');
  const [testProtocol, setTestProtocol] = useState<'http' | 'https'>('https');
  const [testError, setTestError] = useState<string | null>(null);

  // 初始化时填充已有配置
  useEffect(() => {
    if (visible && config) {
      setAddress(config.address + (config.port !== 8000 ? `:${config.port}` : ''));
    }
  }, [visible, config]);

  // 重置状态
  useEffect(() => {
    if (!visible) {
      setTestState('idle');
      setValidationError(null);
      setTestError(null);
    }
  }, [visible]);

  // 地址变化时清除错误
  const handleAddressChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setAddress(e.target.value);
    setValidationError(null);
    setTestState('idle');
    setTestError(null);
  }, []);

  // 测试连接
  const testConnection = useCallback(async () => {
    if (!address.trim()) {
      setValidationError('请输入服务器地址');
      return;
    }

    const result = validateAddress(address);
    if (!result.valid) {
      setValidationError(result.error || '请输入有效的地址');
      return;
    }

    setTestState('testing');
    setTestError(null);

    try {
      // 先尝试 HTTPS
      const httpsUrl = buildServerUrl(result.host!, result.port!, 'https');
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${httpsUrl}/api/health`, {
          method: 'HEAD',
          signal: controller.signal,
          mode: 'cors',
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          setTestState('success');
          setTestProtocol('https');
          return;
        }
      } catch {
        // HTTPS 失败，尝试 HTTP
      }

      // 尝试 HTTP
      const httpUrl = buildServerUrl(result.host!, result.port!, 'http');
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        const response = await fetch(`${httpUrl}/api/health`, {
          method: 'HEAD',
          signal: controller.signal,
          mode: 'cors',
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          setTestState('success');
          setTestProtocol('http');
          return;
        }
      } catch {
        // HTTP 也失败
      }

      setTestState('error');
      setTestError('无法连接到服务器，请检查地址是否正确');
    } catch (error) {
      setTestState('error');
      setTestError(error instanceof Error ? error.message : '连接测试失败');
    }
  }, [address]);

  // 保存配置
  const handleSave = useCallback(async () => {
    if (!address.trim()) {
      setValidationError('请输入服务器地址');
      return;
    }

    const result = validateAddress(address);
    if (!result.valid) {
      setValidationError(result.error || '请输入有效的地址');
      return;
    }

    // 如果还没测试连接，先测试
    if (testState === 'idle') {
      await testConnection();
    }

    // 再次检查状态
    if (testState === 'error') {
      return;
    }

    // 保存配置
    const saveResult = await saveConfig(result.host!, result.port!);
    if (saveResult.success) {
      message.success('服务器配置已保存');
      onConfigured();
    } else {
      message.error(saveResult.error || '保存失败');
    }
  }, [address, testState, testConnection, saveConfig, onConfigured]);

  // 跳过（仅非首次配置时可用）
  const handleSkip = useCallback(() => {
    if (onCancel) {
      onCancel();
    }
  }, [onCancel]);

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>服务器配置</span>
          {isInitialSetup && (
            <span style={{
              fontSize: 12,
              color: '#faad14',
              background: '#fffbe6',
              padding: '2px 8px',
              borderRadius: 4,
            }}>
              首次配置
            </span>
          )}
        </div>
      }
      open={visible}
      footer={null}
      closable={!isInitialSetup}
      maskClosable={false}
      onCancel={onCancel}
      width={480}
    >
      <div style={{ padding: '8px 0' }}>
        <p style={{ color: '#666', marginBottom: 16 }}>
          请输入 CastPlay 服务器的 IP 地址或域名
        </p>

        <Input
          placeholder="例如: 192.168.1.100 或 example.com:8080"
          value={address}
          onChange={handleAddressChange}
          status={validationError ? 'error' : undefined}
          size="large"
          onPressEnter={handleSave}
          style={{ marginBottom: 8 }}
        />

        {validationError && (
          <div style={{ color: '#ff4d4f', fontSize: 12, marginBottom: 8 }}>
            {validationError}
          </div>
        )}

        {/* 连接测试状态 */}
        {testState !== 'idle' && (
          <div style={{
            marginTop: 12,
            padding: '8px 12px',
            background: testState === 'success' ? '#f6ffed' :
                       testState === 'error' ? '#fff2f0' : '#f0f0f0',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            {testState === 'testing' && (
              <>
                <Spin size="small" />
                <span style={{ color: '#666' }}>正在测试连接...</span>
              </>
            )}
            {testState === 'success' && (
              <>
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                <span style={{ color: '#52c41a' }}>
                  连接成功 ({testProtocol})
                </span>
              </>
            )}
            {testState === 'error' && (
              <>
                <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                <span style={{ color: '#ff4d4f' }}>{testError}</span>
              </>
            )}
          </div>
        )}

        {/* 操作按钮 */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 8,
          marginTop: 24,
        }}>
          {!isInitialSetup && (
            <Button onClick={handleSkip}>
              取消
            </Button>
          )}
          <Button
            onClick={testConnection}
            loading={testState === 'testing'}
          >
            测试连接
          </Button>
          <Button
            type="primary"
            onClick={handleSave}
            disabled={testState === 'error'}
          >
            保存
          </Button>
        </div>

        {/* 提示信息 */}
        {isInitialSetup && (
          <div style={{
            marginTop: 16,
            padding: '8px 12px',
            background: '#e6f7ff',
            borderRadius: 6,
            fontSize: 12,
            color: '#1890ff',
          }}>
            <WarningOutlined style={{ marginRight: 4 }} />
            首次使用需要配置服务器地址才能连接
          </div>
        )}
      </div>
    </Modal>
  );
};
