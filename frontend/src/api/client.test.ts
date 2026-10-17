import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, setUnauthorizedHandler, tokenStore } from "./client";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function memoryStorage(): Storage {
  const data = new Map<string, string>();
  return {
    get length() {
      return data.size;
    },
    clear: () => data.clear(),
    getItem: (key) => data.get(key) ?? null,
    key: (index) => [...data.keys()][index] ?? null,
    removeItem: (key) => void data.delete(key),
    setItem: (key, value) => void data.set(key, value),
  };
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("access token'ı Authorization başlığına ekler", async () => {
    tokenStore.set({ access_token: "A1", refresh_token: "R1" });
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    await expect(apiFetch("/auth/me")).resolves.toEqual({ ok: true });
    const headers = new Headers(fetchMock.mock.calls[0][1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer A1");
  });

  it("tek tip hata formatını ApiError'a çevirir", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(401, {
        error: { code: "INVALID_CREDENTIALS", message: "E-posta veya şifre hatalı." },
      }),
    );

    const error = (await apiFetch("/auth/login", { method: "POST", body: "{}" }).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("INVALID_CREDENTIALS");
    expect(error.message).toBe("E-posta veya şifre hatalı.");
  });

  it("401 alınca token'ı yenileyip isteği tekrarlar", async () => {
    tokenStore.set({ access_token: "eski", refresh_token: "R1" });
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: "INVALID_TOKEN", message: "x" } }))
      .mockResolvedValueOnce(jsonResponse(200, { access_token: "yeni", refresh_token: "R2" }))
      .mockResolvedValueOnce(jsonResponse(200, { id: 1 }));

    await expect(apiFetch("/auth/me")).resolves.toEqual({ id: 1 });
    expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/auth/refresh");
    expect(new Headers(fetchMock.mock.calls[2][1]?.headers).get("Authorization")).toBe(
      "Bearer yeni",
    );
    expect(tokenStore.refresh).toBe("R2");
  });

  it("yenileme başarısızsa oturumu kapatır", async () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    tokenStore.set({ access_token: "eski", refresh_token: "R1" });
    fetchMock
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: "INVALID_TOKEN", message: "x" } }))
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: "INVALID_TOKEN", message: "x" } }));

    await expect(apiFetch("/auth/me")).rejects.toBeInstanceOf(ApiError);
    expect(handler).toHaveBeenCalledOnce();
    expect(tokenStore.access).toBeNull();
  });
});
