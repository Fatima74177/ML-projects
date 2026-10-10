import React, { createContext, useContext, useEffect, useState } from "react";
import { api, login as apiLogin, setToken } from "../services/api";

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: "ADMIN" | "ANALYST" | "VIEWER";
  is_active: boolean;
}

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMe = async () => {
    try {
      const me = await api.get("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (localStorage.getItem("eef_token")) {
      loadMe();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    setError(null);
    try {
      const res = await apiLogin(username, password);
      setToken(res.access_token);
      await loadMe();
    } catch (e: any) {
      setError(e.message || "Login failed");
      throw e;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
