"use client";

import React, { useState } from "react";
import Link from "next/link";

interface Comprobante {
  id: string;
  codigo: string;
  tipo: "Boleta" | "Factura" | "Ticket";
  monto: number;
  cliente: string;
  doc_cliente: string;
  creado_por: string;
  estado: "Pendiente Validación" | "Emitido" | "Anulado (N/C)";
  fecha: string;
}

const MOCK_COMPROBANTES: Comprobante[] = [
  { id: "1", codigo: "BV-0012", tipo: "Boleta", monto: 150.00, cliente: "Juan Pérez", doc_cliente: "10293847", creado_por: "María Gómez (Vendedor)", estado: "Pendiente Validación", fecha: "2026-06-21 15:45" },
  { id: "2", codigo: "FT-0045", tipo: "Factura", monto: 320.00, cliente: "Distribuidora Ayacucho", doc_cliente: "20104938210", creado_por: "Samuel Ramos (Admin)", estado: "Emitido", fecha: "2026-06-21 12:30" },
  { id: "3", codigo: "TK-0891", tipo: "Ticket", monto: 15.50, cliente: "Pasajero Express", doc_cliente: "09283746", creado_por: "María Gómez (Vendedor)", estado: "Emitido", fecha: "2026-06-21 10:15" },
];

