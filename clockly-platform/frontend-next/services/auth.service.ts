import { api } from "@/lib/api-client";
import { clearAuthTokens, getRefreshToken, saveAuthTokens } from "@/lib/api-client";
import type { AuthPayload, LoginRequest, MePayload } from "@/types/auth";

export const authService = {
  login: async (payload: LoginRequest) => {
    const session = await api.post<AuthPayload>("/auth/login", {
      identifier: payload.identifier,
      password: payload.password,
    });
    saveAuthTokens(session.access_token, session.refresh_token);
    return session;
  },

  logout: async () => {
    clearAuthTokens();
    return { ok: true };
  },

  me: () => api.get<MePayload>("/auth/me"),

  refresh: async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) throw new Error("No refresh token available");
    const session = await api.post<AuthPayload>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    saveAuthTokens(session.access_token, session.refresh_token);
    return session;
  },
};
