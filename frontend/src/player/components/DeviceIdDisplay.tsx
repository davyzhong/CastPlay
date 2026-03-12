/**
 * 设备 ID 简化展示组件
 * 显示设备 ID 前 4 位，低可视度，无交互
 */
import React from 'react';

interface DeviceIdDisplayProps {
    deviceId: string;
    className?: string;
}

export const DeviceIdDisplay: React.FC<DeviceIdDisplayProps> = ({
    deviceId,
    className = ''
}) => {
    // 取前 4 位
    const shortId = deviceId.slice(0, 4);

    return (
        <div
            className={`device-id-display ${className}`}
            style={styles.container}
            aria-label={`Device ID: ${deviceId}`}
        >
            {shortId}
        </div>
    );
};

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        position: 'fixed',
        right: '16px',
        bottom: '16px',
        fontSize: '12px',
        fontFamily: 'sans-serif',
        color: '#999999',
        opacity: 0.4,
        pointerEvents: 'none', // 禁止交互
        userSelect: 'none',
        zIndex: 9999,
        whiteSpace: 'nowrap' as const
    }
};
