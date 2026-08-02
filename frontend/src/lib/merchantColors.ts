// Real brand colors for merchants that actually appear in our data - "the system's
// actual source of color variety" per driftline-design.md, not invented decoration.
const KNOWN_MERCHANT_COLORS: Record<string, string> = {
  "NETFLIX INC": "#E50914",
  "SPOTIFY INC": "#1DB954",
  "AMAZON": "#FF9900",
  "APPLE": "#000000",
  "OPENAI": "#10A37F",
  "MCDONALD'S INC": "#DA291C",
  "SWEETGREEN": "#005243",
  "UBER": "#000000",
  "MICROSOFT": "#00A4EF",
  "VENMO INC": "#3D95CE",
};

// Deliberately avoids Signal Blue/Moss/Rust/Amber hexes - those four are reserved for
// the functional action/status system, not merchant decoration.
const FALLBACK_PALETTE = ["#7C5CFC", "#06B6D4", "#EC4899", "#F97316", "#8B5CF6", "#0D9488"];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function getMerchantColor(merchantName: string): string {
  const known = KNOWN_MERCHANT_COLORS[merchantName.toUpperCase()];
  if (known) return known;
  return FALLBACK_PALETTE[hashString(merchantName) % FALLBACK_PALETTE.length];
}
