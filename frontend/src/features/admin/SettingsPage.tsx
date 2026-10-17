import { useState } from "react";
import type { FormEvent } from "react";
import { Card, ErrorMessage, LoadingState } from "../../components/ui";
import { inputClass, primaryButton } from "../../lib/ui";
import { SETTING_LABELS, useSaveSettings, useSettings } from "./api";

export function SettingsPage() {
  const settings = useSettings();
  if (settings.isPending) return <LoadingState />;
  if (settings.error) return <ErrorMessage error={settings.error} />;
  return <SettingsForm initial={settings.data} />;
}

function SettingsForm({ initial }: { initial: Record<string, string> }) {
  const [values, setValues] = useState(initial);
  const [saved, setSaved] = useState(false);
  const save = useSaveSettings();
  const keys = Object.keys(SETTING_LABELS).filter((key) => key in values);
  const changed = keys.filter((key) => values[key] !== initial[key]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaved(false);
    const payload = Object.fromEntries(changed.map((key) => [key, values[key]]));
    save.mutate(payload, {
      onSuccess: (data) => {
        setValues(data);
        setSaved(true);
      },
    });
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold text-brand">Sistem ayarları</h1>
        <p className="text-sm text-ink/70">
          Değişiklikler kaydedildiği andan itibaren yeni işlemlerde kullanılır.
        </p>
      </div>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-5 md:grid-cols-2">
            {keys.map((key) => (
              <label key={key} className="block space-y-1">
                <span className="text-sm font-medium">{SETTING_LABELS[key].label}</span>
                <input
                  inputMode="decimal"
                  required
                  value={values[key]}
                  onChange={(e) => {
                    setSaved(false);
                    setValues((prev) => ({ ...prev, [key]: e.target.value }));
                  }}
                  className={`${inputClass} ${values[key] !== initial[key] ? "border-leaf" : ""}`}
                />
                <span className="block text-xs text-ink/60">{SETTING_LABELS[key].hint}</span>
              </label>
            ))}
          </div>
          <ErrorMessage error={save.error} />
          {saved && (
            <p role="status" className="rounded-lg bg-leaf/10 px-3 py-2 text-sm text-leaf">
              Ayarlar kaydedildi.
            </p>
          )}
          <button
            type="submit"
            className={primaryButton}
            disabled={save.isPending || changed.length === 0}
          >
            {changed.length > 0 ? `Kaydet (${changed.length} değişiklik)` : "Kaydet"}
          </button>
        </form>
      </Card>
    </div>
  );
}
