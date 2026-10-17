import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../api/auth";
import { setUnauthorizedHandler, tokenStore } from "../api/client";
import { AuthContext, type AuthContextValue } from "./useAuth";

const ME_KEY = ["auth", "me"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = useState(() => tokenStore.access !== null);

  const meQuery = useQuery({
    queryKey: ME_KEY,
    queryFn: authApi.getMe,
    enabled: hasToken,
    retry: false,
    staleTime: Infinity,
  });

  const signOutLocally = useCallback(() => {
    tokenStore.clear();
    queryClient.clear();
    setHasToken(false);
  }, [queryClient]);

  useEffect(() => {
    setUnauthorizedHandler(signOutLocally);
  }, [signOutLocally]);

  const login = useCallback(
    async (email: string, password: string) => {
      tokenStore.set(await authApi.login(email, password));
      const me = await authApi.getMe();
      queryClient.setQueryData(ME_KEY, me);
      setHasToken(true);
      return me;
    },
    [queryClient],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Sunucuya ulaşılamasa da yerel oturum kapatılır.
    } finally {
      signOutLocally();
    }
  }, [signOutLocally]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: hasToken ? (meQuery.data ?? null) : null,
      isLoading: hasToken && meQuery.isPending,
      login,
      logout,
    }),
    [hasToken, meQuery.data, meQuery.isPending, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
