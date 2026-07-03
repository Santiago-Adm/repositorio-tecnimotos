"""
Entidad ImagenRepuesto — galería de imágenes por repuesto (sesión 2026-06-27).
Nunca usar: foto, picture, photo, gallery. Usar siempre imagen_repuesto.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ImagenRepuesto:
    """
    Una imagen asociada a un Repuesto.
    orden=0 → imagen principal (la que aparece en tarjetas de EP-CAT-01).
    updated_at: se establece en reemplazo (EP-CAT-11); None si nunca fue reemplazada.
    """
    repuesto_id: str
    url: str
    orden: int
    subido_por: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    subido_en: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def reemplazar_url(self, nueva_url: str) -> None:
        """Actualiza la referencia al objeto en R2. No cambia id, orden ni repuesto_id."""
        self.url = nueva_url
        self.updated_at = datetime.now(timezone.utc)
