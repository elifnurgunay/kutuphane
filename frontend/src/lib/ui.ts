import { ApiError } from "../api/client";

const button =
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-leaf focus-visible:ring-offset-2 focus-visible:ring-offset-cream disabled:pointer-events-none disabled:opacity-60";

export const inputClass =
  "w-full rounded-lg border border-sage bg-cream px-3 py-2 text-ink placeholder:text-ink/40 outline-none transition focus:border-leaf focus:ring-2 focus:ring-leaf/40";
export const primaryButton = `${button} bg-brand px-4 py-2 text-white shadow-sm hover:bg-brand/90`;
export const secondaryButton = `${button} bg-leaf px-4 py-2 text-white shadow-sm hover:bg-leaf/90`;
export const outlineButton = `${button} border border-sage bg-surface px-3 py-1.5 text-brand hover:bg-sage/25`;
export const dangerButton = `${button} border border-danger bg-surface px-3 py-1.5 text-danger hover:bg-danger/10`;
export const dangerSolidButton = `${button} bg-danger px-4 py-2 text-white shadow-sm hover:bg-danger/90`;

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Beklenmeyen bir hata oluştu.";
}
