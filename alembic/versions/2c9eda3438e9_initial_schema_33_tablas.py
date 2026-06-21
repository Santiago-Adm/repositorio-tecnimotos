"""initial_schema_33_tablas

Revision ID: 2c9eda3438e9
Revises:
Create Date: 2026-06-21

Crea las 33 tablas declaradas en 03 §5.2-§5.8 en orden topológico.
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2c9eda3438e9"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # 1. usuario
    op.create_table("usuario",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("rol", sa.String(30), nullable=False),
        sa.Column("sub_rol", sa.String(30), nullable=True),
        sa.Column("mfa_secret", sa.Text, nullable=True),
        sa.Column("mfa_habilitado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("token_version", sa.Integer, nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rol IN ('SUPERADMIN','ADMINISTRADOR','VENDEDOR','MECANICO_MASTER','MECANICO_JUNIOR','CLIENTE_CONDUCTOR','CLIENTE_DISTRITO','CLIENTE_RURAL','CLIENTE_FLOTA_DUENO','CLIENTE_FLOTA_CONDUCTOR','CLIENTE_MOTOLINEAL')", name="chk_usuario_rol"),
    )
    op.create_index("idx_usuario_rol", "usuario", ["rol"])
    op.create_index("idx_usuario_activo", "usuario", ["activo"])

    # 2. repuesto
    op.create_table("repuesto",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("codigo", sa.String(50), unique=True, nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False, server_default=""),
        sa.Column("universo", sa.String(20), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("año", sa.Integer, nullable=False),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("precio_venta", sa.Numeric(12, 2), nullable=False),
        sa.Column("precio_costo", sa.Text, nullable=True),
        sa.Column("activo", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("eliminado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("universo IN ('mototaxi','motolineal')", name="chk_repuesto_universo"),
        sa.CheckConstraint("año BETWEEN 1990 AND 2100", name="chk_repuesto_año"),
        sa.CheckConstraint("precio_venta > 0", name="chk_repuesto_precio_venta"),
    )
    op.create_index("idx_repuesto_busqueda", "repuesto", ["universo", "modelo", "año", "codigo"])
    op.create_index("idx_repuesto_activo", "repuesto", ["activo", "universo"])

    # 3. usuario_perfil
    op.create_table("usuario_perfil",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("nombres", sa.Text, nullable=False),
        sa.Column("apellidos", sa.Text, nullable=False),
        sa.Column("dni", sa.Text, nullable=True),
        sa.Column("telefono_principal", sa.Text, nullable=True),
        sa.Column("telefono_secundario", sa.Text, nullable=True),
        sa.Column("direccion", sa.Text, nullable=True),
        sa.Column("consentimiento_fecha", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonimizado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("anonimizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonimizado_por", sa.String(100), nullable=True),
        sa.Column("foto_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_usuario_perfil_usuario", "usuario_perfil", ["usuario_id"])
    op.create_index("idx_usuario_perfil_consentimiento", "usuario_perfil", ["consentimiento_fecha"])

    # 4. sesion
    op.create_table("sesion",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.Text, unique=True, nullable=False),
        sa.Column("jti", sa.String(36), unique=True, nullable=False),
        sa.Column("consultas_precio", sa.Integer, nullable=False, server_default="0"),
        sa.Column("mfa_completado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("estado", sa.String(10), nullable=False, server_default="ACTIVA"),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("consultas_precio >= 0", name="chk_sesion_consultas"),
        sa.CheckConstraint("estado IN ('ACTIVA','REVOCADA')", name="chk_sesion_estado"),
    )
    op.create_index("idx_sesion_usuario", "sesion", ["usuario_id"])
    op.create_index("idx_sesion_jti", "sesion", ["jti"])
    op.create_index("idx_sesion_expiracion", "sesion", ["expira_en"])

    # 5. parametros_sistema
    op.create_table("parametros_sistema",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("clave", sa.String(100), unique=True, nullable=False),
        sa.Column("modulo", sa.String(30), nullable=False),
        sa.Column("valor", sa.Text, nullable=False),
        sa.Column("tipo_valor", sa.String(20), nullable=False),
        sa.Column("valor_defecto", sa.Text, nullable=False),
        sa.Column("descripcion", sa.Text, nullable=False, server_default=""),
        sa.Column("modificable_por", sa.String(30), nullable=False, server_default="ADMINISTRADOR"),
        sa.Column("modificado_por", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("modulo IN ('catalogo','pedidos','stock','taller','shared')", name="chk_params_modulo"),
        sa.CheckConstraint("tipo_valor IN ('int','float','str','bool')", name="chk_params_tipo_valor"),
        sa.CheckConstraint("modificable_por IN ('ADMINISTRADOR','SUPERADMIN')", name="chk_params_modificable_por"),
    )
    op.create_index("idx_params_modulo", "parametros_sistema", ["modulo"])
    op.create_index("idx_params_clave", "parametros_sistema", ["clave"])

    # 6. outbox_events
    op.create_table("outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("tipo_evento", sa.String(100), nullable=False),
        sa.Column("modulo_origen", sa.String(20), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("intentos", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ultimo_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("modulo_origen IN ('catalogo','pedidos','stock','taller')", name="chk_outbox_modulo"),
        sa.CheckConstraint("estado IN ('PENDIENTE','PROCESADO','FALLIDO')", name="chk_outbox_estado"),
        sa.CheckConstraint("intentos >= 0", name="chk_outbox_intentos"),
    )
    op.create_index("idx_outbox_pendiente", "outbox_events", ["estado", "created_at"])
    op.create_index("idx_outbox_fallido", "outbox_events", ["estado", "intentos"])
    op.create_index("idx_outbox_tipo", "outbox_events", ["tipo_evento"])

    # 7. eventos_procesados
    op.create_table("eventos_procesados",
        sa.Column("evento_id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("tipo", sa.String(100), nullable=False),
        sa.Column("modulo_origen", sa.String(20), nullable=False),
        sa.Column("modulo_consumidor", sa.String(20), nullable=False),
        sa.Column("procesado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resultado", sa.String(20), nullable=False),
        sa.CheckConstraint("resultado IN ('EXITOSO','IGNORADO')", name="chk_eventos_proc_resultado"),
    )
    op.create_index("idx_eventos_proc_consumidor", "eventos_procesados", ["modulo_consumidor", "procesado_en"])

    # 8. historial_precio_repuesto
    op.create_table("historial_precio_repuesto",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id", ondelete="CASCADE"), nullable=False),
        sa.Column("precio_anterior", sa.Numeric(12, 2), nullable=False),
        sa.Column("precio_nuevo", sa.Numeric(12, 2), nullable=False),
        sa.Column("modificado_por", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_historial_precio", "historial_precio_repuesto", ["repuesto_id", "created_at"])

    # 9. cliente
    op.create_table("cliente",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("segmento", sa.String(30), nullable=False),
        sa.Column("sub_rol", sa.String(30), nullable=True),
        sa.Column("canal_preferido", sa.String(20), nullable=False, server_default="presencial"),
        sa.Column("mecanico_preferido_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("nivel_visibilidad", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("nivel_visibilidad IN (0,1,2)", name="chk_cliente_visibilidad"),
    )
    op.create_index("idx_cliente_usuario", "cliente", ["usuario_id"])
    op.create_index("idx_cliente_segmento", "cliente", ["segmento"])

    # 10. stock_repuesto
    op.create_table("stock_repuesto",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), unique=True, nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("cantidad_disponible", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cantidad_apartada", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cantidad_en_transito", sa.Integer, nullable=False, server_default="0"),
        sa.Column("umbral_minimo", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cantidad_disponible >= 0", name="chk_disponible_no_negativo"),
        sa.CheckConstraint("cantidad_apartada >= 0", name="chk_apartado_no_negativo"),
        sa.CheckConstraint("cantidad_disponible + cantidad_apartada >= 0", name="chk_stock_coherente"),
    )
    op.create_index("idx_stock_disponible", "stock_repuesto", ["repuesto_id", "cantidad_disponible"])

    # 11. movimiento_stock
    op.create_table("movimiento_stock",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("stock_repuesto.repuesto_id"), nullable=False),
        sa.Column("tipo_movimiento", sa.String(50), nullable=False),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("estado_origen", sa.String(50), nullable=False),
        sa.Column("estado_destino", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(100), nullable=False),
        sa.Column("referencia_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cantidad > 0", name="chk_movimiento_cantidad_positiva"),
        sa.CheckConstraint("tipo_movimiento IN ('ENTRADA_REABASTECIMIENTO','SALIDA_VENTA','SALIDA_TALLER','AJUSTE_MANUAL','RESERVA','LIBERACION_RESERVA')", name="chk_tipo_movimiento"),
    )
    op.create_index("idx_movimiento_repuesto", "movimiento_stock", ["repuesto_id"])
    op.create_index("idx_movimiento_referencia", "movimiento_stock", ["referencia_id"])
    op.create_index("idx_movimiento_actor", "movimiento_stock", ["actor_id"])

    # 12. reabastecimiento
    op.create_table("reabastecimiento",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("proveedor", sa.String(200), nullable=False),
        sa.Column("solicitado_por", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="SOLICITADO"),
        sa.Column("notas", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('SOLICITADO','CONFIRMADO_PROVEEDOR','EN_TRANSITO','RECIBIDO','CANCELADO')", name="chk_reabastecimiento_estado"),
    )
    op.create_index("idx_reabastecimiento_estado", "reabastecimiento", ["estado", "created_at"])

    # 13. reabastecimiento_item
    op.create_table("reabastecimiento_item",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("reabastecimiento_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("reabastecimiento.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("cantidad_solicitada", sa.Integer, nullable=False),
        sa.Column("cantidad_recibida", sa.Integer, nullable=False, server_default="0"),
        sa.Column("precio_costo_unitario", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cantidad_solicitada > 0", name="chk_reab_item_cantidad"),
    )
    op.create_index("idx_reab_item_repuesto", "reabastecimiento_item", ["repuesto_id", "created_at"])

    # 14. notificacion_stock_cliente
    op.create_table("notificacion_stock_cliente",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PENDIENTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('PENDIENTE','ENVIADA','CANCELADA')", name="chk_notif_stock_estado"),
    )
    op.create_index("idx_notif_stock", "notificacion_stock_cliente", ["repuesto_id", "estado"])

    # 15. pedido
    op.create_table("pedido",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("canal_origen", sa.String(50), nullable=False),
        sa.Column("origen_actor", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("monto_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("descuento_aplicado", sa.Text, nullable=True),
        sa.Column("precio_ajustado", sa.Numeric(12, 2), nullable=True),
        sa.Column("motivo_cancelacion", sa.String(200), nullable=True),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('BORRADOR','CONFIRMADO','EN_PREPARACION','DESPACHADO','ENTREGADO','INCIDENCIA','CANCELADO')", name="chk_pedido_estado"),
        sa.CheckConstraint("monto_total >= 0", name="chk_pedido_monto"),
    )
    op.create_index("idx_pedido_cliente", "pedido", ["cliente_id"])
    op.create_index("idx_pedido_estado", "pedido", ["estado"])
    op.create_index("idx_pedido_orden_trabajo", "pedido", ["orden_trabajo_id"])
    op.create_index("idx_pedido_origen_actor", "pedido", ["origen_actor"])

    # 16. pedido_item
    op.create_table("pedido_item",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("precio_unitario", sa.Numeric(12, 2), nullable=False),
        sa.Column("precio_ajustado_unit", sa.Numeric(12, 2), nullable=True),
        sa.CheckConstraint("cantidad > 0", name="chk_pedido_item_cantidad"),
        sa.CheckConstraint("precio_unitario > 0", name="chk_pedido_item_precio"),
    )
    op.create_index("idx_pedido_item_pedido", "pedido_item", ["pedido_id"])

    # 17. reserva
    op.create_table("reserva",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id"), nullable=True),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("segmento", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ACTIVA"),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pago_registrado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notificaciones_enviadas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('ACTIVA','CONFIRMADA','EXPIRADA','LIBERADA')", name="chk_reserva_estado"),
        sa.CheckConstraint("notificaciones_enviadas >= 0", name="chk_reserva_notif"),
    )
    op.create_index("idx_reserva_cliente", "reserva", ["cliente_id"])
    op.create_index("idx_reserva_repuesto", "reserva", ["repuesto_id"])
    op.create_index("idx_reserva_expiracion", "reserva", ["expira_en", "estado"])

    # 18. lista_reserva_progresiva
    op.create_table("lista_reserva_progresiva",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("ultima_actividad", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('BORRADOR','CONFIRMADA','FORMALIZADA')", name="chk_lista_reserva_estado"),
    )
    op.create_index("idx_lista_cliente", "lista_reserva_progresiva", ["cliente_id"])
    op.create_index("idx_lista_actividad", "lista_reserva_progresiva", ["ultima_actividad"])

    # 19. lista_reserva_progresiva_item
    op.create_table("lista_reserva_progresiva_item",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("lista_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("lista_reserva_progresiva.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("precio_referencia", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("cantidad > 0", name="chk_lista_item_cantidad"),
    )
    op.create_index("idx_lista_item_lista", "lista_reserva_progresiva_item", ["lista_id"])

    # 20. proforma
    op.create_table("proforma",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero_referencia", sa.String(50), unique=True, nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="BORRADOR"),
        sa.Column("monto_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('BORRADOR','ENVIADA','ACEPTADA','RECHAZADA','VENCIDA')", name="chk_proforma_estado"),
        sa.CheckConstraint("monto_total > 0", name="chk_proforma_monto"),
    )
    op.create_index("idx_proforma_pedido", "proforma", ["pedido_id"])

    # 21. envio
    op.create_table("envio",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("empresa_encomienda", sa.String(100), nullable=False),
        sa.Column("direccion_destino", sa.Text, nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PREPARADO"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('PREPARADO','ENTREGADO_AGENCIA','EN_TRANSITO','ENTREGADO_CLIENTE','INCIDENCIA','RESUELTO')", name="chk_envio_estado"),
    )
    op.create_index("idx_envio_pedido", "envio", ["pedido_id"])
    op.create_index("idx_envio_estado", "envio", ["estado"])

    # 22. comprobante
    op.create_table("comprobante",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id"), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False, server_default="PENDIENTE_VALIDACION"),
        sa.Column("monto", sa.Numeric(12, 2), nullable=False),
        sa.Column("emitido_por", sa.String(100), nullable=False),
        sa.Column("ruc_cliente", sa.String(20), nullable=True),
        sa.Column("nota_credito_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("comprobante.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tipo IN ('boleta','factura','ticket')", name="chk_comprobante_tipo"),
        sa.CheckConstraint("estado IN ('PENDIENTE_VALIDACION','EMITIDO','ENVIADO_CLIENTE','ANULADO')", name="chk_comprobante_estado"),
        sa.CheckConstraint("monto > 0", name="chk_comprobante_monto"),
    )
    op.create_index("idx_comprobante_pedido", "comprobante", ["pedido_id"])
    op.create_index("idx_comprobante_estado", "comprobante", ["estado"])

    # 23. deuda_activa
    op.create_table("deuda_activa",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("pedido_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("pedido.id"), unique=True, nullable=False),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column("monto_deuda", sa.Numeric(12, 2), nullable=False),
        sa.Column("plazo_dias", sa.Integer, nullable=False),
        sa.Column("alerta_50_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alerta_vencimiento_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("monto_deuda > 0", name="chk_deuda_monto"),
        sa.CheckConstraint("plazo_dias > 0", name="chk_deuda_plazo"),
    )
    op.create_index("idx_deuda_cliente", "deuda_activa", ["cliente_id"])
    op.create_index("idx_deuda_alerta_50", "deuda_activa", ["alerta_50_en"])
    op.create_index("idx_deuda_alerta_venc", "deuda_activa", ["alerta_vencimiento_en"])

    # 24. vehiculo
    op.create_table("vehiculo",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("universo", sa.String(20), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("año", sa.Integer, nullable=False),
        sa.Column("placa", sa.Text, nullable=True),
        sa.Column("tarjeta_propiedad", sa.Text, nullable=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("salud_estimada", sa.Integer, nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("año BETWEEN 1990 AND 2100", name="chk_vehiculo_año"),
        sa.CheckConstraint("salud_estimada BETWEEN 0 AND 100", name="chk_vehiculo_salud"),
    )
    op.create_index("idx_vehiculo_cliente", "vehiculo", ["cliente_id"])
    op.create_index("idx_vehiculo_modelo", "vehiculo", ["universo", "modelo", "año"])

    # 25. mecanico
    op.create_table("mecanico",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("nivel", sa.String(10), nullable=False),
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=True),
        sa.Column("disponible", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("nivel IN ('MASTER','JUNIOR')", name="chk_mecanico_nivel"),
    )
    op.create_index("idx_mecanico_disponible", "mecanico", ["disponible", "nivel"])
    op.create_index("idx_mecanico_supervisor", "mecanico", ["supervisor_id"])

    # 26. mecanico_perfil
    op.create_table("mecanico_perfil",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("mecanico_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("dni", sa.Text, unique=True, nullable=False),
        sa.Column("nombres", sa.Text, nullable=False),
        sa.Column("apellidos", sa.Text, nullable=False),
        sa.Column("telefono", sa.Text, nullable=True),
        sa.Column("direccion", sa.Text, nullable=True),
        sa.Column("fecha_nacimiento", sa.Text, nullable=True),
        sa.Column("tipo_contrato", sa.String(30), nullable=False, server_default="tiempo_completo"),
        sa.Column("validado_por", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tipo_contrato IN ('tiempo_completo','medio_tiempo','eventual','honorarios')", name="chk_mecanico_perfil_contrato"),
    )
    op.create_index("idx_mecanico_perfil_dni", "mecanico_perfil", ["mecanico_id"])

    # 27. orden_trabajo
    op.create_table("orden_trabajo",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("vehiculo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("vehiculo.id"), nullable=False),
        sa.Column("mecanico_master_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=False),
        sa.Column("mecanico_junior_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("modalidad", sa.String(20), nullable=False),
        sa.Column("urgencia", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="ABIERTA"),
        sa.Column("cliente_aprobo_lista", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("visibilidad_precio_cliente", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("cobro_confirmado", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("costo_mano_obra", sa.Numeric(12, 2), nullable=True),
        sa.Column("monto_estimado", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("modalidad IN ('preventivo','correctivo','diagnostico','soldadura')", name="chk_ot_modalidad"),
        sa.CheckConstraint("urgencia IN ('alta','media','baja')", name="chk_ot_urgencia"),
        sa.CheckConstraint("estado IN ('ABIERTA','LISTA_REPUESTOS','EN_EJECUCION','REVISION_FINAL','CERRADA','CANCELADA')", name="chk_ot_estado"),
    )
    op.create_index("idx_ot_vehiculo", "orden_trabajo", ["vehiculo_id"])
    op.create_index("idx_ot_mecanico_master", "orden_trabajo", ["mecanico_master_id"])
    op.create_index("idx_ot_estado", "orden_trabajo", ["estado"])
    op.create_index("idx_ot_cobro", "orden_trabajo", ["cobro_confirmado", "estado"])

    # 28. lista_repuestos_ot
    op.create_table("lista_repuestos_ot",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orden_trabajo.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("repuesto.id"), nullable=False),
        sa.Column("codigo", sa.String(50), nullable=False),
        sa.Column("cantidad", sa.Integer, nullable=False),
        sa.Column("precio_unitario", sa.Numeric(12, 2), nullable=False),
        sa.Column("momento_agregado", sa.String(20), nullable=False),
        sa.Column("tramo_precio", sa.String(20), nullable=True),
        sa.Column("aprobacion_cliente", sa.String(30), nullable=False, server_default="PENDIENTE"),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("espera_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cantidad > 0", name="chk_lrot_cantidad"),
        sa.CheckConstraint("momento_agregado IN ('inicial','en_ejecucion')", name="chk_lrot_momento"),
        sa.CheckConstraint("aprobacion_cliente IN ('PENDIENTE','APROBADO_AUTOMATICO','APROBADO_TACITO','APROBADO_EXPLICITO','RECHAZADO','PENDIENTE_ADICIONAL')", name="chk_lrot_aprobacion"),
    )
    op.create_index("idx_lrot_orden", "lista_repuestos_ot", ["orden_trabajo_id"])
    op.create_index("idx_lrot_aprobacion", "lista_repuestos_ot", ["aprobacion_cliente"])

    # 29. costo_adicional_ot
    op.create_table("costo_adicional_ot",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orden_trabajo.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lista_repuesto_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("lista_repuestos_ot.id"), nullable=False),
        sa.Column("tramo", sa.String(20), nullable=False),
        sa.Column("monto_adicional", sa.Numeric(12, 2), nullable=False),
        sa.Column("espera_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resultado", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tramo IN ('automatico','tacito','manual')", name="chk_costo_adic_tramo"),
    )
    op.create_index("idx_costo_adic_ot", "costo_adicional_ot", ["orden_trabajo_id"])
    op.create_index("idx_costo_adic_espera", "costo_adicional_ot", ["espera_hasta"])

    # 30. rendicion_mecanico
    op.create_table("rendicion_mecanico",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("mecanico_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=False),
        sa.Column("periodo_mes", sa.Integer, nullable=False),
        sa.Column("periodo_año", sa.Integer, nullable=False),
        sa.Column("total_generado", sa.Numeric(12, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="PENDIENTE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('PENDIENTE','APROBADA','PAGADA')", name="chk_rendicion_estado"),
        sa.UniqueConstraint("mecanico_id", "periodo_mes", "periodo_año", name="uq_rendicion_periodo"),
    )
    op.create_index("idx_rendicion_mecanico", "rendicion_mecanico", ["mecanico_id"])
    op.create_index("idx_rendicion_estado", "rendicion_mecanico", ["estado"])

    # 31. historial_cobro_mecanico
    op.create_table("historial_cobro_mecanico",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orden_trabajo.id"), unique=True, nullable=False),
        sa.Column("mecanico_master_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=False),
        sa.Column("costo_mano_obra", sa.Numeric(12, 2), nullable=False),
        sa.Column("periodo_mes", sa.Integer, nullable=False),
        sa.Column("periodo_año", sa.Integer, nullable=False),
        sa.Column("rendicion_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("rendicion_mecanico.id"), nullable=True),
        sa.CheckConstraint("costo_mano_obra >= 0", name="chk_cobro_mano_obra"),
    )
    op.create_index("idx_cobro_master", "historial_cobro_mecanico", ["mecanico_master_id"])
    op.create_index("idx_cobro_periodo", "historial_cobro_mecanico", ["periodo_año", "periodo_mes"])

    # 32. historial_intervencion
    op.create_table("historial_intervencion",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("vehiculo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("vehiculo.id"), nullable=False),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orden_trabajo.id"), unique=True, nullable=False),
        sa.Column("mecanico_master_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("mecanico.id"), nullable=False),
        sa.Column("fecha_apertura", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=False),
        sa.Column("monto_final", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("idx_historial_vehiculo", "historial_intervencion", ["vehiculo_id", "fecha_cierre"])
    op.create_index("idx_historial_mecanico", "historial_intervencion", ["mecanico_master_id"])

    # 33. entrada
    op.create_table("entrada",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("vehiculo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("vehiculo.id"), nullable=False),
        sa.Column("orden_trabajo_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orden_trabajo.id"), nullable=True),
        sa.Column("cliente_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("cliente.id"), nullable=True),
        sa.Column("estado", sa.String(10), nullable=False, server_default="ACTIVA"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('ACTIVA','CERRADA')", name="chk_entrada_estado"),
    )
    op.create_index("idx_entrada_vehiculo", "entrada", ["vehiculo_id"])
    op.create_index("idx_entrada_ot", "entrada", ["orden_trabajo_id"])
    op.create_index("idx_entrada_activa", "entrada", ["estado", "created_at"])


def downgrade() -> None:
    # Eliminar en orden inverso respetando FK
    op.drop_table("entrada")
    op.drop_table("historial_intervencion")
    op.drop_table("historial_cobro_mecanico")
    op.drop_table("rendicion_mecanico")
    op.drop_table("costo_adicional_ot")
    op.drop_table("lista_repuestos_ot")
    op.drop_table("orden_trabajo")
    op.drop_table("mecanico_perfil")
    op.drop_table("mecanico")
    op.drop_table("vehiculo")
    op.drop_table("deuda_activa")
    op.drop_table("comprobante")
    op.drop_table("envio")
    op.drop_table("proforma")
    op.drop_table("lista_reserva_progresiva_item")
    op.drop_table("lista_reserva_progresiva")
    op.drop_table("reserva")
    op.drop_table("pedido_item")
    op.drop_table("pedido")
    op.drop_table("notificacion_stock_cliente")
    op.drop_table("reabastecimiento_item")
    op.drop_table("reabastecimiento")
    op.drop_table("movimiento_stock")
    op.drop_table("stock_repuesto")
    op.drop_table("cliente")
    op.drop_table("historial_precio_repuesto")
    op.drop_table("eventos_procesados")
    op.drop_table("outbox_events")
    op.drop_table("parametros_sistema")
    op.drop_table("sesion")
    op.drop_table("usuario_perfil")
    op.drop_table("repuesto")
    op.drop_table("usuario")
