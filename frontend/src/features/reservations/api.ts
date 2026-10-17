import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { toQueryString, type Page } from "../../api/types";
import type { FineReason, FineStatus, ReservationStatus } from "../members/api";

export interface Reservation {
  id: number;
  book_id: number;
  book_title: string;
  member_id: number;
  member_no: string;
  member_name: string;
  status: ReservationStatus;
  queue_position: number | null;
  created_at: string;
  ready_at: string | null;
  expires_at: string | null;
  assigned_barcode: string | null;
}

export interface ReservationQuery {
  book_id?: number;
  member_id?: number;
  status?: ReservationStatus;
  page?: number;
  size?: number;
}

export interface FineDetail {
  id: number;
  loan_id: number;
  member_id: number;
  member_no: string;
  member_name: string;
  book_title: string;
  barcode: string;
  amount: string;
  reason: FineReason;
  status: FineStatus;
  created_at: string;
  paid_at: string | null;
}

export interface FinePage extends Page<FineDetail> {
  total_amount: string;
}

export interface FineQuery {
  status?: FineStatus;
  member_id?: number;
  page?: number;
  size?: number;
}

/** Rezervasyon, ceza ve ödünç işlemleri birbirini etkiler; ilgili önbellekleri tazele. */
function useInvalidateCirculation() {
  const queryClient = useQueryClient();
  return () => {
    for (const key of ["reservations", "fines", "loans", "books", "members"]) {
      void queryClient.invalidateQueries({ queryKey: [key] });
    }
  };
}

export function useReservations(query: ReservationQuery) {
  return useQuery({
    queryKey: ["reservations", query],
    queryFn: () => apiFetch<Page<Reservation>>(`/reservations${toQueryString({ ...query })}`),
    placeholderData: (previous) => previous,
  });
}

export function useCreateReservation() {
  const invalidate = useInvalidateCirculation();
  return useMutation({
    mutationFn: (input: { book_id: number; member_id: number }) =>
      apiFetch<Reservation>("/reservations", { method: "POST", body: JSON.stringify(input) }),
    onSuccess: invalidate,
  });
}

export function useCancelReservation() {
  const invalidate = useInvalidateCirculation();
  return useMutation({
    mutationFn: (id: number) => apiFetch<Reservation>(`/reservations/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}

export function useFines(query: FineQuery) {
  return useQuery({
    queryKey: ["fines", query],
    queryFn: () => apiFetch<FinePage>(`/fines${toQueryString({ ...query })}`),
    placeholderData: (previous) => previous,
  });
}

export function useCloseFine() {
  const invalidate = useInvalidateCirculation();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "pay" | "waive" }) =>
      apiFetch<FineDetail>(`/fines/${id}/${action}`, { method: "POST" }),
    onSuccess: invalidate,
  });
}
