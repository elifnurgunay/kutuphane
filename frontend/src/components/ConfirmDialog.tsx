import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { ConfirmContext, type ConfirmOptions } from "../lib/confirm";
import { dangerSolidButton, outlineButton, primaryButton } from "../lib/ui";

interface Pending extends ConfirmOptions {
  resolve: (value: boolean) => void;
}

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<Pending | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);

  const confirm = useCallback(
    (options: ConfirmOptions) =>
      new Promise<boolean>((resolve) => setPending({ ...options, resolve })),
    [],
  );

  useEffect(() => {
    const dialog = dialogRef.current;
    if (pending && dialog && !dialog.open) dialog.showModal();
  }, [pending]);

  function close(result: boolean) {
    pending?.resolve(result);
    dialogRef.current?.close();
    setPending(null);
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <dialog
        ref={dialogRef}
        onCancel={(e) => {
          e.preventDefault();
          close(false);
        }}
        className="w-[min(28rem,calc(100vw-2rem))] rounded-xl border border-sage bg-surface p-0 text-ink shadow-xl backdrop:bg-ink/40"
      >
        {pending && (
          <div className="p-6">
            <h2 className="text-lg font-semibold text-brand">{pending.title}</h2>
            {pending.message && <p className="mt-2 text-sm text-ink/80">{pending.message}</p>}
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" className={outlineButton} onClick={() => close(false)}>
                Vazgeç
              </button>
              <button
                type="button"
                autoFocus
                className={pending.tone === "danger" ? dangerSolidButton : primaryButton}
                onClick={() => close(true)}
              >
                {pending.confirmLabel ?? "Onayla"}
              </button>
            </div>
          </div>
        )}
      </dialog>
    </ConfirmContext.Provider>
  );
}
