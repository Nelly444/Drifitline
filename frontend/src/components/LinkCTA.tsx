import type { ButtonHTMLAttributes } from "react";

export function LinkCTA({ children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`inline-flex items-center gap-1 text-body-sm font-sans font-medium text-signal-blue ${className}`}
      {...props}
    >
      {children}
      <span aria-hidden="true">→</span>
    </button>
  );
}
