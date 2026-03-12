/**
 * 下载进度 UI 组件
 *
 * 显示下载进度、状态和错误信息
 */
import React from 'react';
import type { DownloadStatus } from '../hooks/usePlaylistDownload';

// 进度条组件 Props
interface DownloadProgressUIProps {
    // 下载状态
    status: DownloadStatus;
    // 进度百分比 (0-100)
    progress: number;
    // 已完成文件数
    completedFiles: number;
    // 总文件数
    totalFiles: number;
    // 失败文件数
    failedFiles: number;
    // 错误信息
    error?: string | null;
    // 是否显示详情
    showDetails?: boolean;
    // 取消回调
    onCancel?: () => void;
    // 重试回调
    onRetry?: () => void;
    // 自定义样式
    style?: React.CSSProperties;
}

// 状态文本映射
const STATUS_TEXT: Record<DownloadStatus, string> = {
    idle: '空闲',
    pending: '准备中...',
    downloading: '下载中...',
    completed: '下载完成',
    failed: '下载失败',
    partial: '部分完成',
    cancelled: '已取消',
};

// 状态颜色映射
const STATUS_COLORS: Record<DownloadStatus, string> = {
    idle: '#9ca3af',
    pending: '#6b7280',
    downloading: '#3b82f6',
    completed: '#22c55e',
    failed: '#ef4444',
    partial: '#f59e0b',
    cancelled: '#6b7280',
};

export const DownloadProgressUI: React.FC<DownloadProgressUIProps> = ({
    status,
    progress,
    completedFiles,
    totalFiles,
    failedFiles,
    error,
    showDetails = true,
    onCancel,
    onRetry,
    style = {},
}) => {
    const isActive = status === 'pending' || status === 'downloading';
    const isComplete = status === 'completed' || status === 'partial';
    const isFailed = status === 'failed' || status === 'cancelled';

    // 不显示空闲状态
    if (status === 'idle') {
        return null;
    }

    return (
        <div
            style={{
                position: 'fixed',
                bottom: 20,
                right: 20,
                background: 'rgba(0, 0, 0, 0.85)',
                color: 'white',
                padding: '16px 20px',
                borderRadius: 12,
                minWidth: 280,
                maxWidth: 360,
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
                zIndex: 9999,
                fontFamily: 'system-ui, -apple-system, sans-serif',
                ...style,
            }}
        >
            {/* 状态标题 */}
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: 12,
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {/* 状态指示器 */}
                    <div
                        style={{
                            width: 10,
                            height: 10,
                            borderRadius: '50%',
                            background: STATUS_COLORS[status],
                            animation: isActive ? 'pulse 1.5s infinite' : 'none',
                        }}
                    />
                    <span style={{ fontWeight: 600, fontSize: 14 }}>
                        {STATUS_TEXT[status]}
                    </span>
                </div>

                {/* 取消按钮 */}
                {isActive && onCancel && (
                    <button
                        onClick={onCancel}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#9ca3af',
                            cursor: 'pointer',
                            fontSize: 12,
                            padding: '4px 8px',
                            borderRadius: 4,
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                        }}
                    >
                        取消
                    </button>
                )}
            </div>

            {/* 进度条 */}
            {(isActive || isComplete) && (
                <div style={{ marginBottom: 12 }}>
                    <div
                        style={{
                            height: 6,
                            background: 'rgba(255, 255, 255, 0.1)',
                            borderRadius: 3,
                            overflow: 'hidden',
                        }}
                    >
                        <div
                            style={{
                                height: '100%',
                                width: `${progress}%`,
                                background: STATUS_COLORS[status],
                                borderRadius: 3,
                                transition: 'width 0.3s ease',
                            }}
                        />
                    </div>
                </div>
            )}

            {/* 详细信息 */}
            {showDetails && (
                <div
                    style={{
                        fontSize: 12,
                        color: '#9ca3af',
                        marginBottom: error ? 12 : 0,
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>文件进度</span>
                        <span>
                            {completedFiles} / {totalFiles}
                            {failedFiles > 0 && (
                                <span style={{ color: '#ef4444', marginLeft: 8 }}>
                                    ({failedFiles} 失败)
                                </span>
                            )}
                        </span>
                    </div>
                    {isActive && (
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                            <span>进度</span>
                            <span>{progress}%</span>
                        </div>
                    )}
                </div>
            )}

            {/* 错误信息 */}
            {error && (
                <div
                    style={{
                        fontSize: 12,
                        color: '#ef4444',
                        background: 'rgba(239, 68, 68, 0.1)',
                        padding: '8px 12px',
                        borderRadius: 6,
                        marginBottom: onRetry ? 12 : 0,
                    }}
                >
                    {error}
                </div>
            )}

            {/* 重试按钮 */}
            {isFailed && onRetry && (
                <button
                    onClick={onRetry}
                    style={{
                        width: '100%',
                        marginTop: 12,
                        padding: '10px 16px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 13,
                        fontWeight: 500,
                        cursor: 'pointer',
                        transition: 'background 0.2s',
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#2563eb';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#3b82f6';
                    }}
                >
                    重试
                </button>
            )}
        </div>
    );
};

// 紧凑版进度指示器
interface CompactProgressIndicatorProps {
    progress: number;
    status: DownloadStatus;
    style?: React.CSSProperties;
}

export const CompactProgressIndicator: React.FC<CompactProgressIndicatorProps> = ({
    progress,
    status,
    style = {},
}) => {
    if (status === 'idle') return null;

    return (
        <div
            style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                background: 'rgba(0, 0, 0, 0.6)',
                borderRadius: 12,
                fontSize: 11,
                color: 'white',
                ...style,
            }}
        >
            <div
                style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: STATUS_COLORS[status],
                }}
            />
            <span>
                {status === 'downloading' ? `${progress}%` : STATUS_TEXT[status]}
            </span>
        </div>
    );
};

export default DownloadProgressUI;
