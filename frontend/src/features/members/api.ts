import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { toQueryString, type Page } from "../../api/types";

export type MemberType = "student" | "staff" | "public";
export type MemberStatus = "active" | "suspended" | "expired";
export type LoanStatus = "active" | "returned" | "overdue" | "lost";
export type FineReason = "overdue" | "lost" | "damaged";
export type FineStatus = "unpaid" | "paid" | "waived";
export type ReservationStatus = "waiting" | "ready" | "fulfilled" | "cancelled" | "expired";

export interface MemberSummary {
  id: number;
  member_no: string;
  full_name: string;
  email: string;
  phone: string | null;
  member_type: MemberType;
  status: MemberStatus;
  membership_end: string;
  active_loan_count: number;
}

export interface MemberDetail extends MemberSummary {
  user_id: number;
  address: string | null;
  membership_start: string;
  unpaid_fine_total: string;
}

export interface MemberInput {
  email: string;
  full_name: string;
  phone: string | null;
  address: string | null;
  member_type: MemberType;
  membership_start: string;
  membership_end: string;
  password?: string;
}

export interface MemberLoan {
  id: number;
  book_id: number;
  book_title: string;
  barcode: string;
  loan_date: string;
  due_date: string;
  return_date: string | null;
  renew_count: number;
  status: LoanStatus;
}

export interface MemberFine {
  id: number;
  loan_id: number;
  amount: string;
  reason: FineReason;
  status: FineStatus;
  created_at: string;
  paid_at: string | null;
}

export interface MemberReservation {
  id: number;
  book_id: number;
  book_title: string;
  status: ReservationStatus;
  created_at: string;
  ready_at: string | null;
  expires_at: string | null;
}

export interface MemberQuery {
  q?: string;
  status?: MemberStatus;
  page?: number;
  size?: number;
}

export const MEMBER_TYPE_LABELS: Record<MemberType, string> = {
  student: "Öğrenci",
  staff: "Personel",
  public: "Genel",
};

export const MEMBER_STATUS_LABELS: Record<MemberStatus, string> = {
  active: "Aktif",
  suspended: "Askıda",
  expired: "Süresi dolmuş",
};

export const LOAN_STATUS_LABELS: Record<LoanStatus, string> = {
  active: "Ödünçte",
  returned: "İade edildi",
  overdue: "Gecikmiş",
  lost: "Kayıp",
};

export const FINE_REASON_LABELS: Record<FineReason, string> = {
  overdue: "Gecikme",
  lost: "Kayıp",
  damaged: "Hasar",
};

export const FINE_STATUS_LABELS: Record<FineStatus, string> = {
  unpaid: "Ödenmedi",
  paid: "Ödendi",
  waived: "Affedildi",
};

export const RESERVATION_STATUS_LABELS: Record<ReservationStatus, string> = {
  waiting: "Sırada",
  ready: "Hazır",
  fulfilled: "Teslim edildi",
  cancelled: "İptal",
  expired: "Süresi doldu",
};

const keys = {
  all: ["members"] as const,
  list: (query: MemberQuery) => ["members", "list", query] as const,
  detail: (id: number) => ["members", "detail", id] as const,
  history: (id: number, kind: string) => ["members", "history", id, kind] as const,
};

export function useMembers(query: MemberQuery) {
  return useQuery({
    queryKey: keys.list(query),
    queryFn: () => apiFetch<Page<MemberSummary>>(`/members${toQueryString({ ...query })}`),
    placeholderData: (previous) => previous,
  });
}

export function useMember(id: number | undefined) {
  return useQuery({
    queryKey: keys.detail(id ?? 0),
    queryFn: () => apiFetch<MemberDetail>(`/members/${id}`),
    enabled: id !== undefined,
  });
}

export function useMemberLoans(id: number) {
  return useQuery({
    queryKey: keys.history(id, "loans"),
    queryFn: () => apiFetch<MemberLoan[]>(`/members/${id}/loans`),
  });
}

export function useMemberFines(id: number) {
  return useQuery({
    queryKey: keys.history(id, "fines"),
    queryFn: () => apiFetch<MemberFine[]>(`/members/${id}/fines`),
  });
}

export function useMemberReservations(id: number) {
  return useQuery({
    queryKey: keys.history(id, "reservations"),
    queryFn: () => apiFetch<MemberReservation[]>(`/members/${id}/reservations`),
  });
}

export function useSaveMember(id?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MemberInput) =>
      apiFetch<MemberDetail>(id ? `/members/${id}` : "/members", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.all }),
  });
}

export function useSetMemberStatus(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (action: "suspend" | "activate") =>
      apiFetch<MemberDetail>(`/members/${id}/${action}`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.all }),
  });
}
