"use client";

import React, { useState } from "react";
import Link from "next/link";

interface Repuesto {
  id: string;
  codigo: string;
  nombre: string;
  universo: "mototaxi" | "mototaxi_4r" | "motolineal";
  modelo: string;
  anio: number;
  precio_venta: number;
  disponible: number;
}

const MOCK_REPUESTOS: Repuesto[] = [
  { id: "1", codigo: "RP-001", nombre: "Pistón con anillos TVS", universo: "mototaxi", modelo: "TVS King", anio: 2021, precio_venta: 150.00, disponible: 12 },
  { id: "2", codigo: "RP-002", nombre: "Filtro de aceite original", universo: "mototaxi", modelo: "Bajaj Torito", anio: 2020, precio_venta: 85.50, disponible: 40 },
  { id: "3", codigo: "RP-003", nombre: "Amortiguador trasero Pulsar", universo: "motolineal", modelo: "Pulsar 200 NS", anio: 2022, precio_venta: 320.00, disponible: 8 },
  { id: "4", codigo: "RP-004", nombre: "Pastillas de freno RE", universo: "mototaxi_4r", modelo: "Torito RE", anio: 2019, precio_venta: 45.00, disponible: 25 },
  { id: "5", codigo: "RP-005", nombre: "Cable de embrague reforzado", universo: "mototaxi", modelo: "Bajaj Torito Chrome", anio: 2023, precio_venta: 110.00, disponible: 15 },
];

export default function CatalogoPage() {
  const [search, setSearch] = useState("");
  const [universo, setUniverso] = useState<string>("todos");

  const filtered = MOCK_REPUESTOS.filter((r) => {
    const matchesSearch = r.nombre.toLowerCase().includes(search.toLowerCase()) || 
                          r.codigo.toLowerCase().includes(search.toLowerCase()) ||
                          r.modelo.toLowerCase().includes(search.toLowerCase());
    const matchesUniverso = universo === "todos" || r.universo === universo;
    return matchesSearch && matchesUniverso;
  });

  return (
    <div className="flex-1 flex flex-col">
      {/* Header navbar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm">
            S
          </Link>
          <span className="font-display font-bold text-slate-900">Catálogo de Repuestos</span>
        </div>
        <Link href="/" className="text-sm text-slate-500 hover:text-teal-600 transition-colors">
          Volver al Inicio
        </Link>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 flex flex-col gap-6">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900">Buscar Repuestos</h2>
          <p className="text-slate-500 text-sm mt-1">
            Consulta disponibilidad y precios en tiempo real para Bajaj y TVS.
          </p>
        </div>

        {/* Filter bar */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar por nombre, código o modelo de vehículo..."
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500/20 text-sm text-slate-700 bg-slate-50"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <select
              className="px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-700"
              value={universo}
              onChange={(e) => setUniverso(e.target.value)}
            >
              <option value="todos">Todos los Universos</option>
              <option value="mototaxi">Mototaxi (3R)</option>
              <option value="mototaxi_4r">Mototaxi 4R</option>
              <option value="motolineal">Moto Lineal</option>
            </select>
          </div>
        </div>

        {/* Repuestos list */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.length > 0 ? (
            filtered.map((repuesto) => (
              <div
                key={repuesto.id}
                className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded">
                      {repuesto.codigo}
                    </span>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {repuesto.universo}
                    </span>
                  </div>
                  <h3 className="font-display font-bold text-lg text-slate-800 mt-3 leading-snug">
                    {repuesto.nombre}
                  </h3>
                  <div className="space-y-1 mt-4 text-xs text-slate-500">
                    <p>Vehículo: <span className="font-medium text-slate-700">{repuesto.modelo} ({repuesto.anio})</span></p>
                    <p>
                      Disponibilidad:{" "}
                      <span className={`font-semibold ${repuesto.disponible > 10 ? "text-emerald-600" : "text-amber-600"}`}>
                        {repuesto.disponible} unidades
                      </span>
                    </p>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="font-mono text-lg font-bold text-slate-900">
                    S/ {repuesto.precio_venta.toFixed(2)}
                  </span>
                  <Link
                    href={`/reservas?codigo=${repuesto.codigo}`}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2 rounded-xl text-xs transition-colors"
                  >
                    Reservar
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full py-12 text-center text-slate-400">
              No se encontraron repuestos que coincidan con la búsqueda.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
