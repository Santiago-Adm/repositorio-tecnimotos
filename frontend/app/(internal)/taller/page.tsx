"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/src/context/AuthContext";

/**
 * ============================================================================
 * ⚖️ CONTEXTO DE NEGOCIO: ROL DE VENDEDOR EN LA CONSOLA DE TALLER
 * ============================================================================
 * El rol transversal de `VENDEDOR` opera bajo los siguientes lineamientos en taller:
 * 1. Acceso: Puede ingresar a la Consola de Taller (pertenece a los roles internos).
 * 2. Acciones Permitidas (Grupo TAL_VENDEDOR_ROLES):
 *    - EP-TAL-03: Puede formalizar/aprobar la lista inicial de repuestos del taller
 *      para avanzar el estado de ABIERTA/LISTA_REPUESTOS a EN_EJECUCION.
 *    - EP-TAL-04: Puede confirmar ítems adicionales agregados durante la ejecución
 *      que requieran aprobación manual del cliente (tramo de costo > S/100).
 * 3. Acciones Restringidas:
 *    - NO puede declarar revisión final (EP-TAL-06) ni liberar vehículos (EP-TAL-10)
 *      ya que estas son atribuciones exclusivas del equipo técnico (MECANICO_ROLES).
 *    - NO puede cobrar (EP-TAL-07) ni cerrar la OT (EP-TAL-08). El cobro parcial
 *      es exclusivo de ADMIN_ROLES (ADMINISTRADOR, SUPERADMIN).
 * 
 * La interfaz a continuación deshabilita o restringe visualmente las acciones 
 * según el rol decodificado del JWT en el AuthContext.
 * ============================================================================
 */

// Interfaces de comunicación con el Backend (EP-TAL-01 al EP-TAL-12)
interface RepuestoItem {
  item_id: string;
  repuesto_id: string;
  codigo: string;
  cantidad: number;
  precio_unitario: string;
  aprobacion: "PENDIENTE" | "APROBADO_AUTOMATICO" | "APROBADO_TACITO" | "APROBADO_EXPLICITO" | "RECHAZADO" | "PENDIENTE_ADICIONAL";
  tramo: "automatico" | "tacito" | "manual" | null;
}

interface BackendOT {
  ot_id: string;
  estado: "ABIERTA" | "LISTA_REPUESTOS" | "EN_EJECUCION" | "REVISION_FINAL" | "CERRADA" | "CANCELADA";
  vehiculo_id: string;
  mecanico_master_id: string;
  modalidad: "preventivo" | "correctivo" | "diagnostico" | "soldadura";
  urgencia: "alta" | "media" | "baja";
  monto_estimado: string;
  costo_mano_obra: string | null;
  cobro_confirmado: boolean;
  cliente_aprobo_lista: boolean;
  lista_repuestos: RepuestoItem[];
  created_at: string;
}

// Catálogo de vehículos sembrados en Nivel 2 para mapear nombres y placas en UI
const VEHICULOS_MAP: Record<string, { vehiculo: string; placa: string }> = {
  "4c51988a-e773-42a5-b06a-54c2a5737d62": { vehiculo: "TVS King Deluxe", placa: "1234-5A" },
  "c71f461f-3680-4f20-ab53-092340270563": { vehiculo: "Bajaj Torito 2D", placa: "9876-2B" },
  "ebebd8c7-b7b1-4ba3-a0ec-aa593fd8e59b": { vehiculo: "Bajaj Torito Chrome", placa: "4532-8C" },
  "049e30f5-4b6b-4368-a93a-e092d79cacc0": { vehiculo: "Pulsar 200 NS", placa: "XW-9021" },
  "adcdd013-46c4-4015-b09c-3313cc2a6b4c": { vehiculo: "TVS King Deluxe (Rural)", placa: "6543-1A" },
  "c392460b-d4c7-4073-a2a9-1fadb284b479": { vehiculo: "Bajaj Torito 2D (Distrito)", placa: "9876-2B" },
  "355c2f9c-0cd2-400b-a4e9-ea625a9bec9c": { vehiculo: "Bajaj Torito Chrome (Distrito)", placa: "4532-8C" },
  "30d82bc9-7674-4248-aa37-efd5e8348633": { vehiculo: "Pulsar 200 NS (Rural)", placa: "XW-9021" },
  "bf53abe9-5302-482e-925a-28112e9105e8": { vehiculo: "Honda CB Persist Test", placa: "HO-9999" }
};

const SEEDED_OT_IDS = [
  "1c01f7c3-0a60-4f29-b04c-4b4cd93033f6",
  "69808868-efce-41fb-b947-3ba15492823e",
  "475b2714-881b-48f0-a302-c573e5d8bf70",
  "64b4d800-3e6a-4246-8fee-5bb9d37e7284",
  "deaa378f-e02a-4008-be20-e3080b637fbb",
  "1d66dd33-b608-4f16-a016-89018281fefc",
  "f863da0d-6599-425c-b77b-55636ba8b53e",
  "5c45a480-2970-4689-b5d2-7c2812131b99"
];

