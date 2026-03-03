/**
 * Zustand Store - 用户认证状态管理
 */
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { TokenManager } from '../api/client';

interface User {
  id: number;
  username: string;
  role?: string;
}

interface AuthState {
  // 数据
  user: User | null;
  isAuthenticated: boolean;

  // Actions
  login: (user: User) => void;
  logout: () => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // 初始状态
        user: null,
        isAuthenticated: TokenManager.isAuthenticated(),

        // 登录
        login: (user) => {
          set({
            user,
            isAuthenticated: true,
          });
        },

        // 登出
        logout: () => {
          TokenManager.clearTokens();
          set({
            user: null,
            isAuthenticated: false,
          });
        },

        // 检查认证状态
        checkAuth: () => {
          const isAuth = TokenManager.isAuthenticated();
          if (!isAuth && get().isAuthenticated) {
            // Token 已过期，更新状态
            set({ isAuthenticated: false, user: null });
          }
          return isAuth;
        },
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({ user: state.user }), // 只持久化 user
      }
    ),
    { name: 'auth-store' }
  )
);
