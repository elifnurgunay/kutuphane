import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { toQueryString, type Page } from "../../api/types";
import type { FineReason, FineStatus, LoanStatus, MemberSummary } from "../members/api";
import type { CopyStatus } from "../books/api";

export interface Loan {
  id: number;
  copy_id: number;
  barcode: string;
  book_id: number;
  book_title: string;
  member_id: number;
  member_no: string;
  member_name: string;
  loan_date: string;
  due_date: string;
  return_date: string | null;
  renew_count: number;
  status: LoanStatus;
}

export interface Fine {
  id: number;
  amount: string;
  reason: FineReason;
  status: FineStatus;
  created_at: string | null;
}

export interface ReturnResponse {
  loan: Loan;
  fines: Fine[];
  reserved_for: {
    reservation_id: number;
    member_id: number;
    member_no: string;
    member_name: string;
    expires_at: string | null;
  } | null;
}

export interface Eligibility {
  can_borrow: boolean;
  problems: { code: string; message: string }[];
  active_loan_count: number;
  loan_limit: number;
  unpaid_fine_total: string;
  max_unpaid_fine: string;
  overdue_count: number;
}

export interface CopyWithBook {
  id: number;
  book_id: number;
  barcode: string;
  shelf_location: string | null;
  status: CopyStatus;
  book: { id: number; title: string };
}

export type LoanFilter = "open" | "active" | "overdue" | "returned" | "lost";

export interface LoanQuery {
  status?: LoanFilter;
  member_id?: number;
  barcode?: string;
  page?: number;
  size?: number;
}

export interface ReturnInput {
  damaged?: boolean;
  damage_fine?: string | null;
  notes?: string | null;
}

const keys = {
  all: ["loans"] as const,
  list: (query: LoanQuery) => ["loans", "list", query] as const,
  eligibility: (memberId: number) => ["loans", "eligibility", memberId] as const,
};

export function fetchLoans(query: LoanQuery): Promise<Page<Loan>> {
  return apiFetch<Page<Loan>>(`/loans${toQueryString({ ...query })}`);
}

export function useLoans(query: LoanQuery, enabled = true) {
  return useQuery({
    queryKey: keys.list(query),
    queryFn: () => fetchLoans(query),
    placeholderData: (previous) => previous,
    enabled,
  });
}

export function useEligibility(memberId: number | undefined) {
  return useQuery({
    queryKey: keys.eligibility(memberId ?? 0),
    queryFn: () => apiFetch<Eligibility>(`/loans/eligibility/${memberId}`),
    enabled: memberId !== undefined,
  });
}

/** Üye numarasıyla tam eşleşen üyeyi bulur. */
export async function findMemberByNo(memberNo: string): Promise<MemberSummary | null> {
  const normalized = memberNo.trim().toUpperCase();
  const page = await apiFetch<Page<MemberSummary>>(`/members${toQueryString({ q: normalized })}`);
  return page.items.find((m) => m.member_no === normalized) ?? null;
}

export function findCopy(barcode: string): Promise<CopyWithBook> {
  return apiFetch<CopyWithBook>(`/copies/barcode/${encodeURIComponent(barcode.trim())}`);
}

export async function findOpenLoan(barcode: string): Promise<Loan | null> {
  const page = await fetchLoans({ barcode: barcode.trim(), status: "open", size: 1 });
  return page.items[0] ?? null;
}

function useLoanMutation<TInput, TResult>(fn: (input: TInput) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      // Ödünç işlemleri kitap müsaitliğini ve üye özetlerini de değiştirir.
      void queryClient.invalidateQueries({ queryKey: keys.all });
      void queryClient.invalidateQueries({ queryKey: ["books"] });
      void queryClient.invalidateQueries({ queryKey: ["members"] });
    },
  });
}

export function useIssueLoan() {
  return useLoanMutation((input: { member_id: number; barcode: string }) =>
    apiFetch<Loan>("/loans", { method: "POST", body: JSON.stringify(input) }),
  );
}

export function useReturnLoan() {
  return useLoanMutation(({ id, input }: { id: number; input?: ReturnInput }) =>
    apiFetch<ReturnResponse>(`/loans/${id}/return`, {
      method: "POST",
      body: JSON.stringify(input ?? {}),
    }),
  );
}

export function useRenewLoan() {
  return useLoanMutation((id: number) => apiFetch<Loan>(`/loans/${id}/renew`, { method: "POST" }));
}

export function useMarkLost() {
  return useLoanMutation((id: number) =>
    apiFetch<{ loan: Loan; fine: Fine }>(`/loans/${id}/mark-lost`, { method: "POST" }),
  );
}
