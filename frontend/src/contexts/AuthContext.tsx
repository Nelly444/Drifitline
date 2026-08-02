import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import {
  fetchCurrentUser,
  login as loginRequest,
  register as registerRequest,
  setUnauthorizedHandler,
  TOKEN_STORAGE_KEY,
} from "../lib/api";

interface AuthContextValue {
  token: string | null;
  email: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }, [token]);

  useEffect(() => {
    if (!token) {
      setEmail(null);
      return;
    }
    fetchCurrentUser()
      .then((user) => setEmail(user.email))
      .catch(() => setEmail(null));
  }, [token]);

  useEffect(() => {
    setUnauthorizedHandler(() => setToken(null));
  }, []);

  async function login(email: string, password: string) {
    const accessToken = await loginRequest(email, password);
    setToken(accessToken);
  }

  async function register(email: string, password: string) {
    await registerRequest(email, password);
    await login(email, password);
  }

  function logout() {
    setToken(null);
  }

  return <AuthContext.Provider value={{ token, email, login, register, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
