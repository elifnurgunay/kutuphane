const API_BASE = "/api/v1";
const ACCESS_KEY = "kutuphane.access_token";
const REFRESH_KEY = "kutuphane.refresh_token";
const NO_REFRESH_PATHS = ["/auth/login", "/auth/refresh"];

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export const tokenStore = {
  get access(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(pair: TokenPair): void {
    localStorage.setItem(ACCESS_KEY, pair.access_token);
    localStorage.setItem(REFRESH_KEY, pair.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

let onUnauthorized: () => void = () => {};

/** Oturum yenilenemediğinde çağrılır (ör. kullanıcıyı giriş sayfasına göndermek için). */
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json();
    if (body?.error?.code) {
      return new ApiError(response.status, body.error.code, body.error.message);
    }
  } catch {
    // JSON olmayan yanıt
  }
  return new ApiError(response.status, "HTTP_ERROR", "Beklenmeyen bir hata oluştu.");
}

let refreshInFlight: Promise<boolean> | null = null;

/** Aynı anda gelen 401'ler için tek bir yenileme isteği yapar. */
function refreshTokens(): Promise<boolean> {
  refreshInFlight ??= (async () => {
    const refreshToken = tokenStore.refresh;
    if (!refreshToken) return false;
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) return false;
    tokenStore.set(await response.json());
    return true;
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  const accessToken = tokenStore.access;
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (response.status === 401 && retry && !NO_REFRESH_PATHS.includes(path) && tokenStore.refresh) {
    if (await refreshTokens()) return apiFetch<T>(path, init, false);
    tokenStore.clear();
    onUnauthorized();
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
