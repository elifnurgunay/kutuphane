/** "2026-10-10" veya ISO zaman damgasını "10.10.2026" biçimine çevirir. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return "—";
  return `${day}.${month}.${year}`;
}

export function formatMoney(value: number | string): string {
  const amount = Number(value).toLocaleString("tr-TR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${amount} ₺`;
}

/** Bugünün tarihini yerel saate göre "yyyy-MM-dd" olarak döner. */
export function todayIso(now: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/** "yyyy-MM-dd" tarihine gün ekler. */
export function addDaysIso(isoDate: string, days: number): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  return todayIso(new Date(y, m - 1, d + days));
}
