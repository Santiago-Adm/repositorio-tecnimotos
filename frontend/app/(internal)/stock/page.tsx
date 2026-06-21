"use client";

import React, { useState } from "react";
import Link from "next/link";

interface StockItem {
  id: string;
  codigo: string;
  nombre: string;
  modelo: string;
  cantidad: number;
  apartados: number;
  transito: number;
  umbral: number;
}

const MOCK_STOCK: StockItem[] = [
  { id: "1", codigo: "RP-001", nombre: "Pistón con anillos TVS", modelo: "TVS King", cantidad: 12, apartados: 2, transito: 0, umbral: 10 },
  { id: "2", codigo: "RP-002", nombre: "Filtro de aceite original", modelo: "Bajaj Torito", cantidad: 40, apartados: 5, transito: 20, umbral: 15 },
  { id: "3", codigo: "RP-003", nombre: "Amortiguador trasero Pulsar", modelo: "Pulsar 200 NS", cantidad: 2, apartados: 1, transito: 5, umbral: 5 }, // Alert
  { id: "4", codigo: "RP-004", nombre: "Pastillas de freno RE", modelo: "Torito RE", cantidad: 25, apartados: 0, transito: 0, umbral: 10 },
  { id: "5", codigo: "RP-005", nombre: "Cable de embrague reforzado", modelo: "Bajaj Torito Chrome", cantidad: 15, apartados: 3, transito: 0, umbral: 5 },
];

const MOCK_MOVIMIENTOS = [
  { id: "M-301", codigo: "RP-002", tipo: "Entrada (Reabastecimiento)", cantidad: 20, fecha: "2026-06-21 08:30", actor: "Samuel Ramos" },
  { id: "M-302", codigo: "RP-001", tipo: "Salida (OT-101)", cantidad: -1, fecha: "2026-06-21 11:15", actor: "Lucho Huamán" },
  { id: "M-303", codigo: "RP-005", tipo: "Apartado (Reserva S1)", cantidad: -1, fecha: "2026-06-21 14:00", actor: "Sistema (Público)" },
];

export default function StockPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [stock, setStock] = useState<StockItem[]>(MOCK_STOCK);

  const alertsCount = stock.filter((item) => item.cantidad < item.umbral).length;

  const handleReabastecer = (id: string) => {
    setStock(
      stock.map((item) => {
        if (item.id === id) {
          return { ...item, cantidad: item.cantidad + 15 };
        }
        return item;
      })
    );
    alert("Reabastecimiento mock enviado. Se han sumado 15 unidades al stock.");
  };

  const filteredStock = stock.filter((item) =>
    item.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.codigo.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-white tracking-wide">Gestión de Inventario (SANTI)</span>
        </div>
        <div className="flex gap-4 items-center">
          <Link href="/taller" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
            Ver Taller (OT)
          </Link>
          <Link href="/" className="text-xs text-slate-400 hover:text-teal-400 transition-colors">
            Volver al Inicio
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-8 max-w-7xl mx-auto w-full">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-display font-bold text-white">Stock y Movimientos</h2>
            <p className="text-slate-400 text-sm mt-1">
              Registro de existencias físicas, apartados y transacciones Kardex en el taller.
            </p>
          </div>

          {alertsCount > 0 && (
            <div className="bg-red-950/60 border border-red-900/50 text-red-400 px-4 py-2 rounded-2xl text-xs font-semibold flex items-center gap-2 animate-bounce">
              <span>⚠️</span>
              Hay {alertsCount} repuesto(s) bajo el umbral mínimo
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main stock list */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 shadow-sm">
              <div className="flex justify-between items-center gap-4">
                <input
                  type="text"
                  placeholder="Buscar por código o nombre..."
                  className="flex-1 px-4 py-2 rounded-xl border border-slate-850 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-left">
                  <thead>
                    <tr className="border-b border-slate-800 text-xs font-bold text-slate-500 uppercase tracking-wider">
                      <th className="py-3 px-4">Código</th>
                      <th className="py-3 px-4">Repuesto</th>
                      <th className="py-3 px-4 text-center">Disponible</th>
                      <th className="py-3 px-4 text-center">Reservado</th>
                      <th className="py-3 px-4 text-center">Tránsito</th>
                      <th className="py-3 px-4 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-sm">
                    {filteredStock.map((item) => {
                      const isLow = item.cantidad < item.umbral;
                      return (
                        <tr key={item.id} className="hover:bg-slate-900/40">
                          <td className="py-4 px-4 font-mono font-bold text-slate-400">{item.codigo}</td>
                          <td className="py-4 px-4">
                            <p className="font-semibold text-slate-200">{item.nombre}</p>
                            <p className="text-xs text-slate-500 mt-0.5">{item.modelo}</p>
                          </td>
                          <td className="py-4 px-4 text-center">
                            <span
                              className={`font-semibold ${
                                isLow ? "text-red-400 bg-red-950/20 px-2 py-0.5 rounded" : "text-emerald-400"
                              }`}
                            >
                              {item.cantidad}
                            </span>
                            <span className="text-[10px] text-slate-500 block mt-0.5">Umbral: {item.umbral}</span>
                          </td>
                          <td className="py-4 px-4 text-center font-semibold text-slate-300">{item.apartados}</td>
                          <td className="py-4 px-4 text-center font-semibold text-slate-400">{item.transito}</td>
                          <td className="py-4 px-4 text-right">
                            {isLow && (
                              <button
                                onClick={() => handleReabastecer(item.id)}
                                className="bg-teal-600/90 hover:bg-teal-600 text-white font-medium px-3 py-1.5 rounded-lg text-xs transition-colors"
                              >
                                Reabastecer
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

          {/* Kardex logs list */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-sm">
              <h3 className="font-display font-bold text-white text-base">Kardex de Movimientos</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Log de auditoría transaccional del inventario:
              </p>
              
              <div className="space-y-3 pt-2 text-xs">
                {MOCK_MOVIMIENTOS.map((mov) => (
                  <div key={mov.id} className="p-3 bg-slate-950 border border-slate-850 rounded-xl space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-mono font-bold text-teal-400">{mov.codigo}</span>
                      <span className={`font-bold ${mov.cantidad > 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {mov.cantidad > 0 ? `+${mov.cantidad}` : mov.cantidad}
                      </span>
                    </div>
                    <p className="text-slate-300 font-medium">{mov.tipo}</p>
                    <div className="flex justify-between items-center text-[10px] text-slate-500">
                      <span>{mov.actor}</span>
                      <span>{mov.fecha}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-electric-950/20 border border-electric-900/30 rounded-3xl p-6">
              <h4 className="font-display font-bold text-electric-300 text-sm">💡 Regla de Persistencia</h4>
              <p className="text-xs text-electric-400/90 mt-2 leading-relaxed">
                Las transacciones en Kardex son auditories y atómicas. El software prohíbe la eliminación física de registros e impide stocks negativos.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
