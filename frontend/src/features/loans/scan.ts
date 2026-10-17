export type ScanKind = "member" | "copy" | "empty";

const MEMBER_PREFIX = "UYE-";

/** Okutulan değerin üye numarası mı nüsha barkodu mu olduğunu ayırır. */
export function classifyScan(raw: string): ScanKind {
  const value = raw.trim().toUpperCase();
  if (!value) return "empty";
  return value.startsWith(MEMBER_PREFIX) ? "member" : "copy";
}
