"use client";

import React, { useState } from "react";
import Link from "next/link";

interface SesionUsuario {
  id: string;
  usuario: string;
  rol: string;
  ip: string;
  mfa_completado: boolean;
  token_version: number;
  expiracion: string;
}

const MOCK_SESIONES: SesionUsuario[] = [
  { id: "S-101", usuario: "samuel.admin@tecnimotos.com", rol: "ADMINISTRADOR", ip: "192.168.1.15", mfa_completado: true, token_version: 3, expiracion: "2026-06-22 16:00" },
  { id: "S-102", usuario: "maria.vendedor@tecnimotos.com", rol: "VENDEDOR", ip: "192.168.1.18", mfa_completado: false, token_version: 1, expiracion: "2026-06-21 20:00" },
  { id: "S-103", usuario: "lucho.mecanico@tecnimotos.com", rol: "MECANICO_MASTER", ip: "192.168.1.20", mfa_completado: false, token_version: 2, expiracion: "2026-06-21 22:30" },
];

const MOCK_LOGS = [
  { timestamp: "2026-06-21T16:10:05Z", level: "INFO", category: "Auth", message: "Sesión iniciada por usuario samuel.admin@tecnimotos.com", detail: { mfa_method: "TOTP", ip: "192.168.1.15" } },
  { timestamp: "2026-06-21T16:15:30Z", level: "WARN", category: "Security", message: "Intento de acceso a endpoint administrativo sin MFA por mecánico", detail: { endpoint: "/v1/admin/usuarios", ip: "192.168.1.20" } },
  { timestamp: "2026-06-21T16:20:45Z", level: "INFO", category: "Audit", message: "Precio de repuesto RP-001 actualizado manualmente", detail: { modificado_por: "Samuel Ramos", anterior: 140.00, nuevo: 150.00 } },
];

export default function AdminPage() {
  const [sesiones, setSesiones] = useState<SesionUsuario[]>(MOCK_SESIONES);

  const handleRevocarSesion = (id: string) => {
    setSesiones(
      sesiones.map((s) => {
        if (s.id === id) {
          return { ...s, token_version: s.token_version + 1 };
        }
        return s;
      })
    );
    alert("Sesión revocada e incrementada versión de token de usuario. Cualquier token anterior es inválido de inmediato.");
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-white tracking-wide">Consola de Administración (SANTI)</span>
        </div>
        <Link href="/" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
          Volver al Inicio
        </Link>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-8 max-w-7xl mx-auto w-full">
        <div>
          <h2 className="text-3xl font-display font-bold text-white">Panel Técnico Administrativo</h2>
          <p className="text-slate-400 text-sm mt-1">
            Control global de seguridad, sesiones activas, auditoría de logs y scans estáticos del sistema.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Active Sessions list */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 shadow-sm">
              <h3 className="font-display font-bold text-base text-white">Sesiones Activas y Control de Tokens</h3>
              
              <div className="space-y-4">
                {sesiones.map((s) => (
                  <div key={s.id} className="p-4 bg-slate-950 border border-slate-850 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="space-y-1">
                      <p className="font-semibold text-slate-200 text-sm">{s.usuario}</p>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span className="font-mono bg-slate-900 px-1.5 py-0.5 rounded text-[10px] text-slate-400">{s.rol}</span>
                        <span>• IP: {s.ip}</span>
                        <span>• Token Ver: {s.token_version}</span>
                      </div>
                      <div className="pt-1 flex gap-2">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          s.mfa_completado ? "bg-emerald-950 text-emerald-400 border border-emerald-900/30" : "bg-amber-950 text-amber-400 border border-amber-900/30"
                        }`}>
                          {s.mfa_completado ? "MFA Completado" : "Sin MFA"}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRevocarSesion(s.id)}
                      className="bg-red-950/60 hover:bg-red-900/40 text-red-400 hover:text-red-300 font-semibold px-3 py-2 rounded-xl text-xs border border-red-900/30 transition-colors"
                    >
                      Revocar Sesión
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Audit Logs structured */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-sm">
              <h3 className="font-display font-bold text-base text-white">Logs de Auditoría (JSON)</h3>
              <p className="text-xs text-slate-400">Salida de logs estructurados en tiempo real (RNT-06):</p>
              
              <div className="bg-slate-950 border border-slate-850 p-4 rounded-2xl font-mono text-xs text-slate-300 space-y-2 overflow-x-auto">
                {MOCK_LOGS.map((log, idx) => (
                  <pre key={idx} className="whitespace-pre-wrap leading-relaxed py-1 border-b border-slate-900 last:border-0">
                    {JSON.stringify(log, null, 2)}
                  </pre>
                ))}
              </div>
            </div>
          </div>

          {/* Security Scanners Static Reports */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-sm">
              <h3 className="font-display font-bold text-white text-base">Estatus de Seguridad</h3>
              
              <div className="space-y-4 text-xs">
                <div className="p-3 bg-slate-950 border border-slate-850 rounded-xl space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">🔍 SAST (Bandit)</span>
                    <span className="font-semibold text-emerald-400">0 Hallazgos Critical</span>
                  </div>
                  <p className="text-[10px] text-slate-500">Última ejecución: Hoy 16:00 Z</p>
                </div>

                <div className="p-3 bg-slate-950 border border-slate-850 rounded-xl space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">🔑 Secrets (Gitleaks)</span>
                    <span className="font-semibold text-emerald-400">0 Hallazgos</span>
                  </div>
                  <p className="text-[10px] text-slate-500">Repositorio limpio de credenciales.</p>
                </div>

                <div className="p-3 bg-slate-950 border border-slate-850 rounded-xl space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">🐳 Contenedores (Trivy)</span>
                    <span className="font-semibold text-emerald-400">0 Hallazgos Critical</span>
                  </div>
                  <p className="text-[10px] text-slate-500">Verificaciones de Dockerfiles aprobadas.</p>
                </div>
              </div>
            </div>

            <div className="bg-teal-950/20 border border-teal-900/30 rounded-3xl p-6">
              <h4 className="font-display font-bold text-teal-300 text-sm">💡 MFA Obligatorio</h4>
              <p className="text-xs text-teal-400/90 mt-2 leading-relaxed">
                Según la directiva de seguridad RNT-02, el uso de MFA de tipo TOTP es obligatorio para los roles de SUPERADMIN y ADMINISTRADOR.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
