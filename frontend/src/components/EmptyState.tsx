import { DriftMeter } from "./DriftMeter";
import { PrimaryButton } from "./PrimaryButton";

export function EmptyState({ onConnect }: { onConnect?: () => void }) {
  return (
    <div className="flex flex-col items-center py-24 text-center">
      <div className="w-full max-w-md">
        <DriftMeter
          expectedAmount={0}
          actualAmount={0}
          deviationPct={null}
          isDrift={false}
          variant="compact"
          size="large"
        />
      </div>

      <h1 className="mt-10 text-heading-lg font-serif font-medium text-ink">
        Connect an account to start tracking
      </h1>
      <p className="mt-3 max-w-sm text-body font-sans text-slate">
        Driftline watches your transactions for recurring charges and alerts you the
        moment one deviates from what's expected.
      </p>

      <div className="mt-8">
        <PrimaryButton onClick={onConnect}>Connect account</PrimaryButton>
      </div>
    </div>
  );
}
