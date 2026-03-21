/**
 * 认证 API
 */
import { api } from './client';
import type { User } from '../types';

export interface LoginParams {
  username: string;
  password: string;
}

export interface RegisterParams {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: User;
}

// 用户登录
export const login = (params: LoginParams): Promise<LoginResponse> =>
  api.post<LoginResponse>('/auth/login', params);

// 用户注册
export const register = (params: RegisterParams): Promise<{ message: string; user: User }> =>
  api.post<{ message: string; user: User }>('/auth/register', params);

// 获取当前用户信息
export const getCurrentUser = (): Promise<User> =>
  api.get<User>('/auth/me');

// 退出登录
export const logout = () => {
  localStorage.removeItem('token');
  window.location.href = '/login';
};

export const setToken = (token: string) => {
  localStorage.setItem('token', token);
};

export const getToken = () => {
  return localStorage.getItem('token');
};
