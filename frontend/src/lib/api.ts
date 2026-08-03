import axios from "axios";
import { API_URL } from "./config";
import type {
  AlertsTimelinePoint,
  BreakdownEntry,
  CurrentUser,
  PlaidStatus,
  StatsSummary,
  SubscriptionDetail,
  SubscriptionSummary,
  TransactionRow,
} from "./types";

export const TOKEN_STORAGE_KEY = "driftline_token";

const client = axios.create({ baseURL: API_URL });

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

// Lets non-HTTP callers (the WebSocket, on an auth failure) trigger the same
// logout flow as a 401 from a regular API call.
export function triggerUnauthorized() {
  onUnauthorized?.();
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

export async function fetchSubscriptionDetail(id: string): Promise<SubscriptionDetail> {
  const { data } = await client.get<SubscriptionDetail>(`/subscriptions/${id}`);
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

export async function fetchAlertsTimeline(): Promise<AlertsTimelinePoint[]> {
  const { data } = await client.get<AlertsTimelinePoint[]>("/stats/alerts-timeline");
  return data;
}

export async function connectSandboxAccount(): Promise<void> {
  await client.post("/plaid/sandbox-link");
  await client.post("/plaid/sync");
  await client.post("/clustering/run");
  await client.post("/forecasting/run");
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const { data } = await client.get<CurrentUser>("/users/me");
  return data;
}

export async function updatePassword(password: string): Promise<void> {
  await client.patch("/users/me", { password });
}

export async function deleteAccount(): Promise<void> {
  await client.delete("/users/me");
}

export async function fetchPlaidStatus(): Promise<PlaidStatus> {
  const { data } = await client.get<PlaidStatus>("/plaid/status");
  return data;
}

export async function disconnectPlaidAccount(): Promise<void> {
  await client.delete("/plaid/item");
}
