export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

type QueryValue = string | number | boolean | null | undefined;

/** Boş değerleri atlayarak sorgu dizesi üretir ("?a=1&b=x" veya ""). */
export function toQueryString(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}
