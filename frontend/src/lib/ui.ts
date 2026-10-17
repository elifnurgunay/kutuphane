import { ApiError } from "../api/client";

export const inputClass =
  "w-full rounded border border-sage bg-cream px-3 py-2 text-ink outline-none focus:ring-2 focus:ring-leaf";
export const primaryButton =
  "rounded bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand/90 disabled:opacity-60";
export const secondaryButton =
  "rounded bg-leaf px-4 py-2 text-sm font-medium text-white hover:bg-leaf/90 disabled:opacity-60";
export const outlineButton =
  "rounded border border-sage px-3 py-1.5 text-sm text-brand hover:bg-sage/30 disabled:opacity-60";
export const dangerButton =
  "rounded border border-danger px-3 py-1.5 text-sm text-danger hover:bg-danger/10 disabled:opacity-60";

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Beklenmeyen bir hata oluştu.";
}
