/**
 * 错误边界组件
 * 捕获子组件的错误，防止整个应用崩溃
 */
import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  level?: 'page' | 'section' | 'component';
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({
      error,
      errorInfo,
    });

    // 调用错误回调
    this.props.onError?.(error, errorInfo);

    // 上报错误日志
    console.error('[ErrorBoundary]', {
      level: this.props.level || 'component',
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误UI
      const isPageLevel = this.props.level === 'page';
      const isSectionLevel = this.props.level === 'section';

      return (
        <div
          style={{
            padding: isPageLevel ? '40px' : isSectionLevel ? '24px' : '16px',
            textAlign: 'center',
            backgroundColor: '#fff2f0',
            border: isPageLevel ? 'none' : '1px solid #ffccc7',
            borderRadius: isPageLevel ? '0' : '8px',
            minHeight: isPageLevel ? '100vh' : 'auto',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <h2 style={{ color: '#ff4d4f', marginBottom: '8px' }}>
            {isPageLevel ? '页面加载失败' : isSectionLevel ? '内容加载失败' : '组件出错'}
          </h2>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            {this.state.error?.message || '发生了一个错误'}
          </p>
          {process.env.NODE_ENV === 'development' && this.state.error?.stack && (
            <pre
              style={{
                textAlign: 'left',
                padding: '12px',
                backgroundColor: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '12px',
                maxWidth: '100%',
                overflow: 'auto',
                maxHeight: isPageLevel ? '400px' : '200px',
              }}
            >
              {this.state.error.stack}
            </pre>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '16px',
              padding: '8px 24px',
              backgroundColor: '#1890ff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            刷新页面
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
