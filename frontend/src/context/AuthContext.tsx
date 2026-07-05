'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api, setAccessToken, setRefreshToken, clearTokens, getAccessToken } from '@/utils/api';

export interface UserProfile {
  id: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const router = useRouter();
  const pathname = usePathname();

  const refreshProfile = async () => {
    try {
      const profile = await api.get('/auth/me');
      setUser(profile);
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
      setUser(null);
      clearTokens();
    }
  };

  useEffect(() => {
    const initializeAuth = async () => {
      const token = getAccessToken();
      if (token) {
        await refreshProfile();
      }
      setLoading(false);
    };

    initializeAuth();

    // Listen for session expiration events dispatched by the api client wrapper
    const handleSessionExpired = () => {
      setUser(null);
      router.push('/login?expired=true');
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('auth_session_expired', handleSessionExpired);
    }

    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('auth_session_expired', handleSessionExpired);
      }
    };
  }, []);

  // Simple route protection logic
  useEffect(() => {
    if (!loading) {
      const isAuthPage = pathname === '/login' || pathname === '/register';
      const isDashboardPage = pathname.startsWith('/dashboard');

      if (!user && isDashboardPage) {
        router.push('/login');
      } else if (user && isAuthPage) {
        router.push('/dashboard');
      }
    }
  }, [user, pathname, loading]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      // Create url-encoded body matching OAuth2 standard
      const body = new URLSearchParams();
      body.append('username', email);
      body.append('password', password);

      const data = await api.post('/auth/login', body, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        skipAuth: true,
      });

      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      
      await refreshProfile();
      router.push('/dashboard');
    } catch (err) {
      setLoading(false);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setLoading(true);
    try {
      await api.post('/auth/register', { email, password }, { skipAuth: true });
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
