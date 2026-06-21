"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export interface User {
  id: string;
  rol: string;
  token_version: number;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  mfaSessionToken: string | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<{ status: "MFA_REQUIRED" | "SUCCESS" | "ERROR"; mfaToken?: string; error?: string }>;
  verifyMfa: (mfaToken: string, code: string) => Promise<{ status: "SUCCESS" | "ERROR"; error?: string }>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// zero-dependency helper to decode JWT claims in browser
function parseJwt(token: string): { sub: string; rol: string; token_version: number } | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [mfaSessionToken, setMfaSessionToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Attempt to silently refresh token on mount
  useEffect(() => {
    async function silentRefresh() {
      try {
        const res = await fetch("/api-proxy/v1/auth/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (res.ok) {
          const body = await res.json();
          const token = body.data?.access_token;
          if (token) {
            setAccessToken(token);
            const claims = parseJwt(token);
            if (claims) {
              setUser({
                id: claims.sub,
                rol: claims.rol,
                token_version: claims.token_version,
              });
            }
          }
        }
      } catch (err) {
        console.error("Silent refresh failed:", err);
      } finally {
        setLoading(false);
      }
    }
    silentRefresh();
  }, []);

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      const res = await fetch("/api-proxy/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const body = await res.json();

      if (!res.ok) {
        const errMsg = body.detail?.message || "Error al iniciar sesión";
        setError(errMsg);
        return { status: "ERROR" as const, error: errMsg };
      }

      const mfaToken = body.data?.mfa_session_token;
      if (mfaToken) {
        setMfaSessionToken(mfaToken);
        return { status: "MFA_REQUIRED" as const, mfaToken };
      }

      return { status: "ERROR" as const, error: "Respuesta de login inesperada" };
    } catch {
      const errMsg = "Error de red al conectar con el servidor";
      setError(errMsg);
      return { status: "ERROR" as const, error: errMsg };
    }
  };

  const verifyMfa = async (mfaToken: string, code: string) => {
    setError(null);
    try {
      const res = await fetch("/api-proxy/v1/auth/mfa", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mfa_session_token: mfaToken,
          totp_code: code,
        }),
      });

      const body = await res.json();

      if (!res.ok) {
        const errMsg = body.detail?.message || "Código MFA incorrecto";
        setError(errMsg);
        return { status: "ERROR" as const, error: errMsg };
      }

      const token = body.data?.access_token;
      if (token) {
        setAccessToken(token);
        const claims = parseJwt(token);
        if (claims) {
          setUser({
            id: claims.sub,
            rol: claims.rol,
            token_version: claims.token_version,
          });
        }
        setMfaSessionToken(null);
        return { status: "SUCCESS" as const };
      }

      return { status: "ERROR" as const, error: "No se recibió el token de acceso" };
    } catch {
      const errMsg = "Error de red al verificar el MFA";
      setError(errMsg);
      return { status: "ERROR" as const, error: errMsg };
    }
  };

  const logout = async () => {
    try {
      await fetch("/api-proxy/v1/auth/logout", {
        method: "POST",
      });
    } catch (err) {
      console.error("Logout request failed:", err);
    } finally {
      setAccessToken(null);
      setUser(null);
      setMfaSessionToken(null);
      setError(null);
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        mfaSessionToken,
        loading,
        error,
        login,
        verifyMfa,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
