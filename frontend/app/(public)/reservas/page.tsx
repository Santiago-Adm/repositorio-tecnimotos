"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

// Form Component that uses search params
function ReservaForm() {
  const searchParams = useSearchParams();
  const initialCodigo = searchParams.get("codigo") || "";

  const [codigo, setCodigo] = useState(initialCodigo);
  const [segmento, setSegmento] = useState<"S1" | "S2" | "S4">("S1");
  const [cantidad, setCantidad] = useState(1);
  const [clienteNombre, setClienteNombre] = useState("");
  const [clienteDoc, setClienteDoc] = useState("");
  const [loading, setLoading] = useState(false);
  const [reservaConfirmada, setReservaConfirmada] = useState<{
    id: string;
    codigo_reserva: string;
    expira_en: string;
    ttl_horas: number;
  } | null>(null);

  useEffect(() => {
    if (initialCodigo) {
      setCodigo(initialCodigo);
    }
  }, [initialCodigo]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!codigo || !clienteNombre || !clienteDoc) return;

    setLoading(true);
    // Mock API delay
    setTimeout(() => {
      const ttlMap = { S1: 24, S2: 48, S4: 72 };
      const hours = ttlMap[segmento];
      const expiry = new Date();
      expiry.setHours(expiry.getHours() + hours);

      setReservaConfirmada({
        id: Math.random().toString(36).substring(7).toUpperCase(),
        codigo_reserva: `RES-${codigo}-${Math.floor(100 + Math.random() * 900)}`,
        expira_en: expiry.toLocaleString("es-PE", { hour12: false }),
        ttl_horas: hours,
      });
      setLoading(false);
    }, 800);
  };

  const getTtlInfo = () => {
    switch (segmento) {
      case "S1":
        return "24 horas (Conductor individual)";
      case "S2":
        return "48 horas (Mecánico de distrito)";
      case "S4":
        return "72 horas (Cliente rural / conectividad baja)";
      default:
        return "24 horas";
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left side form */}
      <div className="lg:col-span-2 bg-white p-6 md:p-8 rounded-3xl border border-slate-200 shadow-sm flex flex-col justify-between">
        {!reservaConfirmada ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <h3 className="text-xl font-display font-bold text-slate-900 border-b border-slate-100 pb-3">
              Datos del Apartado / Reserva
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Código de Repuesto
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. RP-001"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800 font-mono"
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Cantidad
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800"
                  value={cantidad}
                  onChange={(e) => setCantidad(parseInt(e.target.value) || 1)}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Nombre Completo
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Juan Pérez"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800"
                  value={clienteNombre}
                  onChange={(e) => setClienteNombre(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  DNI / RUC del Cliente
                </label>
                <input
                  type="text"
                  required
                  placeholder="Nro documento"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800"
                  value={clienteDoc}
                  onChange={(e) => setClienteDoc(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Segmento / Tipo de Cliente (Establece el TTL)
              </label>
              <div className="grid grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setSegmento("S1")}
                  className={`py-3 px-4 rounded-xl border text-xs font-medium transition-all ${
                    segmento === "S1"
                      ? "border-teal-500 bg-teal-50 text-teal-800"
                      : "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600"
                  }`}
                >
                  🚙 Conductor (S1)
                </button>
                <button
                  type="button"
                  onClick={() => setSegmento("S2")}
                  className={`py-3 px-4 rounded-xl border text-xs font-medium transition-all ${
                    segmento === "S2"
                      ? "border-teal-500 bg-teal-50 text-teal-800"
                      : "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600"
                  }`}
                >
                  🏬 Distrito (S2)
                </button>
                <button
                  type="button"
                  onClick={() => setSegmento("S4")}
                  className={`py-3 px-4 rounded-xl border text-xs font-medium transition-all ${
                    segmento === "S4"
                      ? "border-teal-500 bg-teal-50 text-teal-800"
                      : "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-600"
                  }`}
                >
                  🏡 Rural (S4)
                </button>
              </div>
              <p className="text-xs text-teal-600 mt-2 font-medium">
                Vigencia de la reserva: {getTtlInfo()}
              </p>
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-teal-500/10 text-sm flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                    Confirmando Reserva...
                  </>
                ) : (
                  "Confirmar y Separar Repuesto"
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-6 text-center py-8">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-3xl">
              ✓
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-display font-bold text-slate-900">
                ¡Reserva Creada Exitosamente!
              </h3>
              <p className="text-slate-500 text-sm max-w-md mx-auto">
                Se ha apartado el stock del repuesto. Guarda el código generado para realizar la recolección en tienda.
              </p>
            </div>

            {/* Voucher Card */}
            <div className="max-w-md mx-auto bg-slate-50 border border-slate-200 rounded-2xl p-6 text-left space-y-4 shadow-inner">
              <div className="flex justify-between items-center pb-3 border-b border-slate-200">
                <span className="text-xs uppercase font-semibold text-slate-400">Código de Reserva</span>
                <span className="font-mono text-sm font-bold text-teal-600">{reservaConfirmada.codigo_reserva}</span>
              </div>
              <div className="space-y-2 text-xs text-slate-600">
                <p>Repuesto: <span className="font-mono font-semibold text-slate-800">{codigo}</span></p>
                <p>Cantidad: <span className="font-semibold text-slate-800">{cantidad} unid.</span></p>
                <p>Cliente: <span className="font-semibold text-slate-800">{clienteNombre} ({clienteDoc})</span></p>
                <p>Segmento: <span className="font-semibold text-slate-800">S{segmento === "S1" ? "1 - Conductor" : segmento === "S2" ? "2 - Distrito" : "4 - Rural"}</span></p>
                <p>Tiempo de Reserva (TTL): <span className="font-semibold text-slate-800">{reservaConfirmada.ttl_horas} horas</span></p>
              </div>
              <div className="pt-3 border-t border-slate-200 text-center">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Expira el</p>
                <p className="font-mono text-sm font-bold text-red-600 mt-1">{reservaConfirmada.expira_en}</p>
              </div>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => setReservaConfirmada(null)}
                className="px-5 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors text-xs font-semibold text-slate-600"
              >
                Nueva Reserva
              </button>
              <Link
                href="/catalogo"
                className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white transition-colors text-xs font-semibold"
              >
                Volver al Catálogo
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Right side info bar */}
      <div className="space-y-6">
        <div className="bg-slate-50 border border-slate-200 rounded-3xl p-6 space-y-4">
          <h4 className="font-display font-bold text-slate-900 text-base">Políticas de Reserva (TTL)</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Las reservas bloquean stock de forma temporal para evitar viajes fallidos. El límite de tiempo (Time to Live) se calcula según tu perfil de cliente:
          </p>
          <div className="space-y-3 pt-2 text-xs">
            <div className="p-3 bg-white border border-slate-100 rounded-xl">
              <p className="font-semibold text-slate-800">🚙 Conductor Individual (S1)</p>
              <p className="text-[10px] text-slate-500 mt-0.5">TTL: 24 horas de vigencia de reserva.</p>
            </div>
            <div className="p-3 bg-white border border-slate-100 rounded-xl">
              <p className="font-semibold text-slate-800">🏬 Mecánico de Distrito (S2)</p>
              <p className="text-[10px] text-slate-500 mt-0.5">TTL: 48 horas de vigencia de reserva para consolidación.</p>
            </div>
            <div className="p-3 bg-white border border-slate-100 rounded-xl">
              <p className="font-semibold text-slate-800">🏡 Cliente Rural (S4)</p>
              <p className="text-[10px] text-slate-500 mt-0.5">TTL: 72 horas para tolerancia de tiempos de viaje largos.</p>
            </div>
          </div>
        </div>

        <div className="bg-teal-50 border border-teal-100 rounded-3xl p-6">
          <h4 className="font-display font-bold text-teal-900 text-sm">💡 ¿Sabías qué?</h4>
          <p className="text-xs text-teal-800 mt-2 leading-relaxed">
            El sistema liberará automáticamente las piezas apartadas al expirar el TTL, poniéndolas nuevamente en venta para otros conductores.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ReservasPage() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Header navbar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <a href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </a>
          <span className="font-display font-bold text-slate-900">Reservas Express</span>
        </div>
        <a href="/" className="text-sm text-slate-500 hover:text-teal-600 transition-colors">
          Volver al Inicio
        </a>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <Suspense fallback={<div className="text-center py-12 text-slate-500 text-sm">Cargando formulario...</div>}>
          <ReservaForm />
        </Suspense>
      </main>
    </div>
  );
}
