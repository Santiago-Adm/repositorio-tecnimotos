"use client";

import React, { useState } from "react";
import Link from "next/link";

interface OrdenTrabajo {
  id: string;
  codigo: string;
  vehiculo: string;
  placa: string;
  mecanico: string;
  estado: "Abierta" | "En Progreso" | "Espera Aprobación" | "Cerrada";
  monto: number;
  repuestos: string[];
}

const MOCK_OTS: OrdenTrabajo[] = [
  { id: "1", codigo: "OT-101", vehiculo: "TVS King Deluxe", placa: "1234-5A", mecanico: "Samuel Ramos (Master)", estado: "Abierta", monto: 120.00, repuestos: ["Filtro de aceite"] },
  { id: "2", codigo: "OT-102", vehiculo: "Bajaj Torito 2D", placa: "9876-2B", mecanico: "Lucho Huamán (Junior)", estado: "En Progreso", monto: 450.00, repuestos: ["Pistón con anillos", "Cable de embrague"] },
  { id: "3", codigo: "OT-103", vehiculo: "Bajaj Torito Chrome", placa: "4532-8C", mecanico: "Samuel Ramos (Master)", estado: "Espera Aprobación", monto: 650.00, repuestos: ["Kit de arrastre", "Pastillas de freno"] },
  { id: "4", codigo: "OT-099", vehiculo: "Pulsar 200 NS", placa: "XW-9021", mecanico: "Lucho Huamán (Junior)", estado: "Cerrada", monto: 320.00, repuestos: ["Amortiguador trasero"] },
];

