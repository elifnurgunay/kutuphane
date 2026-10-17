import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { toQueryString, type Page } from "../../api/types";

export type CopyStatus = "available" | "loaned" | "reserved" | "lost" | "damaged" | "maintenance";
export type ManualCopyStatus = "available" | "damaged" | "maintenance" | "lost";

export interface Author {
  id: number;
  full_name: string;
  birth_year: number | null;
  bio: string | null;
}

export interface Publisher {
  id: number;
  name: string;
}

export interface Category {
  id: number;
  name: string;
  parent_id: number | null;
}

export interface BookSummary {
  id: number;
  isbn: string | null;
  title: string;
  subtitle: string | null;
  publish_year: number | null;
  publisher: Publisher | null;
  authors: { id: number; full_name: string }[];
  categories: Category[];
  copy_count: number;
  available_count: number;
}

export interface BookDetail extends BookSummary {
  page_count: number | null;
  language: string | null;
  description: string | null;
  cover_url: string | null;
  created_at: string;
}

export interface BookInput {
  isbn: string | null;
  title: string;
  subtitle: string | null;
  publisher_id: number | null;
  publish_year: number | null;
  page_count: number | null;
  language: string | null;
  description: string | null;
  cover_url: string | null;
  author_ids: number[];
  category_ids: number[];
}

export interface Copy {
  id: number;
  book_id: number;
  barcode: string;
  shelf_location: string | null;
  status: CopyStatus;
  acquired_at: string | null;
  notes: string | null;
}

export interface CopyInput {
  shelf_location: string | null;
  acquired_at: string | null;
  notes: string | null;
  status?: ManualCopyStatus;
}

export interface BookQuery {
  q?: string;
  category?: number;
  available?: boolean;
  sort?: string;
  page?: number;
  size?: number;
}

export const COPY_STATUS_LABELS: Record<CopyStatus, string> = {
  available: "Müsait",
  loaned: "Ödünçte",
  reserved: "Ayrıldı",
  lost: "Kayıp",
  damaged: "Hasarlı",
  maintenance: "Bakımda",
};

export const MANUAL_COPY_STATUSES: ManualCopyStatus[] = [
  "available",
  "damaged",
  "maintenance",
  "lost",
];

const keys = {
  books: ["books"] as const,
  list: (query: BookQuery) => ["books", "list", query] as const,
  detail: (id: number) => ["books", "detail", id] as const,
  copies: (id: number) => ["books", "copies", id] as const,
};

export function useBooks(query: BookQuery) {
  return useQuery({
    queryKey: keys.list(query),
    queryFn: () => apiFetch<Page<BookSummary>>(`/books${toQueryString({ ...query })}`),
    placeholderData: (previous) => previous,
  });
}

export function useBook(id: number | undefined) {
  return useQuery({
    queryKey: keys.detail(id ?? 0),
    queryFn: () => apiFetch<BookDetail>(`/books/${id}`),
    enabled: id !== undefined,
  });
}

export function useCopies(bookId: number) {
  return useQuery({
    queryKey: keys.copies(bookId),
    queryFn: () => apiFetch<Copy[]>(`/books/${bookId}/copies`),
  });
}

export function useAuthors() {
  return useQuery({
    queryKey: ["authors", "all"],
    queryFn: () => apiFetch<Page<Author>>("/authors?size=500"),
    select: (page) => page.items,
  });
}

export function usePublishers() {
  return useQuery({
    queryKey: ["publishers", "all"],
    queryFn: () => apiFetch<Page<Publisher>>("/publishers?size=500"),
    select: (page) => page.items,
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => apiFetch<Category[]>("/categories"),
  });
}

function jsonBody(body: unknown): RequestInit {
  return { body: JSON.stringify(body) };
}

export function useSaveBook(id?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: BookInput) =>
      apiFetch<BookDetail>(id ? `/books/${id}` : "/books", {
        method: id ? "PUT" : "POST",
        ...jsonBody(input),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.books }),
  });
}

export function useDeleteBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/books/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.books }),
  });
}

export function useAddCopy(bookId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CopyInput) =>
      apiFetch<Copy>(`/books/${bookId}/copies`, { method: "POST", ...jsonBody(input) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.books }),
  });
}

export function useUpdateCopy(bookId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: CopyInput }) =>
      apiFetch<Copy>(`/copies/${id}`, { method: "PUT", ...jsonBody(input) }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: keys.copies(bookId) });
      void queryClient.invalidateQueries({ queryKey: keys.books });
    },
  });
}

export function useCreateAuthor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (full_name: string) =>
      apiFetch<Author>("/authors", { method: "POST", ...jsonBody({ full_name }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["authors"] }),
  });
}

export function useCreatePublisher() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiFetch<Publisher>("/publishers", { method: "POST", ...jsonBody({ name }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["publishers"] }),
  });
}
