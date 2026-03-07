/**
 * 告警配置页面
 * 管理设备告警的基础配置（离线阈值、开关等）
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface AlertConfig {
    id: number;
    device_id: number | null;
    alert_enabled: boolean;
    offline_alert_enabled: boolean;
    offline_threshold_hours: number;
    download_failure_alert_enabled: boolean;
    download_failure_threshold: number;
    storage_alert_enabled: boolean;
    storage_threshold_percent: number;
    storage_min_free_gb: number;
    playback_alert_enabled: boolean;
    playback_error_threshold: number;
    email_enabled: boolean;
    email_recipients: string;
    dingtalk_enabled: boolean;
    quiet_hours_enabled: boolean;
    quiet_hours_start: string;
    quiet_hours_end: string;
}

const defaultConfig: AlertConfig = {
    id: 0,
    device_id: null,
    alert_enabled: true,
    offline_alert_enabled: true,
    offline_threshold_hours: 4,
    download_failure_alert_enabled: true,
    download_failure_threshold: 3,
    storage_alert_enabled: true,
    storage_threshold_percent: 90,
    storage_min_free_gb: 1.0,
    playback_alert_enabled: true,
    playback_error_threshold: 5,
    email_enabled: false,
    email_recipients: '',
    dingtalk_enabled: false,
    quiet_hours_enabled: false,
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00'
};

export const AlertConfigPage: React.FC = () => {
    const [config, setConfig] = useState<AlertConfig>(defaultConfig);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // 加载配置
    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/admin/alert-config');
            if (response.data) {
                setConfig(response.data);
            }
        } catch (error) {
            console.error('Failed to load alert config:', error);
            // 使用默认配置
        } finally {
            setLoading(false);
        }
    };

    const saveConfig = async () => {
        try {
            setSaving(true);
            setMessage(null);

            if (config.id) {
                await axios.put('/api/admin/alert-config', config);
            } else {
                const response = await axios.post('/api/admin/alert-config', config);
                setConfig(response.data);
            }

            setMessage({ type: 'success', text: '配置保存成功' });
        } catch (error) {
            console.error('Failed to save alert config:', error);
            setMessage({ type: 'error', text: '保存失败，请重试' });
        } finally {
            setSaving(false);
        }
    };

    const updateConfig = (updates: Partial<AlertConfig>) => {
        setConfig(prev => ({ ...prev, ...updates }));
    };

    if (loading) {
        return (
            <div className="alert-config-page loading">
                <p>加载中...</p>
            </div>
        );
    }

    return (
        <div className="alert-config-page">
            <h1>告警配置</h1>

            {message && (
                <div className={`message ${message.type}`}>
                    {message.text}
                </div>
            )}

            {/* 总开关 */}
            <section className="config-section">
                <h2>基础设置</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.alert_enabled}
                            onChange={(e) => updateConfig({ alert_enabled: e.target.checked })}
                        />
                        启用告警
                    </label>
                </div>
            </section>

            {/* 离线告警 */}
            <section className="config-section">
                <h2>离线告警</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.offline_alert_enabled}
                            onChange={(e) => updateConfig({ offline_alert_enabled: e.target.checked })}
                            disabled={!config.alert_enabled}
                        />
                        启用设备离线告警
                    </label>
                </div>
                <div className="form-group">
                    <label>离线阈值（小时）</label>
                    <input
                        type="number"
                        min="1"
                        max="24"
                        value={config.offline_threshold_hours}
                        onChange={(e) => updateConfig({ offline_threshold_hours: parseInt(e.target.value) || 4 })}
                        disabled={!config.alert_enabled || !config.offline_alert_enabled}
                    />
                    <span className="hint">设备超过此时间未上报心跳时触发告警</span>
                </div>
            </section>

            {/* 下载失败告警 */}
            <section className="config-section">
                <h2>下载失败告警</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.download_failure_alert_enabled}
                            onChange={(e) => updateConfig({ download_failure_alert_enabled: e.target.checked })}
                            disabled={!config.alert_enabled}
                        />
                        启用下载失败告警
                    </label>
                </div>
                <div className="form-group">
                    <label>失败次数阈值</label>
                    <input
                        type="number"
                        min="1"
                        max="10"
                        value={config.download_failure_threshold}
                        onChange={(e) => updateConfig({ download_failure_threshold: parseInt(e.target.value) || 3 })}
                        disabled={!config.alert_enabled || !config.download_failure_alert_enabled}
                    />
                    <span className="hint">连续失败超过此次数时触发告警</span>
                </div>
            </section>

            {/* 存储空间告警 */}
            <section className="config-section">
                <h2>存储空间告警</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.storage_alert_enabled}
                            onChange={(e) => updateConfig({ storage_alert_enabled: e.target.checked })}
                            disabled={!config.alert_enabled}
                        />
                        启用存储空间告警
                    </label>
                </div>
                <div className="form-group inline">
                    <label>使用率阈值</label>
                    <input
                        type="number"
                        min="50"
                        max="99"
                        value={config.storage_threshold_percent}
                        onChange={(e) => updateConfig({ storage_threshold_percent: parseInt(e.target.value) || 90 })}
                        disabled={!config.alert_enabled || !config.storage_alert_enabled}
                    />
                    <span>%</span>
                </div>
                <div className="form-group inline">
                    <label>最小剩余空间</label>
                    <input
                        type="number"
                        min="0.1"
                        max="100"
                        step="0.1"
                        value={config.storage_min_free_gb}
                        onChange={(e) => updateConfig({ storage_min_free_gb: parseFloat(e.target.value) || 1 })}
                        disabled={!config.alert_enabled || !config.storage_alert_enabled}
                    />
                    <span>GB</span>
                </div>
            </section>

            {/* 播放异常告警 */}
            <section className="config-section">
                <h2>播放异常告警</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.playback_alert_enabled}
                            onChange={(e) => updateConfig({ playback_alert_enabled: e.target.checked })}
                            disabled={!config.alert_enabled}
                        />
                        启用播放异常告警
                    </label>
                </div>
                <div className="form-group">
                    <label>错误次数阈值</label>
                    <input
                        type="number"
                        min="1"
                        max="50"
                        value={config.playback_error_threshold}
                        onChange={(e) => updateConfig({ playback_error_threshold: parseInt(e.target.value) || 5 })}
                        disabled={!config.alert_enabled || !config.playback_alert_enabled}
                    />
                    <span className="hint">连续播放错误超过此次数时触发告警</span>
                </div>
            </section>

            {/* 静默时段 */}
            <section className="config-section">
                <h2>静默时段</h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.quiet_hours_enabled}
                            onChange={(e) => updateConfig({ quiet_hours_enabled: e.target.checked })}
                            disabled={!config.alert_enabled}
                        />
                        启用静默时段
                    </label>
                    <span className="hint">静默时段内不发送告警通知</span>
                </div>
                {config.quiet_hours_enabled && (
                    <div className="form-row">
                        <div className="form-group inline">
                            <label>开始时间</label>
                            <input
                                type="time"
                                value={config.quiet_hours_start}
                                onChange={(e) => updateConfig({ quiet_hours_start: e.target.value })}
                                disabled={!config.alert_enabled}
                            />
                        </div>
                        <div className="form-group inline">
                            <label>结束时间</label>
                            <input
                                type="time"
                                value={config.quiet_hours_end}
                                onChange={(e) => updateConfig({ quiet_hours_end: e.target.value })}
                                disabled={!config.alert_enabled}
                            />
                        </div>
                    </div>
                )}
            </section>

            {/* 通知渠道（预留） */}
            <section className="config-section disabled">
                <h2>通知渠道 <span className="badge">即将推出</span></h2>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.email_enabled}
                            disabled
                        />
                        邮件通知
                    </label>
                </div>
                <div className="form-group">
                    <label>
                        <input
                            type="checkbox"
                            checked={config.dingtalk_enabled}
                            disabled
                        />
                        钉钉通知
                    </label>
                </div>
                <p className="hint">邮件和钉钉通知配置即将推出</p>
            </section>

            {/* 保存按钮 */}
            <div className="actions">
                <button
                    className="btn btn-primary"
                    onClick={saveConfig}
                    disabled={saving}
                >
                    {saving ? '保存中...' : '保存配置'}
                </button>
                <button
                    className="btn btn-secondary"
                    onClick={loadConfig}
                    disabled={saving}
                >
                    重置
                </button>
            </div>

            <style>{`
                .alert-config-page {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }

                .alert-config-page.loading {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 400px;
                }

                h1 {
                    font-size: 24px;
                    margin-bottom: 24px;
                    color: #333;
                }

                h2 {
                    font-size: 18px;
                    margin-bottom: 16px;
                    color: #555;
                }

                .config-section {
                    background: #f9f9f9;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }

                .config-section.disabled {
                    opacity: 0.6;
                }

                .form-group {
                    margin-bottom: 16px;
                }

                .form-group.inline {
                    display: inline-flex;
                    align-items: center;
                    margin-right: 20px;
                }

                .form-group label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                }

                .form-group input[type="checkbox"] {
                    width: 18px;
                    height: 18px;
                }

                .form-group input[type="number"],
                .form-group input[type="time"] {
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                    width: 100px;
                    margin-left: 8px;
                }

                .form-group input:disabled {
                    background-color: #eee;
                    cursor: not-allowed;
                }

                .form-row {
                    display: flex;
                    gap: 20px;
                }

                .hint {
                    color: #888;
                    font-size: 12px;
                    margin-left: 8px;
                }

                .badge {
                    background: #e0e0e0;
                    color: #666;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-left: 8px;
                }

                .message {
                    padding: 12px 16px;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }

                .message.success {
                    background: #d4edda;
                    color: #155724;
                }

                .message.error {
                    background: #f8d7da;
                    color: #721c24;
                }

                .actions {
                    display: flex;
                    gap: 12px;
                    margin-top: 24px;
                }

                .btn {
                    padding: 10px 24px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }

                .btn-primary {
                    background: #007bff;
                    color: white;
                }

                .btn-primary:hover {
                    background: #0056b3;
                }

                .btn-primary:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }

                .btn-secondary {
                    background: #e0e0e0;
                    color: #333;
                }

                .btn-secondary:hover {
                    background: #d0d0d0;
                }
            `}</style>
        </div>
    );
};

export default AlertConfigPage;
