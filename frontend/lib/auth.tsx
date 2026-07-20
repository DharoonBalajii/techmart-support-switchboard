"use client";

import { createContext, useContext, useEffect, useState } from "react";
import * as api from "./api";
import type { User } from "./api";

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .getMe()
      .then(setUser)
      .catch(() => api.clearToken())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    setError(null);
    try {
      const res = await api.login(email, password);
      api.setToken(res.token);
      setUser(res.user);
    } catch (e) {
      setError(e instanceof api.ApiError ? e.message : "Couldn't sign in. Try again.");
      throw e;
    }
  }

  async function register(name: string, email: string, password: string) {
    setError(null);
    try {
      const res = await api.register(name, email, password);
      api.setToken(res.token);
      setUser(res.user);
    } catch (e) {
      setError(e instanceof api.ApiError ? e.message : "Couldn't create your account. Try again.");
      throw e;
    }
  }

  async function logout() {
    await api.logout();
    api.clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, error, login, register, logout, clearError: () => setError(null) }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
