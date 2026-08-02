export function SidebarNavItem({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-input px-4 py-2.5 text-left text-body-sm font-sans font-medium ${
        active ? "bg-white text-signal-blue" : "bg-transparent text-white/70 hover:text-white"
      }`}
    >
      {label}
    </button>
  );
}
