import type { ButtonHTMLAttributes } from "react";

export function PrimaryButton({ children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`rounded-input border border-[#183fae] bg-signal-blue px-5 py-2.5 text-body-sm font-sans font-medium text-white ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
