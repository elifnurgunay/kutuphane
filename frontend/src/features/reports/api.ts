import { useQuery } from "@tanstack/react-query";
import { apiDownload, apiFetch } from "../../api/client";
import { toQueryString } from "../../api/types";

export interface Activity {
  kind: "loan" | "return";
  day: string;
  loan_id: number;
  book_title: string;
  member_name: string;
  member_no: string;
}

export interface Dashboard {
  total_books: number;
  total_copies: number;
  available_copies: number;
  active_members: number;
  open_loans: number;
  overdue_loans: number;
  loans_today: number;
  returns_today: number;
  unpaid_fine_total: string;
  recent_activity: Activity[];
}

export interface PopularBook {
  book_id: number;
  title: string;
  authors: string;
  loan_count: number;
}

export interface OverdueItem {
  loan_id: number;
  book_title: string;
  barcode: string;
  member_id: number;
  member_no: string;
  member_name: string;
  phone: string | null;
  due_date: string;
  days_late: number;
  estimated_fine: string;
}

export interface ActiveMember {
  member_id: number;
  member_no: string;
  full_name: string;
  loan_count: number;
}

export interface CategoryStat {
  category_id: number;
  name: string;
  book_count: number;
  copy_count: number;
  loan_count: number;
}

export interface Period {
  from?: string;
  to?: string;
}

export type ReportName = "popular-books" | "overdue" | "active-members" | "category-stats";

function reportQuery<T>(name: ReportName, params: Record<string, string | number | undefined>) {
  return {
    queryKey: ["reports", name, params],
    queryFn: () => apiFetch<T>(`/reports/${name}${toQueryString(params)}`),
  };
}

export function useDashboard() {
  return useQuery({
    queryKey: ["reports", "dashboard"],
    queryFn: () => apiFetch<Dashboard>("/reports/dashboard"),
  });
}

export function usePopularBooks(period: Period, limit = 10) {
  return useQuery(reportQuery<PopularBook[]>("popular-books", { ...period, limit }));
}

export function useOverdue() {
  return useQuery(reportQuery<OverdueItem[]>("overdue", {}));
}

export function useActiveMembers(period: Period, limit = 10) {
  return useQuery(reportQuery<ActiveMember[]>("active-members", { ...period, limit }));
}

export function useCategoryStats(period: Period) {
  return useQuery(reportQuery<CategoryStat[]>("category-stats", { ...period }));
}

export function downloadReport(name: ReportName, period: Period, limit?: number) {
  const query = toQueryString({ ...period, limit, format: "csv" });
  return apiDownload(`/reports/${name}${query}`, `${name}.csv`);
}
