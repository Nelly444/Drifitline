import axios from "axios";
import type { BreakdownEntry, StatsSummary, SubscriptionSummary, TransactionRow } from "./types";

export const TOKEN_STORAGE_KEY = "driftline_token";

const client = axios.create({ baseURL: "http://localhost:8000" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      onUnauthorized?.();
    }
    return Promise.reject(error);
  },
);

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const { data } = await client.post<{ access_token: string }>("/auth/jwt/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data.access_token;
}

export async function register(email: string, password: string): Promise<void> {
  await client.post("/auth/register", { email, password });
}

export async function fetchSubscriptions(): Promise<SubscriptionSummary[]> {
  const { data } = await client.get<SubscriptionSummary[]>("/subscriptions");
  return data;
}

export async function fetchTransactions(flaggedOnly = false): Promise<TransactionRow[]> {
  const { data } = await client.get<TransactionRow[]>("/transactions", {
    params: { flagged_only: flaggedOnly },
  });
  return data;
}

export async function fetchStatsSummary(): Promise<StatsSummary> {
  const { data } = await client.get<StatsSummary>("/stats/summary");
  return data;
}

export async function fetchStatsBreakdown(): Promise<BreakdownEntry[]> {
  const { data } = await client.get<BreakdownEntry[]>("/stats/breakdown");
  return data;
}