export default function TallerPage() {
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>(MOCK_OTS);
  const [selectedOT, setSelectedOT] = useState<OrdenTrabajo | null>(null);
  const [nuevoRepuesto, setNuevoRepuesto] = useState("");

  const handleAddRepuesto = (otId: string) => {
    if (!nuevoRepuesto) return;
    setOrdenes(
      ordenes.map((ot) => {
        if (ot.id === otId) {
          return {
            ...ot,
            repuestos: [...ot.repuestos, nuevoRepuesto],
            monto: ot.monto + 80.00, // mock price addition
          };
        }
        return ot;
      })
    );
    setNuevoRepuesto("");
  };

  const handleCerrarOT = (otId: string) => {
    setOrdenes(
      ordenes.map((ot) => {
        if (ot.id === otId) {
          return { ...ot, estado: "Cerrada" };
        }
        return ot;
      })
    );
    alert("Órden de Trabajo cerrada. El descuento atómico de stock se ha procesado en la base de datos.");
  };

  const getColumna = (estado: OrdenTrabajo["estado"]) => {
    return ordenes.filter((ot) => ot.estado === estado);
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-white tracking-wide">Consola de Taller (Modo Taller)</span>
        </div>
        <div className="flex gap-4 items-center">
          <Link href="/stock" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
            Ver Stock
          </Link>
          <Link href="/" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
            Volver al Inicio
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        <div>
          <h2 className="text-3xl font-display font-bold text-white">Órdenes de Trabajo (OT)</h2>
          <p className="text-slate-400 text-sm mt-1">
            Asigna reparaciones, registra consumos y coordina cobros en tiempo real.
          </p>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Column Abierta */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>📂 Abiertas</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Abierta").length}</span>
            </h3>
            <div className="space-y-3">
              {getColumna("Abierta").map((ot) => (
                <div
                  key={ot.id}
                  onClick={() => setSelectedOT(ot)}
                  className="bg-slate-900 border border-slate-800 hover:border-teal-500/50 p-4 rounded-xl cursor-pointer transition-all space-y-3"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-xs font-bold text-teal-400">{ot.codigo}</span>
                    <span className="font-mono text-[10px] text-slate-500">{ot.placa}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200">{ot.vehiculo}</h4>
                  <p className="text-[11px] text-slate-400">Mecánico: {ot.mecanico.split(" ")[0]}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Column En Progreso */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>⚙️ En Progreso</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("En Progreso").length}</span>
            </h3>
            <div className="space-y-3">
              {getColumna("En Progreso").map((ot) => (
                <div
                  key={ot.id}
                  onClick={() => setSelectedOT(ot)}
                  className="bg-slate-900 border border-slate-800 hover:border-teal-500/50 p-4 rounded-xl cursor-pointer transition-all space-y-3"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-xs font-bold text-teal-400">{ot.codigo}</span>
                    <span className="font-mono text-[10px] text-slate-500">{ot.placa}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200">{ot.vehiculo}</h4>
                  <p className="text-[11px] text-slate-400">Mecánico: {ot.mecanico.split(" ")[0]}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Column Espera Aprobación */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>⚠️ Espera Aprobación</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Espera Aprobación").length}</span>
            </h3>
            <div className="space-y-3">
              {getColumna("Espera Aprobación").map((ot) => (
                <div
                  key={ot.id}
                  onClick={() => setSelectedOT(ot)}
                  className="bg-slate-900 border border-slate-800 hover:border-electric-500/50 p-4 rounded-xl cursor-pointer transition-all space-y-3 animate-pulse"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-xs font-bold text-electric-400">{ot.codigo}</span>
                    <span className="font-mono text-[10px] text-slate-500">{ot.placa}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200">{ot.vehiculo}</h4>
                  <p className="text-[11px] text-slate-400">Mecánico: {ot.mecanico.split(" ")[0]}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Column Cerrada */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>✅ Cerradas</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Cerrada").length}</span>
            </h3>
            <div className="space-y-3">
              {getColumna("Cerrada").map((ot) => (
                <div
                  key={ot.id}
                  onClick={() => setSelectedOT(ot)}
                  className="bg-slate-900/40 border border-slate-900 p-4 rounded-xl cursor-pointer opacity-70 hover:opacity-100 transition-all space-y-3"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-xs font-bold text-slate-500">{ot.codigo}</span>
                    <span className="font-mono text-[10px] text-slate-600">{ot.placa}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-400">{ot.vehiculo}</h4>
                  <p className="text-[11px] text-slate-500">Costo Final: S/ {ot.monto.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* OT Details modal/drawer split */}
        {selectedOT && (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col md:flex-row justify-between gap-6">
            <div className="flex-1 space-y-4">
              <div className="flex justify-between items-center border-b border-slate-800 pb-3">
                <h3 className="font-display font-bold text-lg text-white">Detalle de la Orden: {selectedOT.codigo}</h3>
                <button onClick={() => setSelectedOT(null)} className="text-slate-400 hover:text-white">
                  Cerrar panel
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <p><span className="text-slate-400">Vehículo:</span> <span className="font-semibold text-slate-200">{selectedOT.vehiculo}</span></p>
                <p><span className="text-slate-400">Placa:</span> <span className="font-mono text-slate-200">{selectedOT.placa}</span></p>
                <p><span className="text-slate-400">Mecánico:</span> <span className="font-semibold text-slate-200">{selectedOT.mecanico}</span></p>
                <p><span className="text-slate-400">Estado:</span> <span className="font-semibold text-teal-400">{selectedOT.estado}</span></p>
              </div>

              <div className="space-y-2">
                <h4 className="font-display font-bold text-sm text-slate-200">Repuestos Consumidos</h4>
                {selectedOT.repuestos.length > 0 ? (
                  <ul className="list-disc list-inside text-xs text-slate-400 pl-2">
                    {selectedOT.repuestos.map((rep, idx) => (
                      <li key={idx} className="font-semibold">{rep}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500">Ningún repuesto cargado en la OT.</p>
                )}
              </div>
            </div>

            <div className="w-full md:w-80 bg-slate-950 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
              <div className="space-y-4">
                <h4 className="font-display font-bold text-sm text-slate-200">Acciones sobre OT</h4>
                
                {selectedOT.estado !== "Cerrada" && (
                  <div className="space-y-3">
                    <div>
                      <input
                        type="text"
                        placeholder="Ej. Pastillas de freno"
                        className="w-full px-3 py-2 rounded-xl border border-slate-850 focus:outline-none focus:border-teal-500 text-xs bg-slate-900 text-white"
                        value={nuevoRepuesto}
                        onChange={(e) => setNuevoRepuesto(e.target.value)}
                      />
                    </div>
                    <button
                      onClick={() => handleAddRepuesto(selectedOT.id)}
                      className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium py-2 rounded-xl text-xs transition-colors"
                    >
                      + Cargar Repuesto
                    </button>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-800/80 mt-4 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block">Costo Estimado</span>
                  <span className="font-mono text-base font-bold text-white">S/ {selectedOT.monto.toFixed(2)}</span>
                </div>
                {selectedOT.estado !== "Cerrada" && (
                  <button
                    onClick={() => handleCerrarOT(selectedOT.id)}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2 rounded-xl text-xs transition-colors"
                  >
                    Cerrar Orden
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
