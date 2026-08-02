import axios from "axios";
import type { BreakdownEntry, StatsSummary, SubscriptionSummary, TransactionRow } from "./types";

const client = axios.create({ baseURL: "http://localhost:8000" });

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
