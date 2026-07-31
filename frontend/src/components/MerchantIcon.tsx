import { getMerchantColor } from "../lib/merchantColors";

export function MerchantIcon({ merchantName }: { merchantName: string }) {
  const initial = merchantName.trim().charAt(0).toUpperCase();

  return (
    <div
      className="w-7 h-7 rounded-avatar flex items-center justify-center shrink-0"
      style={{ backgroundColor: getMerchantColor(merchantName) }}
    >
      <span className="text-white font-sans font-medium text-xs leading-none">{initial}</span>
    </div>
  );
}