export default function FacturacionPage() {
  const [comprobantes, setComprobantes] = useState<Comprobante[]>(MOCK_COMPROBANTES);

  // New billing states
  const [nuevoMonto, setNuevoMonto] = useState(0);
  const [nuevoDoc, setNuevoDoc] = useState("");
  const [nuevoCliente, setNuevoCliente] = useState("");

  const handleValidar = (id: string) => {
    setComprobantes(
      comprobantes.map((c) => {
        if (c.id === id) {
          return { ...c, estado: "Emitido" };
        }
        return c;
      })
    );
    alert("Comprobante aprobado y emitido ante SUNAT (Simulado).");
  };

  const handleAnular = (id: string) => {
    setComprobantes(
      comprobantes.map((c) => {
        if (c.id === id) {
          return { ...c, estado: "Anulado (N/C)" };
        }
        return c;
      })
    );
    alert("Nota de Crédito generada. El comprobante original ha sido anulado.");
  };

  const handleEmitir = (e: React.FormEvent) => {
    e.preventDefault();
    if (nuevoMonto <= 0 || !nuevoCliente) return;

    let tipo: Comprobante["tipo"] = "Ticket";
    if (nuevoMonto > 60) {
      if (nuevoDoc.length !== 11) {
        alert("Para montos mayores a S/ 60 se requiere Factura con RUC de 11 dígitos.");
        return;
      }
      tipo = "Factura";
    } else if (nuevoMonto > 20) {
      tipo = "Boleta";
    }

    const nuevo: Comprobante = {
      id: Math.random().toString(),
      codigo: `${tipo === "Boleta" ? "BV" : tipo === "Factura" ? "FT" : "TK"}-${Math.floor(1000 + Math.random() * 9000)}`,
      tipo,
      monto: nuevoMonto,
      cliente: nuevoCliente,
      doc_cliente: nuevoDoc,
      creado_por: "María Gómez (Vendedor)",
      estado: "Pendiente Validación", // default for Vendedor
      fecha: new Date().toLocaleString("es-PE", { hour12: false }),
    };

    setComprobantes([nuevo, ...comprobantes]);
    setNuevoMonto(0);
    setNuevoDoc("");
    setNuevoCliente("");
    alert(`Comprobante creado en estado PENDIENTE VALIDACIÓN (Rol Vendedor).`);
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-white tracking-wide">Validación y Facturación (SANTI)</span>
        </div>
        <Link href="/" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
          Volver al Inicio
        </Link>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-8 max-w-7xl mx-auto w-full">
        <div>
          <h2 className="text-3xl font-display font-bold text-white">Facturación Electrónica</h2>
          <p className="text-slate-400 text-sm mt-1">
            Revisión y emisión de comprobantes autorizados ante SUNAT según topes de ley.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 shadow-sm">
              <h3 className="font-display font-bold text-base text-white">Comprobantes Recientes</h3>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left">
                  <thead>
                    <tr className="border-b border-slate-800 text-xs font-bold text-slate-500 uppercase tracking-wider">
                      <th className="py-3 px-4">Código / Tipo</th>
                      <th className="py-3 px-4">Cliente / Doc</th>
                      <th className="py-3 px-4 text-right">Monto</th>
                      <th className="py-3 px-4 text-center">Estado</th>
                      <th className="py-3 px-4 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {comprobantes.map((comp) => {
                      return (
                        <tr key={comp.id} className="hover:bg-slate-900/40">
                          <td className="py-4 px-4 font-mono">
                            <p className="font-bold text-slate-300">{comp.codigo}</p>
                            <p className="text-[10px] text-slate-500 uppercase">{comp.tipo}</p>
                          </td>
                          <td className="py-4 px-4">
                            <p className="font-semibold text-slate-200">{comp.cliente}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{comp.doc_cliente}</p>
                          </td>
                          <td className="py-4 px-4 text-right font-mono font-semibold text-slate-100">
                            S/ {comp.monto.toFixed(2)}
                          </td>
                          <td className="py-4 px-4 text-center">
                            <span
                              className={`inline-block px-2.5 py-0.5 rounded-full text-[11px] font-medium ${
                                comp.estado === "Pendiente Validación"
                                  ? "bg-amber-950 text-amber-400 border border-amber-900/50"
                                  : comp.estado === "Emitido"
                                  ? "bg-emerald-950 text-emerald-400 border border-emerald-900/50"
                                  : "bg-red-950 text-red-400 border border-red-900/50"
                              }`}
                            >
                              {comp.estado}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-right space-x-2">
                            {comp.estado === "Pendiente Validación" && (
                              <button
                                onClick={() => handleValidar(comp.id)}
                                className="bg-teal-600 hover:bg-teal-700 text-white font-medium px-2.5 py-1.5 rounded-lg text-xs transition-colors"
                              >
                                Validar
                              </button>
                            )}
                            {comp.estado === "Emitido" && (
                              <button
                                onClick={() => handleAnular(comp.id)}
                                className="bg-slate-800 hover:bg-slate-700 text-red-400 hover:text-red-300 font-medium px-2.5 py-1.5 rounded-lg text-xs transition-colors border border-slate-700"
                              >
                                Anular (N/C)
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Issue New document (Simulated Vendedor input) */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 shadow-sm">
              <h3 className="font-display font-bold text-white text-base">Registrar Venta Directa</h3>

              <form onSubmit={handleEmitir} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-500 uppercase tracking-wider mb-2 font-semibold">
                    Nombre del Cliente
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ej. Pedro Aguilar"
                    className="w-full px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                    value={nuevoCliente}
                    onChange={(e) => setNuevoCliente(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-slate-500 uppercase tracking-wider mb-2 font-semibold">
                    Documento Identidad (DNI / RUC)
                  </label>
                  <input
                    type="text"
                    placeholder="8 u 11 dígitos"
                    className="w-full px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                    value={nuevoDoc}
                    onChange={(e) => setNuevoDoc(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-slate-500 uppercase tracking-wider mb-2 font-semibold">
                    Monto Total Venta
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    step="0.1"
                    className="w-full px-3 py-2 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white font-mono"
                    value={nuevoMonto || ""}
                    onChange={(e) => setNuevoMonto(parseFloat(e.target.value) || 0)}
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full bg-electric-600 hover:bg-electric-700 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-electric-500/10 text-sm"
                  >
                    Generar Registro (Pendiente)
                  </button>
                </div>
              </form>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-3">
              <h4 className="font-display font-bold text-white text-sm">Normativa y Límites (SUNAT)</h4>
              <ul className="text-xs text-slate-400 space-y-2 list-disc list-inside">
                <li>Boleta obligatoria para montos superiores a <span className="font-semibold text-slate-200">S/ 20</span>.</li>
                <li>Factura con RUC obligatoria para montos superiores a <span className="font-semibold text-slate-200">S/ 60</span>.</li>
                <li>Un comprobante emitido no se puede eliminar de la base de datos; solo se puede anular vía una Nota de Crédito vinculada.</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
