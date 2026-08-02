import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { PrimaryButton } from "../components/PrimaryButton";
import { SubscriptionCard } from "../components/SubscriptionCard";
import { connectSandboxAccount, fetchSubscriptions } from "../lib/api";
import type { SubscriptionSummary } from "../lib/types";

export function Subscriptions() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionSummary[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string | null>(null);
  const navigate = useNavigate();

  function refetch() {
    setLoadError(null);
    fetchSubscriptions()
      .then(setSubscriptions)
      .catch(() => setLoadError("Couldn't load your subscriptions. Check your connection and try again."));
  }

  useEffect(() => {
    refetch();
  }, []);

  async function handleConnect() {
    setConnecting(true);
    setConnectError(null);
    try {
      await connectSandboxAccount();
      await waitForSubscriptions();
    } catch {
      setConnectError("Couldn't connect your account. Please try again.");
      setConnecting(false);
    }
  }

  async function waitForSubscriptions(maxAttempts = 15, delayMs = 3000) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const subs = await fetchSubscriptions();
      if (subs.length > 0) {
        setSubscriptions(subs);
        setConnecting(false);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    refetch();
    setConnecting(false);
  }

  if (loadError) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{loadError}</p>
        <PrimaryButton onClick={refetch}>Try again</PrimaryButton>
      </div>
    );
  }

  if (subscriptions === null) {
    return null;
  }

  if (subscriptions.length === 0) {
    return <EmptyState onConnect={handleConnect} connecting={connecting} error={connectError} />;
  }

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Subscriptions</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          Every recurring charge Driftline has found, with its forecast and drift status.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {subscriptions.map((sub) => (
          <button
            key={sub.id}
            onClick={() => navigate(`/subscriptions/${sub.id}`)}
            className="cursor-pointer text-left transition hover:opacity-80"
          >
            <SubscriptionCard subscription={sub} />
          </button>
        ))}
      </div>
    </div>
  );
}
