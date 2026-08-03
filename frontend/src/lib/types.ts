export interface LatestTransaction {
  amount: number;
  posted_date: string;
  deviation_pct: number | null;
  is_drift: boolean;
}

export interface SubscriptionSummary {
  id: number;
  merchant_name: string | null;
  forecast_amount: number | null;
  forecast_date: string | null;
  latest_transaction: LatestTransaction | null;
}

export interface TransactionRow {
  id: number;
  merchant_name: string;
  amount: number;
  posted_date: string;
  expected_amount: number | null;
  deviation_pct: number | null;
  is_drift: boolean;
}

export interface SparklinePoint {
  date: string;
  amount: number;
}

export interface StatsSummary {
  total_monthly_spend: number;
  active_subscriptions_count: number;
  flagged_this_month_count: number;
  sparkline: SparklinePoint[];
}

export interface BreakdownEntry {
  merchant_name: string;
  amount: number;
}

export interface CurrentUser {
  id: string;
  email: string;
}

export interface PlaidStatus {
  connected: boolean;
  linked_at: string | null;
}

export interface SubscriptionDetail {
  id: number;
  merchant_name: string | null;
  forecast_amount: number | null;
  forecast_date: string | null;
  transactions: TransactionRow[];
}

export interface AlertsTimelinePoint {
  week_start: string;
  count: number;
}
