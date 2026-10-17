import { COPY_STATUS_LABELS, type CopyStatus } from "./api";

const STATUS_CLASSES: Record<CopyStatus, string> = {
  available: "bg-leaf text-white",
  loaned: "bg-warning text-white",
  reserved: "bg-sage text-brand",
  lost: "bg-danger text-white",
  damaged: "bg-danger text-white",
  maintenance: "bg-cream text-brand border border-sage",
};

export function CopyStatusBadge({ status }: { status: CopyStatus }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs ${STATUS_CLASSES[status]}`}>
      {COPY_STATUS_LABELS[status]}
    </span>
  );
}
