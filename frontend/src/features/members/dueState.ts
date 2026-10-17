import { addDaysIso } from "../../lib/format";

export type DueState = "overdue" | "soon" | "ok";

/** Vadesine 2 gün kalanlar "yaklaşan" sayılır (hatırlatma kuralıyla aynı). */
const DUE_SOON_DAYS = 2;

/** İade edilmemiş bir ödüncün son teslim tarihine göre durumu. */
export function dueState(dueDate: string, today: string): DueState {
  if (dueDate < today) return "overdue";
  if (dueDate <= addDaysIso(today, DUE_SOON_DAYS)) return "soon";
  return "ok";
}
