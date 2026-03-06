/**
 * 设备 ID 管理器
 * 生成并持久化设备唯一标识
 */

export class DeviceIdManager {
    private static readonly STORAGE_KEY = 'castplay_device_id';
    private static instance: string | null = null;

    /**
     * 获取或创建设备 ID
     */
    static async getDeviceId(): Promise<string> {
        // 内存缓存
        if (this.instance) {
            return this.instance;
        }

        // 尝试从 localStorage 读取
        let deviceId = localStorage.getItem(this.STORAGE_KEY);

        if (!deviceId) {
            // 生成新的 UUID v4
            deviceId = this.generateUUIDv4();
            localStorage.setItem(this.STORAGE_KEY, deviceId);
        }

        this.instance = deviceId;
        return deviceId;
    }

    /**
     * 生成 UUID v4
     */
    private static generateUUIDv4(): string {
        // 现代浏览器支持 crypto.randomUUID()
        if (crypto && 'randomUUID' in crypto) {
            return crypto.randomUUID();
        }

        // 降级方案：手动生成
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 重置设备 ID（用于测试或重新部署）
     */
    static reset(): string {
        const newId = this.generateUUIDv4();
        localStorage.setItem(this.STORAGE_KEY, newId);
        this.instance = newId;
        return newId;
    }
}
