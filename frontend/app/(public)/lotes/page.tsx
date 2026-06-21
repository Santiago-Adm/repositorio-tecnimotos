"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/src/context/AuthContext";

interface ItemLista {
  id: string;
  repuesto_id: string;
  codigo: string;
  nombre: string;
  cantidad: number;
  precio_ref: number;
  disponible: boolean;
}

interface HistorialPedido {
  pedido_id: string;
  estado: string;
  canal_origen: string;
  cliente_id: string;
  monto_total: string;
  created_at: string;
}

export default function LotesPage() {
  const { user, accessToken, logout } = useAuth();
  
  const [activeTab, setActiveTab] = useState<"lista" | "historial">("lista");
  const [items, setItems] = useState<ItemLista[]>([]);
  const [historial, setHistorial] = useState<HistorialPedido[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  const [nuevoCodigo, setNuevoCodigo] = useState("");
  const [nuevaCantidad, setNuevaCantidad] = useState(1);
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [exitoInfo, setExitoInfo] = useState<{
    pedido_id: string;
    monto_total: number;
  } | null>(null);

  // Map seed client ID based on role
  const getClienteId = (): string => {
    // defaults to S2 (Distrito) seed client ID for testing
    return "5a4f5e5b-1f11-44ad-af69-d96b8b81ed80";
  };

  const addItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoCodigo) return;
    setAdding(true);
    setAddError(null);

    try {
      const headers = { "Content-Type": "application/json" };
      
      // 1. Fetch part basic info
      const res = await fetch(`/api-proxy/v1/repuestos/${nuevoCodigo.toUpperCase()}`, { headers });
      if (!res.ok) {
        throw new Error("El código de repuesto no existe en el catálogo.");
      }
      const rBody = await res.json();
      const rData = rBody.data;

      // 2. Fetch reference price (using level 0 since it is a public-facing lote list)
      const pRes = await fetch(`/api-proxy/v1/repuestos/${nuevoCodigo.toUpperCase()}/precio?nivel_visibilidad=0`, { headers });
      let precio_ref = 0;
      if (pRes.ok) {
        const pBody = await pRes.json();
        precio_ref = parseFloat(pBody.data?.precio_venta || "0.00");
      }

      // Check if already in list
      const exists = items.some((item) => item.codigo === rData.codigo);
      if (exists) {
        setItems(prev => prev.map(item => {
          if (item.codigo === rData.codigo) {
            return { ...item, cantidad: item.cantidad + nuevaCantidad };
          }
          return item;
        }));
      } else {
        setItems(prev => [
          ...prev,
          {
            id: Math.random().toString(),
            repuesto_id: rData.id,
            codigo: rData.codigo,
            nombre: rData.nombre,
            cantidad: nuevaCantidad,
            precio_ref,
            disponible: rData.disponible,
          }
        ]);
      }

      setNuevoCodigo("");
      setNuevaCantidad(1);
    } catch (err) {
      console.error(err);
      setAddError(err instanceof Error ? err.message : "Error al buscar repuesto");
    } finally {
      setAdding(false);
    }
  };

  const removeItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const fetchHistorial = useCallback(async () => {
    if (!accessToken) return;
    setLoadingHistory(true);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };
      // Fetch orders for client04's seed ID
      const cid = getClienteId();
      const res = await fetch(`/api-proxy/v1/pedidos?cliente_id=${cid}`, { headers });
      if (res.ok) {
        const body = await res.json();
        setHistorial(body.data?.pedidos ?? []);
      }
    } catch (e) {
      console.error("Error fetching order history:", e);
    } finally {
      setLoadingHistory(false);
    }
  }, [accessToken]);

  useEffect(() => {
    if (activeTab === "historial") {
      fetchHistorial();
    }
  }, [activeTab, fetchHistorial]);

  const handleConfirmarPedido = async () => {
    if (items.length === 0) return;
    if (!accessToken) {
      setSubmitError("Debes iniciar sesión para formalizar tu pedido.");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const cid = getClienteId();

      // Step 1: Create progressive reservation list (EP-PED-13)
      const listRes = await fetch("/api-proxy/v1/lista-reserva-progresiva", {
        method: "POST",
        headers,
        body: JSON.stringify({
          cliente_id: cid,
          nombre: `Lote ${new Date().toLocaleDateString("es-PE")}`,
          items: items.map(i => ({
            repuesto_id: i.repuesto_id,
            codigo: i.codigo,
            cantidad: i.cantidad,
            precio_referencia: i.precio_ref,
          })),
        }),
      });

      if (!listRes.ok) {
        const body = await listRes.json();
        const msg = body.detail?.error?.message || body.detail?.message || "Error al crear la lista de reserva";
        throw new Error(`${listRes.status} | ${msg}`);
      }

      const listBody = await listRes.json();
      const lista_id = listBody.data?.lista_id;

      // Step 2: Formalize reservation list into actual order (EP-PED-14)
      const formRes = await fetch(`/api-proxy/v1/lista-reserva-progresiva/${lista_id}/formalizar`, {
        method: "POST",
        headers,
      });

      if (!formRes.ok) {
        const body = await formRes.json();
        const msg = body.detail?.error?.message || body.detail?.message || "Error al formalizar el pedido";
        throw new Error(`${formRes.status} | ${msg}`);
      }

      // Success: Clear cart and show receipt
      const total = items.reduce((acc, item) => acc + item.precio_ref * item.cantidad, 0);
      setExitoInfo({
        pedido_id: lista_id,
        monto_total: total,
      });
      setItems([]);
    } catch (err) {
      console.error(err);
      setSubmitError(err instanceof Error ? err.message : "Error al formalizar el pedido.");
    } finally {
      setSubmitting(false);
    }
  };

  const totalEstimado = items.reduce((acc, item) => acc + item.precio_ref * item.cantidad, 0);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      {/* Header navbar */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm hover:bg-teal-700 transition-colors"
          >
            S
          </Link>
          <div>
            <span className="font-display font-bold text-slate-900 block leading-tight">
              Pedidos por Lote
            </span>
            <span className="text-[10px] text-slate-500 font-mono uppercase">
              Área de Clientes
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-4">
              <div className="text-right text-xs">
                <p className="font-bold text-slate-800 font-display">
                  {user.id === "user-admin-seed" ? "Administrador (Seed)" : "Cliente Mayorista"}
                </p>
                <p className="text-slate-500 font-mono text-[10px] uppercase">
                  {user.rol}
                </p>
              </div>
              <button
                onClick={() => logout()}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded-lg transition-colors font-medium border border-slate-200"
              >
                Cerrar Sesión
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 italic">Invitado</span>
              <Link
                href="/login"
                className="bg-teal-600 hover:bg-teal-700 text-white text-xs px-4 py-2 rounded-xl transition-colors font-medium shadow-sm"
              >
                Iniciar Sesión
              </Link>
            </div>
          )}

          <Link
            href="/"
            className="text-xs text-slate-500 hover:text-teal-600 transition-colors font-medium border-l border-slate-200 pl-4 ml-2"
          >
            Inicio
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 flex flex-col gap-6">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900 tracking-tight">
            Pedidos al por Mayor
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Consolida múltiples repuestos en un solo lote con envío prioritario a distritos.
          </p>
        </div>

        {/* Tabs switcher */}
        <div className="flex border-b border-slate-200 gap-6">
          <button
            onClick={() => {
              setActiveTab("lista");
              setExitoInfo(null);
            }}
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
          exitoInfo ? (
            <div className="bg-white border border-slate-200 rounded-3xl p-8 max-w-md mx-auto shadow-sm text-center space-y-6">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-3xl">
                ✓
              </div>
              <div className="space-y-2">
                <h3 className="text-2xl font-display font-bold text-slate-900">
                  ¡Pedido Formalizado!
                </h3>
                <p className="text-slate-500 text-xs leading-relaxed max-w-sm mx-auto">
                  La lista progresiva se ha convertido en un pedido formalizado en el backend. 
                </p>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-5 text-left space-y-3 font-mono text-xs">
                <div className="flex justify-between border-b border-slate-200 pb-2">
                  <span className="text-slate-400">ID Pedido / Lista:</span>
                  <span className="font-bold text-slate-800">{exitoInfo.pedido_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Monto Total:</span>
                  <span className="font-bold text-teal-600">S/ {exitoInfo.monto_total.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Estado Inicial:</span>
                  <span className="font-bold text-slate-700">BORRADOR</span>
                </div>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  onClick={() => setExitoInfo(null)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 rounded-xl text-xs transition-colors border border-slate-200"
                >
                  Nueva Lista
                </button>
                <button
                  onClick={() => setActiveTab("historial")}
                  className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-2.5 rounded-xl text-xs transition-colors shadow-sm"
                >
                  Ver Historial
                </button>
              </div>
            </div>
          ) : (
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
                        placeholder="Ej. SEED-000"
                        className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800 font-mono uppercase"
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
                        className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-800 font-mono"
                        value={nuevaCantidad}
                        onChange={(e) => setNuevaCantidad(parseInt(e.target.value) || 1)}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={adding}
                      className="w-full sm:w-auto bg-teal-600 hover:bg-teal-700 text-white font-medium px-6 py-3 rounded-xl transition-colors text-sm"
                    >
                      {adding ? "Buscando..." : "Agregar"}
                    </button>
                  </form>

                  {addError && (
                    <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs">
                      ⚠️ {addError}
                    </div>
                  )}
                </div>

                {/* Items List */}
                <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
                  <h3 className="text-lg font-display font-bold text-slate-900">
                    Items en la Lista
                  </h3>

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
                            <p className="text-sm font-semibold text-slate-800 mt-1">
                              {item.nombre}
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">
                              Precio Ref: S/ {item.precio_ref.toFixed(2)} c/u
                            </p>
                          </div>

                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-sm font-mono font-bold text-slate-900">
                                S/ {(item.precio_ref * item.cantidad).toFixed(2)}
                              </p>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {item.cantidad} unidades
                              </p>
                            </div>
                            <button
                              onClick={() => removeItem(item.id)}
                              className="text-slate-400 hover:text-red-500 transition-colors text-lg"
                              title="Eliminar"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center py-8 text-slate-400 text-sm">
                      Tu lista de reserva progresiva está vacía.
                    </p>
                  )}
                </div>
              </div>

              {/* Order Summary & Actions */}
              <div>
                <div className="bg-slate-50 border border-slate-200 rounded-3xl p-6 space-y-6">
                  <h4 className="font-display font-bold text-slate-900 text-base">
                    Resumen del Lote
                  </h4>
                  
                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between text-slate-500">
                      <span>Total de Repuestos</span>
                      <span className="font-semibold text-slate-800">
                        {items.reduce((acc, i) => acc + i.cantidad, 0)} piezas
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-500">
                      <span>Tipos de repuesto</span>
                      <span className="font-semibold text-slate-800">
                        {items.length} distintos
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-500">
                      <span>Destino (Distrito)</span>
                      <span className="font-semibold text-teal-700">Tambo, Ayacucho</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-200 flex justify-between items-end">
                    <span className="text-xs font-semibold text-slate-500">Total Estimado</span>
                    <span className="font-mono text-xl font-bold text-slate-900">
                      S/ {totalEstimado.toFixed(2)}
                    </span>
                  </div>

                  {submitError && (
                    <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs space-y-1">
                      <p className="font-semibold">Error al confirmar pedido:</p>
                      <p className="leading-normal text-slate-600">{submitError}</p>
                    </div>
                  )}

                  <button
                    disabled={items.length === 0 || submitting}
                    className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-350 text-white font-medium py-3 rounded-xl transition-all shadow-md shadow-teal-500/10 text-sm flex items-center justify-center gap-2"
                    onClick={handleConfirmarPedido}
                  >
                    {submitting ? (
                      <>
                        <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                        Formalizando en Backend...
                      </>
                    ) : (
                      "Confirmar Pedido y Generar Proforma"
                    )}
                  </button>
                </div>
              </div>
            </div>
          )
        ) : (
          /* Historial de envíos */
          <div className="bg-white border border-slate-200 rounded-3xl p-6 shadow-sm overflow-x-auto">
            {loadingHistory ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                Cargando historial...
              </div>
            ) : historial.length > 0 ? (
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-bold text-slate-400 uppercase tracking-wider">
                    <th className="py-3 px-4">ID Pedido / Lista</th>
                    <th className="py-3 px-4">Fecha Creación</th>
                    <th className="py-3 px-4">Canal</th>
                    <th className="py-3 px-4 text-right">Monto Total</th>
                    <th className="py-3 px-4 text-center">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-sm">
                  {historial.map((lote) => (
                    <tr key={lote.pedido_id} className="hover:bg-slate-50/50">
                      <td className="py-4 px-4 font-mono font-bold text-slate-700 text-xs">
                        {lote.pedido_id}
                      </td>
                      <td className="py-4 px-4 text-slate-500">
                        {new Date(lote.created_at).toLocaleString("es-PE")}
                      </td>
                      <td className="py-4 px-4 text-slate-800 font-medium">
                        {lote.canal_origen}
                      </td>
                      <td className="py-4 px-4 text-right font-mono font-semibold text-slate-900">
                        S/ {parseFloat(lote.monto_total).toFixed(2)}
                      </td>
                      <td className="py-4 px-4 text-center">
                        <span
                          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            lote.estado === "BORRADOR"
                              ? "bg-amber-50 text-amber-700 border border-amber-200/50"
                              : lote.estado === "ENTREGADO"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/50"
                              : "bg-blue-50 text-blue-700 border border-blue-200/50"
                          }`}
                        >
                          {lote.estado}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="py-12 text-center text-slate-400 text-sm">
                No hay pedidos formalizados para este cliente.
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

