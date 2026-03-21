/**
 * 配置错误边界组件
 * 捕获配置相关的错误并提供友好的错误界面
 */
import { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Collapse } from 'antd';
import { ReloadOutlined, BugOutlined, ClearOutlined } from '@ant-design/icons';
import { configStorage } from '../services/ConfigStorage';
import { STORAGE_KEYS } from '../types/config';

const { Paragraph, Text } = Typography;

interface ConfigErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ConfigErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorType: 'config' | 'storage' | 'network' | 'unknown';
}

/**
 * 分析错误类型
 */
function analyzeError(error: Error): 'config' | 'storage' | 'network' | 'unknown' {
  const message = error.message.toLowerCase();
  const stack = error.stack?.toLowerCase() || '';

  if (
    message.includes('config') ||
    message.includes('server') ||
    message.includes('address') ||
    stack.includes('configstorage') ||
    stack.includes('useserverconfig')
  ) {
    return 'config';
  }

  if (
    message.includes('storage') ||
    message.includes('localstorage') ||
    message.includes('quota') ||
    stack.includes('storage')
  ) {
    return 'storage';
  }

  if (
    message.includes('network') ||
    message.includes('fetch') ||
    message.includes('timeout') ||
    message.includes('connection') ||
    stack.includes('playerapi')
  ) {
    return 'network';
  }

  return 'unknown';
}

/**
 * 获取错误标题
 */
function getErrorTitle(errorType: string): string {
  switch (errorType) {
    case 'config':
      return '配置错误';
    case 'storage':
      return '存储错误';
    case 'network':
      return '网络错误';
    default:
      return '播放器错误';
  }
}

/**
 * 获取错误描述
 */
function getErrorDescription(errorType: string): string {
  switch (errorType) {
    case 'config':
      return '服务器配置出现问题，请检查服务器地址是否正确';
    case 'storage':
      return '本地存储出现问题，可能是存储空间不足或浏览器限制';
    case 'network':
      return '网络连接出现问题，请检查网络状态';
    default:
      return '播放器遇到意外错误';
  }
}

export class ConfigErrorBoundary extends Component<ConfigErrorBoundaryProps, ConfigErrorBoundaryState> {
  constructor(props: ConfigErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorType: 'unknown',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ConfigErrorBoundaryState> {
    return {
      hasError: true,
      error,
      errorType: analyzeError(error),
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ConfigErrorBoundary] Caught error:', error);
    console.error('[ConfigErrorBoundary] Error info:', errorInfo);

    this.setState({
      errorInfo,
    });

    // 上报错误（如果有错误上报服务）
    this.reportError(error, errorInfo);
  }

  /**
   * 上报错误
   */
  private reportError(error: Error, errorInfo: ErrorInfo) {
    try {
      // 可以集成到错误上报服务
      const errorReport = {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      };

      console.log('[ConfigErrorBoundary] Error report:', errorReport);

      // TODO: 发送到错误上报服务
      // ErrorReporter.report(errorReport);
    } catch (e) {
      console.error('[ConfigErrorBoundary] Failed to report error:', e);
    }
  }

  /**
   * 重试
   */
  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorType: 'unknown',
    });
  };

  /**
   * 清除配置并刷新
   */
  handleClearConfig = () => {
    try {
      // 清除所有配置
      configStorage.clearAll();

      // 也清除 localStorage 中的其他相关数据
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });

      // 清除其他可能的缓存
      localStorage.removeItem('castplay_setup_completed');
      localStorage.removeItem('castplay_playlist_selection');

      console.log('[ConfigErrorBoundary] Config cleared, reloading...');

      // 刷新页面
      window.location.reload();
    } catch (e) {
      console.error('[ConfigErrorBoundary] Failed to clear config:', e);
      // 强制刷新
      window.location.reload();
    }
  };

  /**
   * 复制错误信息
   */
  handleCopyError = () => {
    const { error, errorInfo } = this.state;
    if (!error) return;

    const errorText = `
错误信息: ${error.message}

错误堆栈:
${error.stack || 'N/A'}

组件堆栈:
${errorInfo?.componentStack || 'N/A'}

时间: ${new Date().toLocaleString()}
URL: ${window.location.href}
UserAgent: ${navigator.userAgent}
    `.trim();

    navigator.clipboard.writeText(errorText).then(() => {
      console.log('[ConfigErrorBoundary] Error info copied to clipboard');
    });
  };

  render() {
    const { hasError, error, errorType } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      // 如果提供了自定义 fallback，使用它
      if (fallback) {
        return fallback;
      }

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
            padding: 20,
          }}
        >
          <div
            style={{
              maxWidth: 600,
              width: '100%',
              background: 'white',
              borderRadius: 16,
              overflow: 'hidden',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
            }}
          >
            <Result
              status="error"
              title={getErrorTitle(errorType)}
              subTitle={getErrorDescription(errorType)}
              extra={[
                <Button
                  key="retry"
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={this.handleRetry}
                >
                  重试
                </Button>,
                <Button
                  key="clear"
                  icon={<ClearOutlined />}
                  onClick={this.handleClearConfig}
                  danger
                >
                  清除配置
                </Button>,
              ]}
            />

            {/* 详细错误信息 */}
            {error && (
              <div style={{ padding: '0 24px 24px' }}>
                <Collapse
                  ghost
                  items={[
                    {
                      key: '1',
                      label: (
                        <Text type="secondary">
                          <BugOutlined style={{ marginRight: 8 }} />
                          技术详情（可提供给技术支持）
                        </Text>
                      ),
                      children: (
                        <div>
                          <Paragraph
                            code
                            copyable
                            style={{
                              fontSize: 12,
                              background: '#f5f5f5',
                              padding: 12,
                              borderRadius: 4,
                              maxHeight: 200,
                              overflow: 'auto',
                            }}
                          >
                            {error.message}
                          </Paragraph>

                          <Button
                            size="small"
                            onClick={this.handleCopyError}
                          >
                            复制完整错误信息
                          </Button>
                        </div>
                      ),
                    },
                  ]}
                />
              </div>
            )}
          </div>
        </div>
      );
    }

    return children;
  }
}

export default ConfigErrorBoundary;
