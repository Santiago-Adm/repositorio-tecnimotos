"""
EP-OBS-02: GET /v1/privacidad — Política de privacidad ANPDP (08 §8.1 Legal).
Conforme a Ley N.° 29733 (Protección de Datos Personales — Perú).
Completar campos marcados con [PENDIENTE] antes del deploy a producción.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/v1", tags=["legal"])


@router.get("/privacidad", summary="EP-OBS-02: Política de privacidad")
async def politica_privacidad(request: Request) -> dict:
    return {
        "responsable": {
            "nombre": "Tecnimotos Santi",
            "ruc": "[PENDIENTE — completar antes de deploy]",
            "direccion": "Ayacucho, Perú",
            "contacto_arco": "san25level@gmail.com",
            "registro_anpdp": "[PENDIENTE — número de registro ANPDP tras inscripción]",
        },
        "finalidad": [
            "Gestión de pedidos y reservas de repuestos",
            "Emisión de comprobantes de pago",
            "Registro y seguimiento de órdenes de trabajo (taller)",
            "Comunicación de estado de pedidos por WhatsApp",
            "Cumplimiento de obligaciones tributarias (SUNAT)",
        ],
        "derechos_arco": {
            "descripcion": "Acceso, Rectificación, Cancelación y Oposición — Ley N.° 29733",
            "canal": "san25level@gmail.com",
            "plazo_respuesta_dias": 20,
        },
        "retencion_datos": {
            "datos_transaccionales": "5 años (obligación tributaria — Código Tributario art. 87)",
            "datos_personales_cliente": "2 años tras la última operación",
            "registros_taller": "3 años",
        },
        "transferencias_terceros": [
            {
                "receptor": "SUNAT",
                "finalidad": "Cumplimiento tributario — D.L. N.° 943",
            },
            {
                "receptor": "Meta (WhatsApp Business)",
                "finalidad": "Notificaciones de estado de pedido y alertas de stock",
            },
            {
                "receptor": "Twilio",
                "finalidad": "Notificaciones SMS de estado de pedido",
            },
        ],
        "consentimiento": {
            "requerido": True,
            "mecanismo": "Checkbox explícito no premarcado en flujo de registro",
            "revocable": True,
            "canal_revocacion": "san25level@gmail.com",
        },
        "version": "1.0",
        "vigente_desde": "2026-06-21",
        "proxima_revision": "2027-06-21",
    }
