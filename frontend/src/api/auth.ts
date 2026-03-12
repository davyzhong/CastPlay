/**
 * 认证 API
 */
import { api } from './client';
import type { User, ApiResponse } from '../types';

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

// 用户登录
export const login = (params: LoginParams) =>
  api.post<ApiResponse<{ access_token: string; user: User }>>('/auth/login', params);

// 用户注册
export const register = (params: RegisterParams) =>
  api.post<ApiResponse<{ user: User }>>('/auth/register', params);

// 获取当前用户信息
export const getCurrentUser = () =>
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
