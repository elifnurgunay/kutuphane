import {
  LOAN_STATUS_LABELS,
  MEMBER_STATUS_LABELS,
  type LoanStatus,
  type MemberStatus,
} from "./api";
import type { DueState } from "./dueState";

const badge = "inline-block rounded px-2 py-0.5 text-xs";

const MEMBER_STATUS_CLASSES: Record<MemberStatus, string> = {
  active: "bg-leaf text-white",
  suspended: "bg-danger text-white",
  expired: "bg-warning text-white",
};

export function MemberStatusBadge({ status }: { status: MemberStatus }) {
  return (
    <span className={`${badge} ${MEMBER_STATUS_CLASSES[status]}`}>
      {MEMBER_STATUS_LABELS[status]}
    </span>
  );
}

const LOAN_STATUS_CLASSES: Record<LoanStatus, string> = {
  active: "bg-sage text-brand",
  returned: "bg-cream text-brand border border-sage",
  overdue: "bg-danger text-white",
  lost: "bg-danger text-white",
};

const DUE_CLASSES: Record<DueState, string> = {
  overdue: "bg-danger text-white",
  soon: "bg-warning text-white",
  ok: "",
};

export function LoanStatusBadge({ status, due }: { status: LoanStatus; due?: DueState }) {
  // Günlük görev gecikmeyi henüz işaretlemediyse de vadesi geçen ödünç kırmızı görünür.
  const classes = due && due !== "ok" ? DUE_CLASSES[due] : LOAN_STATUS_CLASSES[status];
  const label = due === "overdue" ? LOAN_STATUS_LABELS.overdue : LOAN_STATUS_LABELS[status];
  return <span className={`${badge} ${classes}`}>{label}</span>;
}
