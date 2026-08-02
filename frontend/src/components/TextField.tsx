import type { InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export function TextField({ label, className = "", id, ...props }: TextFieldProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-body-sm font-sans font-medium text-ink">
        {label}
      </label>
      <input
        id={inputId}
        className={`rounded-input border border-hairline px-4 py-2.5 text-body-sm font-sans text-ink outline-none focus:border-signal-blue ${className}`}
        {...props}
      />
    </div>
  );
}
