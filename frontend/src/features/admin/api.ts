import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { toQueryString, type Page } from "../../api/types";

export type StaffRole = "admin" | "librarian";

export interface StaffUser {
  id: number;
  email: string;
  full_name: string;
  role: StaffRole;
  is_active: boolean;
  created_at: string;
}

export interface StaffInput {
  email: string;
  full_name: string;
  role: StaffRole;
  is_active?: boolean;
  password?: string;
}

export interface AuditLog {
  id: number;
  user_id: number | null;
  user_name: string | null;
  action: string;
  entity: string;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export const SETTING_LABELS: Record<string, { label: string; hint: string }> = {
  loan_days: { label: "Ödünç süresi (gün)", hint: "Yeni ödünç ve uzatmalarda son teslim tarihi." },
  max_loans_student: { label: "Ödünç limiti — öğrenci", hint: "Aynı anda alınabilecek kitap." },
  max_loans_staff: { label: "Ödünç limiti — personel", hint: "Aynı anda alınabilecek kitap." },
  max_loans_public: { label: "Ödünç limiti — genel", hint: "Aynı anda alınabilecek kitap." },
  max_renewals: { label: "En fazla süre uzatma", hint: "Bir ödünç kaç kez uzatılabilir." },
  reservation_hold_days: {
    label: "Rezervasyon bekletme (gün)",
    hint: "Hazır rezervasyon bu süre içinde alınmazsa sıradakine geçer.",
  },
  daily_fine: { label: "Günlük gecikme cezası (₺)", hint: "Geciken her gün için." },
  max_unpaid_fine: {
    label: "Ödünç engeli ceza sınırı (₺)",
    hint: "Ödenmemiş ceza bu tutara ulaşınca üye kitap alamaz.",
  },
  lost_book_fine: { label: "Kayıp kitap cezası (₺)", hint: "Kayıp işaretlenen ödünç için." },
};

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => apiFetch<Record<string, string>>("/settings"),
  });
}

export function useSaveSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, string>) =>
      apiFetch<Record<string, string>>("/settings", {
        method: "PUT",
        body: JSON.stringify(values),
      }),
    onSuccess: (data) => queryClient.setQueryData(["settings"], data),
  });
}

export function useStaff() {
  return useQuery({ queryKey: ["staff"], queryFn: () => apiFetch<StaffUser[]>("/staff") });
}

export function useSaveStaff() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: StaffInput }) =>
      apiFetch<StaffUser>(id ? `/staff/${id}` : "/staff", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["staff"] }),
  });
}

export function useResetStaffPassword() {
  return useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      apiFetch<void>(`/staff/${id}/reset-password`, {
        method: "POST",
        body: JSON.stringify({ new_password: password }),
      }),
  });
}

export function useAuditLogs(query: { entity?: string; page?: number; size?: number }) {
  return useQuery({
    queryKey: ["audit-logs", query],
    queryFn: () => apiFetch<Page<AuditLog>>(`/audit-logs${toQueryString({ ...query })}`),
    placeholderData: (previous) => previous,
  });
}
