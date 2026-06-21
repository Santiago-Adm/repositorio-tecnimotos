"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/src/context/AuthContext";

interface StockItem {
  repuesto_id: string;
  codigo: string;
  nombre: string;
  modelo: string;
  cantidad: number;
  apartados: number;
  transito: number;
  umbral: number;
  esta_agotado: boolean;
  esta_bajo_umbral: boolean;
}

interface Movimiento {
  id: string;
  tipo_movimiento: string;
  cantidad: number;
  estado_origen: string;
  estado_destino: string;
  actor_id: string;
  referencia_id: string;
  timestamp: string;
}

export default function StockPage() {
  const { user, accessToken, logout } = useAuth();
  
  const [stock, setStock] = useState<StockItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<StockItem | null>(null);
  const [movements, setMovements] = useState<Movimiento[]>([]);
  const [loadingMovements, setLoadingMovements] = useState(false);
  const [movementsError, setMovementsError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states for stock adjustment
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [adjustItem, setAdjustItem] = useState<StockItem | null>(null);
  const [adjustQty, setAdjustQty] = useState<number>(10);
  const [adjustReason, setAdjustReason] = useState("Ajuste manual de stock");
  const [adjustError, setAdjustError] = useState<string | null>(null);

  const fetchStockData = useCallback(async () => {
    if (!accessToken) {
      setError("Autenticación requerida. Por favor, inicia sesión.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      // 1. Fetch catalog metadata to match name and model of repuestos
      interface CatalogItem {
        codigo: string;
        nombre: string;
        modelo: string;
      }

      const getListForUniverso = async (univ: string): Promise<CatalogItem[]> => {
        const res = await fetch(`/api-proxy/v1/repuestos?universo=${univ}`, { headers });
        if (!res.ok) return [];
        const body = await res.json();
        return (body.data?.repuestos ?? []) as CatalogItem[];
      };

      const [mototaxis, motolineales] = await Promise.all([
        getListForUniverso("mototaxi"),
        getListForUniverso("motolineal"),
      ]);

      const repuestosMap = new Map<string, { nombre: string; modelo: string }>();
      [...mototaxis, ...motolineales].forEach((r: CatalogItem) => {
        repuestosMap.set(r.codigo, { nombre: r.nombre, modelo: r.modelo });
      });

      // 2. Fetch actual stock list
      const res = await fetch("/api-proxy/v1/stock", { headers });
      if (!res.ok) {
        const body = await res.json();
        const msg = body.detail?.error?.message || body.detail?.message || "Error al obtener la lista de stock";
        throw new Error(`${res.status} | ${msg}`);
      }

      interface RawStockItem {
        repuesto_id: string;
        codigo: string;
        cantidad_disponible: number;
        cantidad_apartada: number;
        cantidad_en_transito: number;
        umbral_minimo: number;
        esta_agotado: boolean;
        esta_bajo_umbral: boolean;
      }
      const body = await res.json();
      const rawStocks = (body.data?.stocks ?? []) as RawStockItem[];

      const enrichedStocks: StockItem[] = rawStocks.map((item) => {
        const meta = repuestosMap.get(item.codigo);
        return {
          repuesto_id: item.repuesto_id,
          codigo: item.codigo,
          nombre: meta?.nombre || "Repuesto del catálogo",
          modelo: meta?.modelo || "Universal",
          cantidad: item.cantidad_disponible ?? 0,
          apartados: item.cantidad_apartada ?? 0,
          transito: item.cantidad_en_transito ?? 0,
          umbral: item.umbral_minimo ?? 5,
          esta_agotado: item.esta_agotado ?? false,
          esta_bajo_umbral: item.esta_bajo_umbral ?? false,
        };
      });

      setStock(enrichedStocks);
      
      // Auto-select the first item if none is selected
      if (enrichedStocks.length > 0 && !selectedItem) {
        setSelectedItem(enrichedStocks[0]);
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Error al conectar con la API");
    } finally {
      setLoading(false);
    }
  }, [accessToken, selectedItem]);

  useEffect(() => {
    fetchStockData();
  }, [fetchStockData]);

  // Load movements whenever selected item changes
  const fetchMovements = useCallback(async (codigo: string) => {
    if (!accessToken) return;
    setLoadingMovements(true);
    setMovementsError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };
      const res = await fetch(`/api-proxy/v1/stock/${codigo}/movimientos`, { headers });
      if (!res.ok) {
        const body = await res.json();
        const msg = body.detail?.error?.message || body.detail?.message || "Acceso denegado";
        throw new Error(`${res.status} | ${msg}`);
      }
      const body = await res.json();
      setMovements(body.data?.movimientos ?? []);
    } catch (err) {
      console.error(err);
      setMovementsError(err instanceof Error ? err.message : "No autorizado para ver movimientos");
      setMovements([]);
    } finally {
      setLoadingMovements(false);
    }
  }, [accessToken]);

  useEffect(() => {
    if (selectedItem) {
      fetchMovements(selectedItem.codigo);
    }
  }, [selectedItem, fetchMovements]);

  // Handle stock adjustment
  const handleAjustarStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem || !accessToken || !user) return;
    setAdjustError(null);

    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/stock/${adjustItem.codigo}/ajuste`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          cantidad_ajuste: adjustQty,
          motivo: adjustReason,
          actor_id: user.id,
        }),
      });

      if (!res.ok) {
        const body = await res.json();
        const msg = body.detail?.error?.message || body.detail?.message || "No autorizado para ajustar stock";
        throw new Error(`${res.status} | ${msg}`);
      }

      // Success
      setShowAdjustModal(false);
      setAdjustQty(10);
      setAdjustReason("Ajuste manual de stock");
      
      // Refresh stock table and movements
      await fetchStockData();
      if (selectedItem?.codigo === adjustItem.codigo) {
        fetchMovements(adjustItem.codigo);
      }
    } catch (err) {
      console.error(err);
      setAdjustError(err instanceof Error ? err.message : "Error al realizar el ajuste");
    }
  };

  const filteredStock = stock.filter(
    (item) =>
      item.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.modelo.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const alertsCount = stock.filter((item) => item.esta_bajo_umbral).length;

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-100">
        <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm mt-4 font-medium font-display">
          Conectando con base de datos e inventario SANTI...
        </p>
      </div>
    );
  }

  // Check 403 blocking error from backend
  if (error && error.includes("403")) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 px-6 text-slate-100">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-md w-full shadow-2xl text-center space-y-6">
          <div className="w-16 h-16 bg-red-950/50 border border-red-900/50 text-red-500 rounded-full flex items-center justify-center mx-auto text-3xl">
            🔒
          </div>
          <div className="space-y-2">
            <h3 className="font-display font-bold text-xl text-white">
              Acceso Denegado (403)
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              El backend ha bloqueado tu solicitud de inventario debido a restricciones de rol.
            </p>
          </div>
          <div className="bg-slate-950 border border-slate-850 p-4 rounded-2xl text-left space-y-1.5">
            <p className="text-xs text-slate-500">
              Usuario: <span className="font-mono text-slate-300 font-bold">{user?.id}</span>
            </p>
            <p className="text-xs text-slate-500">
              Rol: <span className="font-mono text-amber-500 font-bold">{user?.rol}</span>
            </p>
            <p className="text-xs text-slate-500">
              Detalle: <span className="text-red-400 font-medium">{error}</span>
            </p>
          </div>
          <div className="flex flex-col gap-2 pt-2">
            <Link
              href="/"
              className="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors"
            >
              Volver al Inicio
            </Link>
            <button
              onClick={() => logout()}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors font-medium underline"
            >
              Cerrar sesión e ingresar con otra cuenta
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 px-6 text-slate-100">
        <div className="bg-slate-900 border border-red-900/30 rounded-3xl p-8 max-w-md w-full shadow-2xl text-center space-y-6">
          <div className="w-16 h-16 bg-red-950/20 text-red-400 rounded-full flex items-center justify-center mx-auto text-2xl">
            ⚠️
          </div>
          <div className="space-y-2">
            <h3 className="font-display font-bold text-xl text-white">Error de Conexión</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{error}</p>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => fetchStockData()}
              className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors"
            >
              Reintentar
            </button>
            <Link
              href="/"
              className="flex-1 bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors"
            >
              Inicio
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm hover:bg-teal-700 transition-colors"
          >
            S
          </Link>
          <div>
            <span className="font-display font-bold text-white tracking-wide block leading-tight">
              Gestión de Inventario (SANTI)
            </span>
            <span className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">
              Control de Stock
            </span>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-right text-xs">
            <p className="font-bold text-slate-200 font-display">{user?.id}</p>
            <p className="text-slate-500 font-mono text-[9px] uppercase tracking-wider">{user?.rol}</p>
          </div>
          <button
            onClick={() => logout()}
            className="bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 font-medium transition-colors"
          >
            Cerrar Sesión
          </button>
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-teal-400 transition-colors font-medium border-l border-slate-800 pl-4"
          >
            Inicio
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-8 max-w-7xl mx-auto w-full">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-display font-bold text-white tracking-tight">
              Stock y Movimientos
            </h2>
            <p className="text-slate-400 text-sm mt-1">
              Registro de existencias físicas, apartados y transacciones Kardex en el taller.
            </p>
          </div>

          {alertsCount > 0 && (
            <div className="bg-red-950/60 border border-red-900/50 text-red-400 px-4 py-2 rounded-2xl text-xs font-semibold flex items-center gap-2">
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
                  placeholder="Buscar por código, nombre o modelo..."
                  className="flex-1 px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white placeholder-slate-600 transition-colors"
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
                    {filteredStock.length > 0 ? (
                      filteredStock.map((item) => {
                        const isSelected = selectedItem?.codigo === item.codigo;
                        return (
                          <tr
                            key={item.codigo}
                            onClick={() => setSelectedItem(item)}
                            className={`cursor-pointer transition-colors ${
                              isSelected
                                ? "bg-slate-800/50 hover:bg-slate-800"
                                : "hover:bg-slate-900/40"
                            }`}
                          >
                            <td className="py-4 px-4 font-mono font-bold text-slate-400">
                              {item.codigo}
                            </td>
                            <td className="py-4 px-4">
                              <p className="font-semibold text-slate-200">{item.nombre}</p>
                              <p className="text-xs text-slate-500 mt-0.5">{item.modelo}</p>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span
                                className={`font-semibold ${
                                  item.esta_bajo_umbral
                                    ? "text-red-400 bg-red-950/20 px-2 py-0.5 rounded border border-red-900/20"
                                    : "text-emerald-400"
                                }`}
                              >
                                {item.cantidad}
                              </span>
                              <span className="text-[10px] text-slate-500 block mt-0.5">
                                Umbral: {item.umbral}
                              </span>
                            </td>
                            <td className="py-4 px-4 text-center font-semibold text-slate-300">
                              {item.apartados}
                            </td>
                            <td className="py-4 px-4 text-center font-semibold text-slate-400">
                              {item.transito}
                            </td>
                            <td className="py-4 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={() => {
                                  setAdjustItem(item);
                                  setShowAdjustModal(true);
                                }}
                                className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium px-3 py-1.5 rounded-lg text-xs transition-colors"
                              >
                                Ajustar
                              </button>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-600">
                          No se encontraron repuestos en el stock.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Kardex logs list */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-sm">
              <h3 className="font-display font-bold text-white text-base">
                Kardex de Movimientos
              </h3>
              {selectedItem ? (
                <div className="space-y-3">
                  <p className="text-xs text-slate-400">
                    Historial de auditoría para{" "}
                    <span className="font-mono font-bold text-teal-400">
                      {selectedItem.codigo}
                    </span>
                    :
                  </p>

                  {loadingMovements ? (
                    <div className="py-6 text-center text-slate-500 text-xs">
                      Cargando Kardex...
                    </div>
                  ) : movementsError ? (
                    <div className="p-3 bg-red-950/20 border border-red-900/20 text-red-400 rounded-xl text-xs">
                      <p className="font-semibold">Fallo de Permiso (403):</p>
                      <p className="mt-1 leading-normal text-slate-400">
                        {movementsError}
                      </p>
                    </div>
                  ) : movements.length > 0 ? (
                    <div className="space-y-3 text-xs max-h-[350px] overflow-y-auto pr-1">
                      {movements.map((mov) => (
                        <div
                          key={mov.id}
                          className="p-3 bg-slate-950 border border-slate-850 rounded-xl space-y-1.5 hover:border-slate-800 transition-colors"
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-mono text-[9px] uppercase bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded text-slate-400">
                              {mov.tipo_movimiento}
                            </span>
                            <span
                              className={`font-bold ${
                                mov.cantidad > 0 ? "text-emerald-400" : "text-red-400"
                              }`}
                            >
                              {mov.cantidad > 0 ? `+${mov.cantidad}` : mov.cantidad}
                            </span>
                          </div>
                          {mov.referencia_id && (
                            <p className="text-slate-400 text-[10px]">
                              Ref ID: <span className="font-mono text-slate-300">{mov.referencia_id}</span>
                            </p>
                          )}
                          <div className="flex justify-between items-center text-[9px] text-slate-500 pt-1 border-t border-slate-900/60">
                            <span>Actor: {mov.actor_id}</span>
                            <span>{new Date(mov.timestamp).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic py-4">
                      No hay movimientos registrados para este repuesto.
                    </p>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic py-4">
                  Selecciona un repuesto para cargar su historial Kardex.
                </p>
              )}
            </div>

            <div className="bg-teal-950/20 border border-teal-900/30 rounded-3xl p-6">
              <h4 className="font-display font-bold text-teal-400 text-sm">
                💡 Criterio de Consistencia
              </h4>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Las transacciones en Kardex son auditories y atómicas. El sistema prohíbe la eliminación física de registros e impide existencias negativas.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Adjust Stock Modal */}
      {showAdjustModal && adjustItem && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 animate-fadeIn">
          <form
            onSubmit={handleAjustarStock}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-6"
          >
            <div className="flex justify-between items-center">
              <h3 className="font-display font-bold text-lg text-white">
                Ajuste Manual de Inventario
              </h3>
              <button
                type="button"
                onClick={() => {
                  setShowAdjustModal(false);
                  setAdjustError(null);
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-850">
                <p className="text-xs text-slate-500">Repuesto Seleccionado</p>
                <p className="font-semibold text-slate-200 mt-1">{adjustItem.nombre}</p>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Cód: {adjustItem.codigo} | Stock actual: {adjustItem.cantidad}
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs text-slate-400 font-medium block">
                  Cantidad a Ajustar
                </label>
                <input
                  type="number"
                  required
                  placeholder="Ej. 10 para sumar, -5 para restar"
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(parseInt(e.target.value) || 0)}
                />
                <p className="text-[10px] text-slate-500">
                  Usa números positivos para entradas y negativos para salidas.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs text-slate-400 font-medium block">
                  Motivo de Ajuste
                </label>
                <textarea
                  required
                  rows={2}
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white resize-none"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                />
              </div>

              {adjustError && (
                <div className="p-3 bg-red-950/20 border border-red-900/20 text-red-400 rounded-xl text-xs">
                  <p className="font-semibold">Error al realizar ajuste (403/401):</p>
                  <p className="mt-1 leading-normal text-slate-400">{adjustError}</p>
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowAdjustModal(false);
                  setAdjustError(null);
                }}
                className="flex-1 bg-slate-800 hover:bg-slate-750 text-slate-300 font-medium py-2.5 rounded-xl text-xs transition-colors border border-slate-700"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors shadow-sm"
              >
                Confirmar Ajuste
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

