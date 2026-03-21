/**
 * 服务器地址验证服务
 * 支持 IP 地址、域名、端口号的验证和标准化
 */

import type { AddressValidationResult } from '../types/config';

/**
 * 地址格式正则表达式
 * 支持：
 * - IP 地址：192.168.1.100
 * - IP:端口：192.168.1.100:8080
 * - 域名：example.com
 * - 域名:端口：example.com:443
 * - 带协议：http://example.com 或 https://example.com
 */
const ADDRESS_REGEX = /^(https?:\/\/)?([\w.-]+)(:\d+)?$/;

/**
 * IP 地址正则（用于区分 IP 和域名）
 */
const IP_REGEX = /^(\d{1,3}\.){3}\d{1,3}$/;

/**
 * 验证服务器地址
 * @param input 用户输入的地址
 * @returns 验证结果
 */
export function validateAddress(input: string): AddressValidationResult & { host?: string; port?: number } {
  // 空值检查
  if (!input || input.trim().length === 0) {
    return {
      valid: false,
      error: '请输入服务器地址',
    };
  }

  const trimmed = input.trim();

  // 基本格式检查
  const match = trimmed.match(ADDRESS_REGEX);
  if (!match) {
    return {
      valid: false,
      error: '请输入有效的 IP 地址或域名',
    };
  }

  const [, _protocol, host, portStr] = match;

  // 检查主机名不为空
  if (!host || host.length === 0) {
    return {
      valid: false,
      error: '请输入有效的 IP 地址或域名',
    };
  }

  // 验证端口号
  let port: number | undefined;
  if (portStr) {
    port = parseInt(portStr.slice(1), 10);
    if (isNaN(port) || port < 1 || port > 65535) {
      return {
        valid: false,
        error: '端口号必须在 1-65535 之间',
      };
    }
  }

  // 验证 IP 地址格式（如果是 IP）
  if (IP_REGEX.test(host)) {
    const parts = host.split('.');
    const validIp = parts.every(part => {
      const num = parseInt(part, 10);
      return num >= 0 && num <= 255;
    });
    if (!validIp) {
      return {
        valid: false,
        error: '请输入有效的 IP 地址',
      };
    }
  }

  // 标准化地址（移除协议前缀）
  const normalized = host + (portStr || '');

  return {
    valid: true,
    normalized,
    host,
    port: port ?? 8000, // 默认端口 8000
  };
}

/**
 * 构建完整的服务器 URL
 * @param host 主机名
 * @param port 端口号
 * @param protocol 协议
 * @returns 完整的 URL
 */
export function buildServerUrl(
  host: string,
  port: number,
  protocol: 'http' | 'https' = 'https'
): string {
  // 如果是默认端口，不显示端口号
  const portSuffix = (protocol === 'https' && port === 443) ||
                     (protocol === 'http' && port === 80)
                     ? '' : `:${port}`;
  return `${protocol}://${host}${portSuffix}`;
}

/**
 * 从 URL 中提取地址信息
 * @param url 完整的 URL
 * @returns 地址信息
 */
export function parseServerUrl(url: string): {
  host: string;
  port: number;
  protocol: 'http' | 'https';
} | null {
  try {
    const parsed = new URL(url);
    return {
      host: parsed.hostname,
      port: parseInt(parsed.port, 10) || (parsed.protocol === 'https:' ? 443 : 80),
      protocol: parsed.protocol.replace(':', '') as 'http' | 'https',
    };
  } catch {
    return null;
  }
}

/**
 * 测试服务器连接
 * @param host 主机名
 * @param port 端口号
 * @param timeout 超时时间（毫秒）
 * @returns 连接结果
 */
export async function testServerConnection(
  host: string,
  port: number,
  timeout: number = 5000
): Promise<{
  success: boolean;
  protocol: 'http' | 'https';
  error?: string;
}> {
  const protocols: Array<'https' | 'http'> = ['https', 'http'];

  for (const protocol of protocols) {
    const url = buildServerUrl(host, port, protocol);
    const healthUrl = `${url}/api/health`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(healthUrl, {
        method: 'HEAD',
        signal: controller.signal,
        mode: 'cors',
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        console.log(`[AddressValidator] Connection successful via ${protocol}`);
        return { success: true, protocol };
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.log(`[AddressValidator] ${protocol} connection failed:`, errorMessage);
    }
  }

  return {
    success: false,
    protocol: 'https',
    error: '无法连接到服务器，请检查地址是否正确',
  };
}

/**
 * 地址验证器类
 * 提供面向对象的验证接口
 */
export class AddressValidator {
  /**
   * 验证地址
   */
  static validate(input: string): AddressValidationResult & { host?: string; port?: number } {
    return validateAddress(input);
  }

  /**
   * 测试连接
   */
  static async testConnection(
    host: string,
    port: number,
    timeout?: number
  ): Promise<{
    success: boolean;
    protocol: 'http' | 'https';
    error?: string;
  }> {
    return testServerConnection(host, port, timeout);
  }

  /**
   * 构建 URL
   */
  static buildUrl(host: string, port: number, protocol?: 'http' | 'https'): string {
    return buildServerUrl(host, port, protocol);
  }
}
