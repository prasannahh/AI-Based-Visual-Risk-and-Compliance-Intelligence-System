import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api';
import type { User } from '../types/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    name: string;
    email: string;
    password: string;
    gender?: string;
    age?: number;
    occupation?: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('dt_auth_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, []);

  useEffect(() => {
    async function loadCurrentUser() {
      const storedToken = localStorage.getItem('dt_auth_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const data = await api.me();
        setUser(data.user);
        setToken(storedToken);
      } catch (err) {
        console.warn('Failed to load session, clearing token:', err);
        api.clearToken();
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadCurrentUser();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const data = await api.login(email, password);
      setUser(data.user);
      setToken(data.token);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: {
    name: string;
    email: string;
    password: string;
    gender?: string;
    age?: number;
    occupation?: string;
  }) => {
    setIsLoading(true);
    try {
      const data = await api.register(payload);
      setUser(data.user);
      setToken(data.token);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.clearToken();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
