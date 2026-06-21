"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/src/context/AuthContext";

interface Repuesto {
  id: string;
  codigo: string;
  nombre: string;
  universo: "mototaxi" | "motolineal";
  modelo: string;
  año: number;
  categoria: string;
  activo: boolean;
  advertencia_instalacion: boolean;
  precio_venta?: string | null;
  precio_visible?: boolean;
  disponible?: boolean | number;
  precio_mensaje?: string | null;
  precio_limite_alcanzado?: boolean;
}

export default function CatalogoPage() {
  const { user, accessToken, logout } = useAuth();
  const [repuestos, setRepuestos] = useState<Repuesto[]>([]);
  const [search, setSearch] = useState("");
  const [universo, setUniverso] = useState<string>("todos");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [consultasRealizadas, setConsultasRealizadas] = useState(0);

  const fetchRepuestos = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const isInternal = user && ["ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR", "SUPERADMIN"].includes(user.rol);
      let list: Repuesto[] = [];

      const getListForUniverso = async (univ: string) => {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }
        const res = await fetch(`/api-proxy/v1/repuestos?universo=${univ}`, { headers });
        if (!res.ok) {
          throw new Error(`Error al buscar repuestos del universo ${univ}`);
        }
        const body = await res.json();
        return (body.data?.repuestos ?? []) as Repuesto[];
      };

      if (universo === "todos") {
        const [mototaxis, motolineales] = await Promise.all([
          getListForUniverso("mototaxi"),
          getListForUniverso("motolineal"),
        ]);
        list = [...mototaxis, ...motolineales];
      } else {
        list = await getListForUniverso(universo);
      }

      if (isInternal) {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }
        const enriched = await Promise.all(
          list.map(async (r) => {
            let precio_venta: string | null = null;
            let disponible: number = 0;
            try {
              const [pRes, sRes] = await Promise.all([
                fetch(`/api-proxy/v1/repuestos/${r.codigo}/precio?nivel_visibilidad=2`, { headers }),
                fetch(`/api-proxy/v1/stock/${r.codigo}`, { headers }),
              ]);
              if (pRes.ok) {
                const pData = await pRes.json();
                precio_venta = pData.data?.precio_venta ?? null;
              }
              if (sRes.ok) {
                const sData = await sRes.json();
                disponible = sData.data?.cantidad_disponible ?? 0;
              }
            } catch (err) {
              console.error(`Error enriching ${r.codigo}:`, err);
            }
            return {
              ...r,
              precio_venta,
              precio_visible: true,
              disponible,
            };
          })
        );
        setRepuestos(enriched);
      } else {
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (accessToken) {
          headers["Authorization"] = `Bearer ${accessToken}`;
        }
        const enriched = await Promise.all(
          list.map(async (r) => {
            let disponible = false;
            try {
              const pRes = await fetch(`/api-proxy/v1/repuestos/${r.codigo}/precio?nivel_visibilidad=0`, { headers });
              if (pRes.ok) {
                const pData = await pRes.json();
                disponible = pData.data?.disponible ?? false;
              }
            } catch (err) {
              console.error(`Error checking availability for ${r.codigo}:`, err);
            }
            return {
              ...r,
              disponible,
            };
          })
        );
        setRepuestos(enriched);
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Error al cargar repuestos");
    } finally {
      setLoading(false);
    }
  }, [universo, user, accessToken]);

  useEffect(() => {
    fetchRepuestos();
  }, [fetchRepuestos]);

  const handleVerPrecio = async (codigo: string) => {
    if (!user) {
      setRepuestos((prev) =>
        prev.map((r) =>
          r.codigo === codigo
            ? { ...r, precio_mensaje: "Inicia sesión para consultar precios" }
            : r
        )
      );
      return;
    }

    const isInternal = ["ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR", "SUPERADMIN"].includes(user.rol);
    const nivelVisibilidad = isInternal ? 2 : 1;

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
      }

      const res = await fetch(
        `/api-proxy/v1/repuestos/${codigo}/precio?consultas_realizadas=${consultasRealizadas}&nivel_visibilidad=${nivelVisibilidad}`,
        { headers }
      );

      if (res.ok) {
        const body = await res.json();
        const data = body.data;

        setRepuestos((prev) =>
          prev.map((r) => {
            if (r.codigo === codigo) {
              return {
                ...r,
                precio_venta: data.precio_venta,
                precio_visible: data.precio_visible,
                precio_limite_alcanzado: data.precio_limite_alcanzado,
                precio_mensaje: data.mensaje,
                disponible: data.disponible,
              };
            }
            return r;
          })
        );

        if (nivelVisibilidad === 1 && data.precio_visible) {
          setConsultasRealizadas((prev) => prev + 1);
        }
      } else {
        const body = await res.json();
        const errMsg = body.detail?.message || "Error al obtener precio";
        setRepuestos((prev) =>
          prev.map((r) =>
            r.codigo === codigo ? { ...r, precio_mensaje: errMsg } : r
          )
        );
      }
    } catch (err) {
      console.error(err);
      setRepuestos((prev) =>
        prev.map((r) =>
          r.codigo === codigo ? { ...r, precio_mensaje: "Error de red" } : r
        )
      );
    }
  };

  const filtered = repuestos.filter((r) => {
    const matchesSearch =
      r.nombre.toLowerCase().includes(search.toLowerCase()) ||
      r.codigo.toLowerCase().includes(search.toLowerCase()) ||
      r.modelo.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

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
              Catálogo de Repuestos
            </span>
            <span className="text-[10px] text-slate-500 font-mono uppercase">
              Tecnimotos Santi
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {user && user.rol.startsWith("CLIENTE_") && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-3 py-1.5 text-xs text-amber-700 font-medium">
              Consultas de precio: {consultasRealizadas} / 3
            </div>
          )}

          {user ? (
            <div className="flex items-center gap-4">
              <div className="text-right text-xs">
                <p className="font-bold text-slate-800 font-display">
                  {user.id === "user-admin-seed" ? "Administrador (Seed)" : user.id}
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
          <h2 className="text-3xl font-display font-bold text-slate-900">
            Buscar Repuestos
          </h2>
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
              className="px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-teal-500 text-sm bg-slate-50 text-slate-700 font-medium"
              value={universo}
              onChange={(e) => setUniverso(e.target.value)}
            >
              <option value="todos">Todos los Universos</option>
              <option value="mototaxi">Mototaxi (3R/4R)</option>
              <option value="motolineal">Moto Lineal</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm mt-4 font-medium">
              Cargando catálogo en tiempo real...
            </p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
            <p className="text-red-700 font-semibold">{error}</p>
            <button
              onClick={() => fetchRepuestos()}
              className="mt-4 bg-red-600 hover:bg-red-700 text-white text-xs px-4 py-2 rounded-xl font-medium transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : (
          /* Repuestos list */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.length > 0 ? (
              filtered.map((repuesto) => {
                const isInternal =
                  user &&
                  [
                    "ADMINISTRADOR",
                    "VENDEDOR",
                    "MECANICO_MASTER",
                    "MECANICO_JUNIOR",
                    "SUPERADMIN",
                  ].includes(user.rol);

                return (
                  <div
                    key={repuesto.id}
                    className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded">
                          {repuesto.codigo}
                        </span>
                        <div className="flex gap-1.5">
                          <span className="text-[9px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                            {repuesto.universo}
                          </span>
                          <span className="text-[9px] uppercase font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-600">
                            {repuesto.categoria}
                          </span>
                        </div>
                      </div>
                      <h3 className="font-display font-bold text-lg text-slate-800 mt-3 leading-snug">
                        {repuesto.nombre}
                      </h3>
                      <div className="space-y-1 mt-4 text-xs text-slate-500">
                        <p>
                          Vehículo:{" "}
                          <span className="font-medium text-slate-700">
                            {repuesto.modelo} ({repuesto.año})
                          </span>
                        </p>
                        <p>
                          Disponibilidad:{" "}
                          {isInternal ? (
                            <span
                              className={`font-semibold ${
                                (repuesto.disponible as number) > 5
                                  ? "text-emerald-600"
                                  : "text-amber-600"
                              }`}
                            >
                              {repuesto.disponible} unidades
                            </span>
                          ) : (
                            <span
                              className={`font-semibold ${
                                repuesto.disponible
                                  ? "text-emerald-600"
                                  : "text-rose-600"
                              }`}
                            >
                              {repuesto.disponible ? "Disponible" : "Agotado"}
                            </span>
                          )}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
                      <div className="flex flex-col">
                        {repuesto.precio_visible ? (
                          <span className="font-mono text-lg font-bold text-slate-900">
                            S/{" "}
                            {repuesto.precio_venta
                              ? parseFloat(repuesto.precio_venta).toFixed(2)
                              : "0.00"}
                          </span>
                        ) : repuesto.precio_mensaje ? (
                          <span className="text-xs text-slate-500 font-medium italic">
                            {repuesto.precio_mensaje}
                          </span>
                        ) : (
                          <button
                            onClick={() => handleVerPrecio(repuesto.codigo)}
                            className="text-xs text-teal-600 hover:text-teal-700 font-semibold underline flex items-center gap-1"
                          >
                            Consultar precio
                          </button>
                        )}
                      </div>
                      <Link
                        href={`/reservas?codigo=${repuesto.codigo}`}
                        className={`bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2 rounded-xl text-xs transition-colors ${
                          !isInternal && !repuesto.disponible
                            ? "opacity-50 pointer-events-none bg-slate-400"
                            : ""
                        }`}
                      >
                        Reservar
                      </Link>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-full py-12 text-center text-slate-400">
                No se encontraron repuestos que coincidan con la búsqueda.
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

