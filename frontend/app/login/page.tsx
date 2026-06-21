"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/src/context/AuthContext";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const { login, verifyMfa, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"credentials" | "mfa">("credentials");

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);
    clearError();

    const res = await login(email, password);
    setLoading(false);

    if (res.status === "MFA_REQUIRED" && res.mfaToken) {
      setMfaToken(res.mfaToken);
      setStep("mfa");
    } else if (res.status === "SUCCESS") {
      // Direct login (if backend bypassed MFA, though EP-AUTH-01 always returns mfa_session_token)
      router.push("/");
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaToken || !totpCode) return;

    setLoading(true);
    clearError();

    const res = await verifyMfa(mfaToken, totpCode);
    setLoading(false);

    if (res.status === "SUCCESS") {
      // Decode user role or fetch state to decide route
      // Let's reload or push to root page which will redirect or show portals
      router.push("/");
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-center items-center px-6 relative overflow-hidden font-body">
      {/* Decorative background gradients */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-electric-500/10 rounded-full blur-3xl -z-10"></div>

      <div className="max-w-md w-full bg-slate-950/80 border border-slate-800 backdrop-blur-lg rounded-3xl p-8 shadow-2xl space-y-8">
        {/* Brand */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-teal-600 to-electric-500 flex items-center justify-center text-white font-display font-bold text-2xl shadow-lg shadow-teal-500/20 mx-auto">
            S
          </div>
          <h2 className="font-display font-extrabold text-2xl tracking-tight text-white mt-4">
            {step === "credentials" ? "Iniciar Sesión" : "Autenticación MFA"}
          </h2>
          <p className="text-slate-400 text-xs">
            {step === "credentials" 
              ? "Ingresa tus credenciales para acceder a la plataforma SANTI" 
              : "Ingresa el código de 6 dígitos enviado a tu dispositivo"}
          </p>
        </div>

        {error && (
          <div className="bg-red-950/60 border border-red-900/50 text-red-400 p-4 rounded-2xl text-xs font-semibold">
            {error}
          </div>
        )}

        {step === "credentials" ? (
          <form onSubmit={handleCredentialsSubmit} className="space-y-6">
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Correo Electrónico
                </label>
                <input
                  type="email"
                  required
                  placeholder="ejemplo@tecnimotos.test"
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-900 text-white font-body"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Contraseña
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-900 text-white"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-teal-500/10 text-sm flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                  Autenticando...
                </>
              ) : (
                "Ingresar"
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleMfaSubmit} className="space-y-6">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Código de Verificación TOTP
              </label>
              <input
                type="text"
                required
                maxLength={6}
                pattern="^[0-9]{6}$"
                placeholder="000000"
                className="w-full px-4 py-3 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-center tracking-widest text-lg font-mono bg-slate-900 text-white"
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
              />
              <p className="text-[10px] text-slate-500 mt-2 text-center">
                (En el entorno de desarrollo, cualquier código de 6 dígitos numéricos será válido)
              </p>
            </div>

            <div className="space-y-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-electric-600 hover:bg-electric-700 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-electric-500/10 text-sm flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                    Verificando...
                  </>
                ) : (
                  "Verificar Código"
                )}
              </button>

              <button
                type="button"
                className="w-full bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium py-3 rounded-xl transition-colors text-sm"
                onClick={() => {
                  setStep("credentials");
                  setTotpCode("");
                }}
              >
                Volver
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="mt-8">
        <Link href="/" className="text-xs text-slate-500 hover:text-teal-500 transition-colors">
          ← Volver al Portal de Inicio
        </Link>
      </div>
    </div>
  );
}
