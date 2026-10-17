import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import type { MemberDetail, MemberFine, MemberLoan } from "../members/api";
import type { Reservation } from "../reservations/api";

const ME = ["me"] as const;

export function useMyProfile() {
  return useQuery({
    queryKey: [...ME, "profile"],
    queryFn: () => apiFetch<MemberDetail>("/me/profile"),
  });
}

export function useMyLoans() {
  return useQuery({
    queryKey: [...ME, "loans"],
    queryFn: () => apiFetch<MemberLoan[]>("/me/loans"),
  });
}

export function useMyFines() {
  return useQuery({
    queryKey: [...ME, "fines"],
    queryFn: () => apiFetch<MemberFine[]>("/me/fines"),
  });
}

export function useMyReservations() {
  return useQuery({
    queryKey: [...ME, "reservations"],
    queryFn: () => apiFetch<Reservation[]>("/me/reservations"),
  });
}

function useMeMutation<TInput, TResult>(fn: (input: TInput) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ME });
      void queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });
}

export function useRenewMyLoan() {
  return useMeMutation((loanId: number) =>
    apiFetch<MemberLoan>(`/me/loans/${loanId}/renew`, { method: "POST" }),
  );
}

export function useReserveBook() {
  return useMeMutation((bookId: number) =>
    apiFetch<Reservation>("/me/reservations", {
      method: "POST",
      body: JSON.stringify({ book_id: bookId }),
    }),
  );
}

export function useCancelMyReservation() {
  return useMeMutation((id: number) =>
    apiFetch<Reservation>(`/me/reservations/${id}`, { method: "DELETE" }),
  );
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (input: { current_password: string; new_password: string }) =>
      apiFetch<void>("/auth/change-password", { method: "POST", body: JSON.stringify(input) }),
  });
}

/** Son teslime kalan gün (negatifse gecikme günü). */
export function daysLeft(dueDate: string, today: string): number {
  const toUtc = (iso: string) => {
    const [y, m, d] = iso.split("-").map(Number);
    return Date.UTC(y, m - 1, d);
  };
  return Math.round((toUtc(dueDate) - toUtc(today)) / 86_400_000);
}
