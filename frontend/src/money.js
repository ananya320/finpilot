export function fmt(value, symbol = "$") {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  const locale = symbol === "₹" ? "en-IN" : "en-US";
  const abs = Math.abs(n).toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return `${n < 0 ? "-" : ""}${symbol}${abs}`;
}