export default function TallerPage() {
  const { user, accessToken, logout } = useAuth();

  const [otIds, setOtIds] = useState<string[]>([]);
  const [ordenes, setOrdenes] = useState<BackendOT[]>([]);
  const [selectedOT, setSelectedOT] = useState<BackendOT | null>(null);

  // Loading, Errors, and Action flags
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVehiculoId, setNewVehiculoId] = useState("4c51988a-e773-42a5-b06a-54c2a5737d62");
  const [newModalidad, setNewModalidad] = useState<"preventivo" | "correctivo" | "diagnostico" | "soldadura">("correctivo");
  const [newUrgencia, setNewUrgencia] = useState<"alta" | "media" | "baja">("media");

  // Action input states
  const [nuevoRepuestoCodigo, setNuevoRepuestoCodigo] = useState("");
  const [nuevoRepuestoCantidad, setNuevoRepuestoCantidad] = useState(1);
  const [costoManoObra, setCostoManoObra] = useState("50.00");
  const [montoPagado, setMontoPagado] = useState("0.00");
  const [plazoDias, setPlazoDias] = useState(30);

  // Initialize OT IDs from session/local storage or seed
  useEffect(() => {
    const stored = localStorage.getItem("santi_workshop_ot_ids");
    if (stored) {
      try {
        setOtIds(JSON.parse(stored));
      } catch {
        setOtIds(SEEDED_OT_IDS);
      }
    } else {
      setOtIds(SEEDED_OT_IDS);
    }
  }, []);

  // Sync state back to local storage
  useEffect(() => {
    if (otIds.length > 0) {
      localStorage.setItem("santi_workshop_ot_ids", JSON.stringify(otIds));
    }
  }, [otIds]);

  // Parallel fetching of all workshop orders
  const fetchAllOTs = useCallback(async () => {
    if (!accessToken) {
      setError("Autenticación requerida. Por favor, inicia sesión.");
      setLoading(false);
      return;
    }
    if (otIds.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const fetchPromises = otIds.map(async (id) => {
        const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${id}`, { headers });
        if (!res.ok) {
          throw new Error(`${res.status}`);
        }
        const body = await res.json();
        return body.data as BackendOT;
      });

      const results = await Promise.allSettled(fetchPromises);
      const successfulOTs = results
        .filter((r) => r.status === "fulfilled")
        .map((r) => (r as PromiseFulfilledResult<BackendOT>).value);

      setOrdenes(successfulOTs);

      // Keep selected OT detail updated in real-time
      if (selectedOT) {
        const updated = successfulOTs.find((o) => o.ot_id === selectedOT.ot_id);
        if (updated) {
          setSelectedOT(updated);
        }
      }
    } catch (err) {
      console.error("Error fetching OTs:", err);
      if (err instanceof Error && err.message.includes("403")) {
        setError("403 | No tienes permisos para ver la consola de taller (RBAC).");
      } else {
        setError("Error al cargar las órdenes de trabajo desde PostgreSQL.");
      }
    } finally {
      setLoading(false);
    }
  }, [accessToken, otIds, selectedOT]);

  useEffect(() => {
    if (accessToken && otIds.length > 0) {
      fetchAllOTs();
    }
  }, [accessToken, otIds, fetchAllOTs]);

  // EP-TAL-01: Abrir Orden de Trabajo
  const handleCrearOT = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch("/api-proxy/v1/ordenes-trabajo", {
        method: "POST",
        headers,
        body: JSON.stringify({
          vehiculo_id: newVehiculoId,
          mecanico_master_id: "807af7ef-3972-4a2d-83a3-82fed233a5d4", // Seed master mechanic
          modalidad: newModalidad,
          urgencia: newUrgencia,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.message || "No autorizado para abrir órdenes de trabajo.";
        throw new Error(`${res.status} | ${msg}`);
      }

      const nuevaOT = body.data as BackendOT;
      setOtIds((prev) => [nuevaOT.ot_id, ...prev]);
      setShowCreateModal(false);
      setSelectedOT(nuevaOT);
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al abrir la OT");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-02: Agregar Repuesto a Orden de Trabajo
  const handleAgregarRepuesto = async () => {
    if (!selectedOT || !accessToken || !nuevoRepuestoCodigo || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/repuestos`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          codigo: nuevoRepuestoCodigo.trim().toUpperCase(),
          cantidad: nuevoRepuestoCantidad,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.error?.message || body.detail?.message || "Error al agregar repuesto.";
        throw new Error(`${res.status} | ${msg}`);
      }

      setNuevoRepuestoCodigo("");
      setNuevoRepuestoCantidad(1);
      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al registrar repuesto");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-03: Aprobar lista inicial de repuestos (Avanza a EN_EJECUCION)
  const handleAprobarLista = async () => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/aprobar-lista`, {
        method: "POST",
        headers,
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.message || "Error al aprobar la lista.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al aprobar la lista");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-04: Confirmar Costo Adicional Manual (Aprobación explícita por ítem)
  const handleAprobarAdicional = async (itemId: string) => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/confirmar-adicional`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          item_id: itemId,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.message || "Error al aprobar costo adicional.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al aprobar costo adicional");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-06: Declarar revisión final (Mecánico Maestro declara mano de obra y termina)
  const handleRevisionFinal = async () => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/revision-final`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          costo_mano_obra: parseFloat(costoManoObra) || 0,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.error?.message || body.detail?.message || "Error en revisión final.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al declarar revisión final");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-07: Registrar cobro parcial (Enfrenta el umbral del 80%)
  const handleCobroParcial = async () => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/cobro-parcial`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          monto_pagado: parseFloat(montoPagado) || 0,
          plazo_dias: plazoDias,
        }),
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.error?.message || body.detail?.message || "Error al registrar el cobro.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al registrar cobro");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-08: Cerrar Orden de Trabajo
  const handleCerrarOT = async () => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/cerrar`, {
        method: "POST",
        headers,
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.error?.message || body.detail?.message || "Error al cerrar OT.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al cerrar OT");
    } finally {
      setSubmitting(false);
    }
  };

  // EP-TAL-10: Liberar Vehículo
  const handleLiberarVehiculo = async () => {
    if (!selectedOT || !accessToken || submitting) return;

    setSubmitting(true);
    setActionError(null);
    try {
      const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`,
      };

      const res = await fetch(`/api-proxy/v1/ordenes-trabajo/${selectedOT.ot_id}/liberar-vehiculo`, {
        method: "POST",
        headers,
      });

      const body = await res.json();
      if (!res.ok) {
        const msg = body.detail?.error?.message || body.detail?.message || "Error al liberar vehículo.";
        throw new Error(`${res.status} | ${msg}`);
      }

      await fetchAllOTs();
    } catch (err) {
      console.error(err);
      setActionError(err instanceof Error ? err.message : "Error al liberar vehículo");
    } finally {
      setSubmitting(false);
    }
  };

  // Helper arrays for Kanban Board columns filtering
  const getColumna = (colName: "Abierta" | "EnProgreso" | "Revision" | "Cerrada") => {
    return ordenes.filter((ot) => {
      if (colName === "Abierta") return ot.estado === "ABIERTA" || ot.estado === "LISTA_REPUESTOS";
      if (colName === "EnProgreso") return ot.estado === "EN_EJECUCION";
      if (colName === "Revision") return ot.estado === "REVISION_FINAL";
      return ot.estado === "CERRADA" || ot.estado === "CANCELADA";
    });
  };

  // Check RBAC permissions for the logged-in role
  const isVendedor = user?.rol === "VENDEDOR";
  const isMecanico = user?.rol === "MECANICO_MASTER" || user?.rol === "MECANICO_JUNIOR";
  const isAdmin = user?.rol === "ADMINISTRADOR" || user?.rol === "SUPERADMIN";

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen bg-slate-950 text-slate-100">
        <div className="w-12 h-12 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-400 text-sm mt-4 font-medium font-display">
          Cargando Órdenes de Trabajo desde PostgreSQL...
        </p>
      </div>
    );
  }

  // 403 Block Panel for Unauthorized Roles (like Client Roles attempting to enter internal zone)
  if (error && (error.includes("403") || !["SUPERADMIN", "ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR"].includes(user?.rol || ""))) {
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
              No dispones de los permisos internos requeridos para operar en el taller.
            </p>
          </div>
          <div className="bg-slate-950 border border-slate-850 p-4 rounded-2xl text-left space-y-1.5">
            <p className="text-xs text-slate-500">
              Usuario ID: <span className="font-mono text-slate-300 font-bold">{user?.id || "Desconocido"}</span>
            </p>
            <p className="text-xs text-slate-500">
              Rol Asignado: <span className="font-mono text-amber-500 font-bold">{user?.rol || "Ninguno"}</span>
            </p>
          </div>
          <div className="flex flex-col gap-2 pt-2">
            <Link
              href="/"
              className="bg-slate-800 hover:bg-slate-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors"
            >
              Volver al Catálogo Público
            </Link>
            <button
              onClick={() => logout()}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors font-medium underline"
            >
              Cerrar sesión e iniciar con otra cuenta
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-950 text-slate-100 min-h-screen font-body">
      {/* Header navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <Link href="/" className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white font-display font-bold text-base shadow-sm hover:bg-teal-700 transition-colors">
            S
          </Link>
          <div>
            <span className="font-display font-bold text-white tracking-wide block leading-tight">
              Consola Operativa de Taller
            </span>
            <span className="text-[9px] text-teal-400 font-mono uppercase tracking-wider">
              Nivel 2 PostgreSQL · Conexión Establecida
            </span>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white text-xs px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <span>+</span> Abrir OT
          </button>
          <div className="text-right text-xs border-l border-slate-800 pl-4">
            <p className="font-bold text-slate-200 font-display">{user?.id.split("@")[0]}</p>
            <p className="text-slate-500 font-mono text-[9px] uppercase tracking-wider">{user?.rol}</p>
          </div>
          <button
            onClick={() => logout()}
            className="bg-slate-800 hover:bg-slate-750 text-slate-300 text-xs px-2.5 py-1.5 rounded-lg border border-slate-700 font-medium transition-colors"
          >
            Cerrar Sesión
          </button>
        </div>
      </header>

      <main className="flex-1 px-6 py-8 flex flex-col gap-6 max-w-7xl mx-auto w-full">
        <div>
          <h2 className="text-3xl font-display font-bold text-white">Tablero de Órdenes de Trabajo (OT)</h2>
          <p className="text-slate-400 text-sm mt-1">
            Asigna reparaciones, registra consumo de repuestos y coordina pagos en tiempo real.
          </p>
        </div>

        {/* Global Error Banner */}
        {actionError && (
          <div className="p-4 bg-rose-950/30 border border-rose-900/40 text-rose-300 rounded-2xl text-xs flex justify-between items-center animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="text-sm">⚠️</span>
              <p>
                <span className="font-bold">Error de dominio / validación:</span> {actionError}
              </p>
            </div>
            <button
              onClick={() => setActionError(null)}
              className="text-rose-400 hover:text-white font-bold ml-4"
            >
              ✕
            </button>
          </div>
        )}

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          
          {/* Column Abiertas */}
          <div className="bg-slate-900/50 border border-slate-850 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>📂 Abiertas / Repuestos</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Abierta").length}</span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {getColumna("Abierta").map((ot) => {
                const info = VEHICULOS_MAP[ot.vehiculo_id] || { vehiculo: "Modelo Genérico", placa: "SEED-NUEVA" };
                return (
                  <div
                    key={ot.ot_id}
                    onClick={() => { setSelectedOT(ot); setActionError(null); }}
                    className={`bg-slate-900 border p-4 rounded-xl cursor-pointer transition-all space-y-3 ${
                      selectedOT?.ot_id === ot.ot_id ? "border-teal-500 bg-slate-900/80 shadow-md shadow-teal-500/5" : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] font-bold text-teal-400 truncate max-w-[120px]">{ot.ot_id.slice(0, 8)}...</span>
                      <span className="font-mono text-[9px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded uppercase">{ot.estado.replace("_", " ")}</span>
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">{info.vehiculo}</h4>
                      <p className="text-[10px] font-mono text-slate-500 mt-0.5">Placa: {info.placa}</p>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-400 pt-2 border-t border-slate-850">
                      <span>Urgencia: <span className={`font-semibold ${ot.urgencia === "alta" ? "text-rose-400" : "text-slate-300"}`}>{ot.urgencia}</span></span>
                      <span className="font-mono font-bold text-slate-300">S/ {parseFloat(ot.monto_estimado).toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column En Progreso */}
          <div className="bg-slate-900/50 border border-slate-850 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>⚙️ En Progreso</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("EnProgreso").length}</span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {getColumna("EnProgreso").map((ot) => {
                const info = VEHICULOS_MAP[ot.vehiculo_id] || { vehiculo: "Modelo Genérico", placa: "SEED-NUEVA" };
                const tienePendientes = ot.lista_repuestos.some(i => i.aprobacion === "PENDIENTE_ADICIONAL" && i.tramo === "manual");
                return (
                  <div
                    key={ot.ot_id}
                    onClick={() => { setSelectedOT(ot); setActionError(null); }}
                    className={`bg-slate-900 border p-4 rounded-xl cursor-pointer transition-all space-y-3 ${
                      selectedOT?.ot_id === ot.ot_id 
                        ? "border-teal-500 bg-slate-900/80 shadow-md shadow-teal-500/5" 
                        : tienePendientes 
                        ? "border-amber-600/40 hover:border-amber-500 animate-pulse" 
                        : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] font-bold text-teal-400 truncate max-w-[120px]">{ot.ot_id.slice(0, 8)}...</span>
                      {tienePendientes && (
                        <span className="text-[9px] bg-amber-950/50 border border-amber-900/40 text-amber-400 px-1.5 py-0.5 rounded font-semibold animate-pulse">
                          Aprobar Adicional
                        </span>
                      )}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">{info.vehiculo}</h4>
                      <p className="text-[10px] font-mono text-slate-500 mt-0.5">Placa: {info.placa}</p>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-400 pt-2 border-t border-slate-850">
                      <span>Mod: <span className="font-semibold text-slate-300">{ot.modalidad}</span></span>
                      <span className="font-mono font-bold text-slate-300">S/ {parseFloat(ot.monto_estimado).toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column Revisión Final */}
          <div className="bg-slate-900/50 border border-slate-850 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>⚠️ Revisión Final</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Revision").length}</span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {getColumna("Revision").map((ot) => {
                const info = VEHICULOS_MAP[ot.vehiculo_id] || { vehiculo: "Modelo Genérico", placa: "SEED-NUEVA" };
                const total = parseFloat(ot.monto_estimado) + parseFloat(ot.costo_mano_obra || "0");
                return (
                  <div
                    key={ot.ot_id}
                    onClick={() => { setSelectedOT(ot); setActionError(null); }}
                    className={`bg-slate-900 border p-4 rounded-xl cursor-pointer transition-all space-y-3 ${
                      selectedOT?.ot_id === ot.ot_id 
                        ? "border-teal-500 bg-slate-900/80 shadow-md shadow-teal-500/5" 
                        : ot.cobro_confirmado 
                        ? "border-emerald-600/30 bg-emerald-950/5 hover:border-emerald-500/40" 
                        : "border-purple-600/20 hover:border-purple-500/30 bg-purple-950/5"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] font-bold text-purple-400 truncate max-w-[120px]">{ot.ot_id.slice(0, 8)}...</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-semibold border ${
                        ot.cobro_confirmado 
                          ? "bg-emerald-950/50 border-emerald-900/40 text-emerald-400" 
                          : "bg-purple-950/50 border-purple-900/40 text-purple-400"
                      }`}>
                        {ot.cobro_confirmado ? "PAGADO (≥80%)" : "PENDIENTE COBRO"}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">{info.vehiculo}</h4>
                      <p className="text-[10px] font-mono text-slate-500 mt-0.5">Placa: {info.placa}</p>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-400 pt-2 border-t border-slate-850">
                      <span>Total final:</span>
                      <span className="font-mono font-bold text-white">S/ {total.toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column Cerradas */}
          <div className="bg-slate-900/50 border border-slate-850 rounded-2xl p-4 space-y-4">
            <h3 className="font-display font-bold text-sm text-slate-400 uppercase tracking-wider flex items-center justify-between">
              <span>✅ Cerradas / Canceladas</span>
              <span className="bg-slate-800 text-xs px-2 py-0.5 rounded-full">{getColumna("Cerrada").length}</span>
            </h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {getColumna("Cerrada").map((ot) => {
                const info = VEHICULOS_MAP[ot.vehiculo_id] || { vehiculo: "Modelo Genérico", placa: "SEED-NUEVA" };
                const total = parseFloat(ot.monto_estimado) + parseFloat(ot.costo_mano_obra || "0");
                return (
                  <div
                    key={ot.ot_id}
                    onClick={() => { setSelectedOT(ot); setActionError(null); }}
                    className={`bg-slate-900/40 border p-4 rounded-xl cursor-pointer opacity-70 hover:opacity-100 transition-all space-y-3 ${
                      selectedOT?.ot_id === ot.ot_id ? "border-slate-600 bg-slate-900/60" : "border-slate-950"
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-mono text-[10px] font-bold text-slate-500 truncate max-w-[120px]">{ot.ot_id.slice(0, 8)}...</span>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                        ot.estado === "CERRADA" ? "bg-slate-800 text-slate-400" : "bg-rose-950/20 text-rose-500"
                      }`}>
                        {ot.estado}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400">{info.vehiculo}</h4>
                      <p className="text-[10px] font-mono text-slate-600 mt-0.5">Placa: {info.placa}</p>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-500 pt-2 border-t border-slate-900">
                      <span>Costo Final:</span>
                      <span className="font-mono font-bold text-slate-400">S/ {total.toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* Selected OT Split Detail Panel */}
        {selectedOT ? (
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col lg:flex-row justify-between gap-8 shadow-xl animate-fadeIn">
            
            {/* Left section: details, state timeline and list of repuestos */}
            <div className="flex-1 space-y-6">
              <div className="flex justify-between items-center border-b border-slate-800 pb-4">
                <div>
                  <h3 className="font-display font-bold text-lg text-white">Detalle de la Orden</h3>
                  <p className="text-slate-500 font-mono text-[11px] mt-0.5">UUID: {selectedOT.ot_id}</p>
                </div>
                <button
                  onClick={() => setSelectedOT(null)}
                  className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-750 px-3 py-1 rounded-xl text-xs transition-colors"
                >
                  Cerrar panel
                </button>
              </div>

              {/* Grid fields */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-950/50 border border-slate-850 p-4 rounded-2xl text-xs">
                <div>
                  <p className="text-slate-500">Vehículo</p>
                  <p className="font-semibold text-slate-200 mt-0.5">
                    {VEHICULOS_MAP[selectedOT.vehiculo_id]?.vehiculo || "Modelo Genérico"}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Placa</p>
                  <p className="font-mono font-semibold text-slate-200 mt-0.5">
                    {VEHICULOS_MAP[selectedOT.vehiculo_id]?.placa || "SEED-NUEVA"}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Urgencia</p>
                  <p className={`font-semibold mt-0.5 uppercase text-[10px] ${selectedOT.urgencia === "alta" ? "text-rose-400" : "text-amber-500"}`}>
                    {selectedOT.urgencia}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500">Estado Actual</p>
                  <p className="font-semibold text-teal-400 mt-0.5 font-mono uppercase text-[10px]">
                    {selectedOT.estado.replace("_", " ")}
                  </p>
                </div>
              </div>

              {/* Repuestos table/list */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h4 className="font-display font-bold text-sm text-slate-200">Lista de Repuestos Cargados</h4>
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2.5 py-0.5 rounded-full font-mono">
                    {selectedOT.lista_repuestos.length} repuestos
                  </span>
                </div>
                {selectedOT.lista_repuestos.length > 0 ? (
                  <div className="bg-slate-950 border border-slate-850 rounded-2xl overflow-hidden">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-900 border-b border-slate-850 text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                          <th className="py-2.5 px-4 font-mono">Código</th>
                          <th className="py-2.5 px-4 text-center">Cant</th>
                          <th className="py-2.5 px-4 text-right">P. Unit</th>
                          <th className="py-2.5 px-4 text-right">Subtotal</th>
                          <th className="py-2.5 px-4 text-center">Aprobación Cliente</th>
                          <th className="py-2.5 px-4 text-center">Acción</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-850 text-slate-300 font-mono">
                        {selectedOT.lista_repuestos.map((item) => {
                          const sub = parseFloat(item.precio_unitario) * item.cantidad;
                          const esManual = item.tramo === "manual" && item.aprobacion === "PENDIENTE_ADICIONAL";
                          return (
                            <tr key={item.item_id} className="hover:bg-slate-900/40">
                              <td className="py-3 px-4 font-bold text-slate-200">{item.codigo}</td>
                              <td className="py-3 px-4 text-center">{item.cantidad}</td>
                              <td className="py-3 px-4 text-right">S/ {parseFloat(item.precio_unitario).toFixed(2)}</td>
                              <td className="py-3 px-4 text-right font-bold">S/ {sub.toFixed(2)}</td>
                              <td className="py-3 px-4 text-center">
                                <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-semibold tracking-wider ${
                                  item.aprobacion.startsWith("APROBADO") 
                                    ? "bg-emerald-950/60 border border-emerald-900/50 text-emerald-400"
                                    : item.aprobacion === "RECHAZADO"
                                    ? "bg-rose-950/60 border border-rose-900/50 text-rose-400"
                                    : "bg-amber-950/60 border border-amber-900/50 text-amber-400 animate-pulse"
                                }`}>
                                  {item.aprobacion.replace("_", " ")}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-center">
                                {esManual ? (
                                  <button
                                    onClick={() => handleAprobarAdicional(item.item_id)}
                                    disabled={submitting || (!isVendedor && !isAdmin)}
                                    title={(!isVendedor && !isAdmin) ? "Solo Vendedor o Administrador pueden aprobar costos adicionales" : "Aprobar costo adicional manualmente"}
                                    className="bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-medium text-[10px] px-2 py-1 rounded transition-colors"
                                  >
                                    Aprobar S/ {sub.toFixed(2)}
                                  </button>
                                ) : (
                                  <span className="text-slate-600 text-[10px]">-</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic p-4 bg-slate-950/30 border border-slate-850 rounded-2xl text-center">
                    No hay ningún repuesto cargado en esta orden de trabajo todavía.
                  </p>
                )}
              </div>
            </div>

            {/* Right section: Action Panels configured for specific states and RBAC constraints */}
            <div className="w-full lg:w-96 bg-slate-950 border border-slate-850 rounded-2xl p-5 flex flex-col justify-between shadow-inner space-y-6">
              
              <div className="space-y-4">
                <h4 className="font-display font-bold text-sm text-slate-200 border-b border-slate-850 pb-2">
                  Acciones de Negocio
                </h4>

                {/* 1. Add Repuesto Form (State ABIERTA or EN_EJECUCION) */}
                {(selectedOT.estado === "ABIERTA" || selectedOT.estado === "EN_EJECUCION") && (
                  <div className="space-y-3 p-3 bg-slate-900/60 border border-slate-850 rounded-xl">
                    <p className="text-xs font-bold text-teal-400">⚡ Cargar Repuesto a OT</p>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="col-span-2">
                        <input
                          type="text"
                          placeholder="Cód. Repuesto (Ej: SEED-000)"
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-teal-500 text-xs bg-slate-950 text-white"
                          value={nuevoRepuestoCodigo}
                          onChange={(e) => setNuevoRepuestoCodigo(e.target.value)}
                        />
                      </div>
                      <div>
                        <input
                          type="number"
                          min={1}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-teal-500 text-xs bg-slate-950 text-white"
                          value={nuevoRepuestoCantidad}
                          onChange={(e) => setNuevoRepuestoCantidad(parseInt(e.target.value) || 1)}
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleAgregarRepuesto}
                      disabled={submitting || !nuevoRepuestoCodigo}
                      className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium py-1.5 rounded-lg text-xs transition-colors flex justify-center items-center gap-1.5"
                    >
                      {submitting ? "Procesando..." : "+ Cargar Repuesto"}
                    </button>
                    <p className="text-[9px] text-slate-500 leading-normal">
                      * En ejecución, los repuestos &gt; S/100 requerirán aprobación manual de VENDEDOR.
                    </p>
                  </div>
                )}

                {/* 2. Approve List (State ABIERTA or LISTA_REPUESTOS) */}
                {(selectedOT.estado === "ABIERTA" || selectedOT.estado === "LISTA_REPUESTOS") && (
                  <div className="space-y-2.5 p-3 bg-slate-900/60 border border-slate-850 rounded-xl">
                    <p className="text-xs font-bold text-teal-400">📋 Formalización de Lista</p>
                    <p className="text-[10px] text-slate-400 leading-normal">
                      Aprobar la lista inicial de repuestos del taller y comenzar la ejecución técnica.
                    </p>
                    <button
                      onClick={handleAprobarLista}
                      disabled={submitting || (!isVendedor && !isAdmin) || selectedOT.lista_repuestos.length === 0}
                      title={(!isVendedor && !isAdmin) ? "Acción exclusiva para Vendedor o Admin" : selectedOT.lista_repuestos.length === 0 ? "Agrega repuestos primero" : "Aprobar y pasar a En Progreso"}
                      className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-800 disabled:text-slate-500 disabled:opacity-60 text-white font-medium py-2 rounded-lg text-xs transition-colors"
                    >
                      {(!isVendedor && !isAdmin) ? "Aprobación Reservada a Vendedores" : "Aprobar Lista → Iniciar Trabajo"}
                    </button>
                  </div>
                )}

                {/* 3. Revision Final (State EN_EJECUCION) */}
                {selectedOT.estado === "EN_EJECUCION" && (
                  <div className="space-y-3 p-3 bg-slate-900/60 border border-slate-850 rounded-xl">
                    <p className="text-xs font-bold text-purple-400">🛠️ Finalizar Reparaciones</p>
                    <div className="space-y-1.5">
                      <label className="text-[10px] text-slate-400">Costo Mano de Obra (S/.)</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        className="w-full px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-purple-500 text-xs bg-slate-950 text-white font-mono"
                        value={costoManoObra}
                        onChange={(e) => setCostoManoObra(e.target.value)}
                      />
                    </div>
                    <button
                      onClick={handleRevisionFinal}
                      disabled={submitting || (!isMecanico && !isAdmin)}
                      title={(!isMecanico && !isAdmin) ? "Solo los mecánicos declaran la mano de obra" : "Declarar finalización de trabajo técnico"}
                      className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-slate-800 disabled:text-slate-500 disabled:opacity-60 text-white font-medium py-2 rounded-lg text-xs transition-colors"
                    >
                      {(!isMecanico && !isAdmin) ? "Reservado para Mecánico Maestro" : "Declarar Revisión Final → Terminar Trabajo"}
                    </button>
                  </div>
                )}

                {/* 4. Cobro Parcial (State REVISION_FINAL) */}
                {selectedOT.estado === "REVISION_FINAL" && (
                  <div className="space-y-3 p-3 bg-slate-900/60 border border-slate-850 rounded-xl border-purple-900/30">
                    <p className="text-xs font-bold text-emerald-400">💰 Registro de Cobro Parcial</p>
                    
                    {!isAdmin && (
                      <div className="p-2 bg-amber-950/20 border border-amber-900/20 text-amber-400 rounded-lg text-[10px]">
                        🔒 Solo los roles de <span className="font-bold">Administrador</span> pueden registrar cobros parciales de taller.
                      </div>
                    )}

                    <div className="space-y-2 text-xs">
                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400">Monto Cobrado (S/.)</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          disabled={!isAdmin}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-emerald-500 text-xs bg-slate-950 text-white font-mono"
                          value={montoPagado}
                          onChange={(e) => setMontoPagado(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] text-slate-400">Plazo en días (si hay deuda)</label>
                        <input
                          type="number"
                          disabled={!isAdmin}
                          className="w-full px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-emerald-500 text-xs bg-slate-950 text-white font-mono"
                          value={plazoDias}
                          onChange={(e) => setPlazoDias(parseInt(e.target.value) || 30)}
                        />
                      </div>
                    </div>
                    
                    <button
                      onClick={handleCobroParcial}
                      disabled={submitting || !isAdmin}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white font-medium py-2 rounded-lg text-xs transition-colors"
                    >
                      Registrar Pago
                    </button>
                    <p className="text-[9px] text-slate-500 leading-normal">
                      * Criterio Elena: El pago registrado debe ser al menos el <span className="font-bold text-slate-400">80%</span> del costo total para autorizar el cierre.
                    </p>
                  </div>
                )}

                {/* 5. Cerrar OT (State REVISION_FINAL and cobro_confirmado = True) */}
                {selectedOT.estado === "REVISION_FINAL" && selectedOT.cobro_confirmado && (
                  <div className="space-y-2 p-3 bg-slate-900/60 border border-slate-850 rounded-xl">
                    <p className="text-xs font-bold text-teal-400">🔒 Cierre de Orden</p>
                    <p className="text-[10px] text-slate-400 leading-normal">
                      El pago ya cumple con las normativas (≥80%). Cierra la orden de trabajo para formalizar los costos y procesar los inventarios.
                    </p>
                    <button
                      onClick={handleCerrarOT}
                      disabled={submitting || (!isMecanico && !isAdmin)}
                      className="w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-xs transition-colors"
                    >
                      Cerrar Orden y Guardar Historial
                    </button>
                  </div>
                )}

                {/* 6. Liberar Vehículo (State CERRADA) */}
                {selectedOT.estado === "CERRADA" && (
                  <div className="space-y-2 p-3 bg-slate-900/60 border border-slate-850 rounded-xl">
                    <p className="text-xs font-bold text-emerald-400">🚗 Entrega y Salida</p>
                    <p className="text-[10px] text-slate-400 leading-normal">
                      La orden está cerrada. Registra la prueba de ruta y autoriza la salida del vehículo del taller.
                    </p>
                    <button
                      onClick={handleLiberarVehiculo}
                      disabled={submitting || (!isMecanico && !isAdmin)}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-xs transition-colors"
                    >
                      Liberar Vehículo y Cerrar Entrada
                    </button>
                  </div>
                )}

              </div>

              {/* Costs summary breakdown */}
              <div className="pt-4 border-t border-slate-800/80 space-y-3 font-mono text-xs">
                <div className="flex justify-between text-slate-400">
                  <span>Repuestos Estimados:</span>
                  <span className="text-slate-200">S/ {parseFloat(selectedOT.monto_estimado).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Mano de Obra:</span>
                  <span className="text-slate-200">S/ {parseFloat(selectedOT.costo_mano_obra || "0").toFixed(2)}</span>
                </div>
                
                <div className="pt-3 border-t border-slate-900 flex justify-between items-end">
                  <span className="text-slate-300 font-bold font-display">Costo Total:</span>
                  <span className="text-base font-bold text-white">
                    S/ {(parseFloat(selectedOT.monto_estimado) + parseFloat(selectedOT.costo_mano_obra || "0")).toFixed(2)}
                  </span>
                </div>

                <div className="pt-2 flex justify-between items-center text-[10px]">
                  <span className="text-slate-500">Cobro Autorizado:</span>
                  <span className={`font-semibold ${selectedOT.cobro_confirmado ? "text-emerald-400" : "text-rose-400"}`}>
                    {selectedOT.cobro_confirmado ? "SÍ (Autorizado)" : "NO (Bloqueado)"}
                  </span>
                </div>
              </div>

            </div>
          </div>
        ) : null}

      </main>

      {/* Modal for creating a new Workshop Order (EP-TAL-01) */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 animate-fadeIn">
          <form
            onSubmit={handleCrearOT}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-6"
          >
            <div className="flex justify-between items-center">
              <h3 className="font-display font-bold text-lg text-white">
                Abrir Nueva Orden de Trabajo
              </h3>
              <button
                type="button"
                onClick={() => {
                  setShowCreateModal(false);
                  setActionError(null);
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs text-slate-400 font-medium block">
                  Seleccionar Vehículo Ingresado
                </label>
                <select
                  required
                  className="w-full px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white font-mono"
                  value={newVehiculoId}
                  onChange={(e) => setNewVehiculoId(e.target.value)}
                >
                  {Object.entries(VEHICULOS_MAP).map(([id, info]) => (
                    <option key={id} value={id}>
                      {info.vehiculo} ({info.placa})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs text-slate-400 font-medium block">
                    Modalidad
                  </label>
                  <select
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                    value={newModalidad}
                    onChange={(e) => setNewModalidad(e.target.value as "preventivo" | "correctivo" | "diagnostico" | "soldadura")}
                  >
                    <option value="correctivo">Correctivo</option>
                    <option value="preventivo">Preventivo</option>
                    <option value="diagnostico">Diagnóstico</option>
                    <option value="soldadura">Soldadura</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-slate-400 font-medium block">
                    Nivel Urgencia
                  </label>
                  <select
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-800 focus:outline-none focus:border-teal-500 text-sm bg-slate-950 text-white"
                    value={newUrgencia}
                    onChange={(e) => setNewUrgencia(e.target.value as "alta" | "media" | "baja")}
                  >
                    <option value="alta">Alta</option>
                    <option value="media">Media</option>
                    <option value="baja">Baja</option>
                  </select>
                </div>
              </div>

              <div className="p-3 bg-slate-950 rounded-2xl border border-slate-850 text-[11px] text-slate-500 leading-normal">
                * Asignado automáticamente a Samuel Ramos (Mecánico Maestro) de turno en el sistema.
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setShowCreateModal(false);
                  setActionError(null);
                }}
                className="flex-1 bg-slate-800 hover:bg-slate-750 text-slate-300 font-medium py-2.5 rounded-xl text-xs transition-colors border border-slate-700"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-medium py-2.5 rounded-xl text-xs transition-colors shadow-sm"
              >
                {submitting ? "Creando..." : "Abrir OT"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
