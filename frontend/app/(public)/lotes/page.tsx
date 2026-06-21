"use client";

import React, { useState } from "react";
import Link from "next/link";

interface ItemLista {
  id: string;
  codigo: string;
  nombre: string;
  cantidad: number;
  precio_ref: number;
  disponible: boolean;
}

const MOCK_HISTORIAL_LOTES = [
  { id: "LOTE-901", fecha: "2026-06-20", repuestos: 8, monto: 1240.00, estado: "En Camino", destino: "Distrito San Juan" },
  { id: "LOTE-784", fecha: "2026-06-15", repuestos: 15, monto: 3105.50, estado: "Entregado", destino: "Distrito Tambo" },
  { id: "LOTE-512", fecha: "2026-06-12", repuestos: 4, monto: 640.00, estado: "Entregado", destino: "Huanta Centro" },
];

export default function LotesPage() {
  const [activeTab, setActiveTab] = useState<"lista" | "historial">("lista");
  const [items, setItems] = useState<ItemLista[]>([
    { id: "1", codigo: "RP-001", nombre: "Pistón con anillos TVS", cantidad: 5, precio_ref: 150.00, disponible: true },
    { id: "2", codigo: "RP-002", nombre: "Filtro de aceite original", cantidad: 10, precio_ref: 85.50, disponible: true },
    { id: "3", codigo: "RP-005", nombre: "Cable de embrague reforzado", cantidad: 3, precio_ref: 110.00, disponible: false },
  ]);

  const [nuevoCodigo, setNuevoCodigo] = useState("");
  const [nuevaCantidad, setNuevaCantidad] = useState(1);

  const addItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoCodigo) return;

    // Simulate looking up a part
    const newItem: ItemLista = {
      id: Math.random().toString(),
      codigo: nuevoCodigo.toUpperCase(),
      nombre: `Repuesto Registrado ${nuevoCodigo.toUpperCase()}`,
      cantidad: nuevaCantidad,
      precio_ref: Math.floor(40 + Math.random() * 200),
      disponible: Math.random() > 0.2, // 80% chance of stock availability in mockup
    };

    setItems([...items, newItem]);
    setNuevoCodigo("");
    setNuevaCantidad(1);
  };

  const removeItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const totalEstimado = items.reduce((acc, item) => acc + item.precio_ref * item.cantidad, 0);

  return (
    <div className="flex-1 flex flex-col">
      {/* Header navbar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-slate-900">Pedidos por Lote</span>
        </div>
        <Link href="/" className="text-sm text-slate-500 hover:text-teal-600 transition-colors">
          Volver al Inicio
        </Link>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 flex flex-col gap-6">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900">Pedidos al por Mayor</h2>
          <p className="text-slate-500 text-sm mt-1">
            Consolida múltiples repuestos en un solo pedido con envío prioritario a distritos.
          </p>
        </div>

        {/* Tabs switcher */}
        <div className="flex border-b border-slate-200 gap-6">
          <button
            onClick={() => setActiveTab("lista")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === "lista"
                ? "border-teal-500 text-teal-600"
                : "border-transparent text-slate-400 hover:text-slate-600"
            }`}
          >
            📋 Lista Progresiva de Reserva
          </button>
          <button
            onClick={() => setActiveTab("historial")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === "historial"
                ? "border-teal-500 text-teal-600"
                : "border-transparent text-slate-400 hover:text-slate-600"
            }`}
          >
            🚚 Historial de Envíos
          </button>
        </div>

        {activeTab === "lista" ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Interactive Builder */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-6">
                <h3 className="text-lg font-display font-bold text-slate-900 border-b border-slate-100 pb-3">
                  Añadir al Lote
                </h3>

                <form onSubmit={addItem} className="flex flex-col sm:flex-row gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      Código de Repuesto
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="Ej. RP-103"
                      className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800 font-mono"
                      value={nuevoCodigo}
                      onChange={(e) => setNuevoCodigo(e.target.value)}
                    />
                  </div>

                  <div className="w-full sm:w-32">
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      Cantidad
                    </label>
                    <input
                      type="number"
                      required
                      min="1"
                      className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800"
                      value={nuevaCantidad}
                      onChange={(e) => setNuevaCantidad(parseInt(e.target.value) || 1)}
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full sm:w-auto bg-teal-600 hover:bg-teal-700 text-white font-medium px-6 py-3 rounded-xl transition-colors text-sm"
                  >
                    Agregar
                  </button>
                </form>
              </div>

              {/* Items List */}
              <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-lg font-display font-bold text-slate-900">Items en la Lista</h3>

                {items.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {items.map((item) => (
                      <div key={item.id} className="py-4 flex items-center justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded">
                              {item.codigo}
                            </span>
                            <span
                              className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                item.disponible
                                  ? "bg-emerald-50 text-emerald-700"
                                  : "bg-red-50 text-red-700"
                              }`}
                            >
                              {item.disponible ? "Stock Disponible" : "Sin Stock Inmediato"}
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-slate-800 mt-1">{item.nombre}</p>
                          <p className="text-xs text-slate-400 mt-0.5">Precio Ref: S/ {item.precio_ref.toFixed(2)} c/u</p>
                        </div>

                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm font-mono font-bold text-slate-900">
                              S/ {(item.precio_ref * item.cantidad).toFixed(2)}
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">{item.cantidad} unidades</p>
                          </div>
                          <button
                            onClick={() => removeItem(item.id)}
                            className="text-slate-400 hover:text-red-500 transition-colors text-lg"
                            title="Eliminar"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center py-8 text-slate-400 text-sm">Tu lista de reserva progresiva está vacía.</p>
                )}
              </div>
            </div>

            {/* Order Summary & Actions */}
            <div>
              <div className="bg-slate-50 border border-slate-200 rounded-3xl p-6 space-y-6">
                <h4 className="font-display font-bold text-slate-900 text-base">Resumen del Lote</h4>
                
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between text-slate-500">
                    <span>Total de Repuestos</span>
                    <span className="font-semibold text-slate-800">{items.reduce((acc, i) => acc + i.cantidad, 0)} piezas</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Tipos de repuesto</span>
                    <span className="font-semibold text-slate-800">{items.length} distintos</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>Destino (Distrito)</span>
                    <span className="font-semibold text-teal-700">Tambo, Ayacucho</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-200 flex justify-between items-end">
                  <span className="text-xs font-semibold text-slate-500">Total Estimado</span>
                  <span className="font-mono text-xl font-bold text-slate-900">S/ {totalEstimado.toFixed(2)}</span>
                </div>

                <button
                  disabled={items.length === 0}
                  className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-teal-500/10 text-sm"
                  onClick={() => alert("Simulando creación de pedido por lote (Modo Mock).")}
                >
                  Confirmar Pedido y Generar Proforma
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Historial de envíos */
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm overflow-x-auto">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">ID Pedido</th>
                  <th className="py-3 px-4">Fecha</th>
                  <th className="py-3 px-4">Destino</th>
                  <th className="py-3 px-4 text-center">Nro Repuestos</th>
                  <th className="py-3 px-4 text-right">Monto Total</th>
                  <th className="py-3 px-4 text-center">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {MOCK_HISTORIAL_LOTES.map((lote) => (
                  <tr key={lote.id} className="hover:bg-slate-50/50">
                    <td className="py-4 px-4 font-mono font-bold text-slate-700">{lote.id}</td>
                    <td className="py-4 px-4 text-slate-500">{lote.fecha}</td>
                    <td className="py-4 px-4 text-slate-800">{lote.destino}</td>
                    <td className="py-4 px-4 text-center text-slate-600">{lote.repuestos}</td>
                    <td className="py-4 px-4 text-right font-mono font-semibold text-slate-900">S/ {lote.monto.toFixed(2)}</td>
                    <td className="py-4 px-4 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          lote.estado === "En Camino"
                            ? "bg-blue-50 text-blue-700"
                            : "bg-emerald-50 text-emerald-700"
                        }`}
                      >
                        {lote.estado}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
