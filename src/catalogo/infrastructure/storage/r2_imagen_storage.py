"""
Adaptador Cloudflare R2 para ImagenStoragePort (03 §3.5).
Usa la API S3-compatible de R2 vía aioboto3.

Decisión de sesión 2026-06-28: se usa R2_ENDPOINT directamente
(URL completa incluyendo account_id), no se deriva en código.
`prefix` parametrizable (default "repuestos") — permite reutilizar
la misma clase para documentos de usuario con prefix "documentos"
(sesión 2026-06-28, flujo de autorregistro).

Key format:  {prefix}/{uuid_hex}.{extension}
             El nombre original del archivo nunca se persiste
             en la key para evitar colisiones y exposición de
             nombres de archivo del cliente.
URL pública: {R2_PUBLIC_URL}/{key}  — nunca el R2_ENDPOINT S3.
"""
from __future__ import annotations

import uuid

import aioboto3


class R2ImagenStorage:
    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_url: str,
        prefix: str = "repuestos",
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._bucket_name = bucket_name
        self._public_url = public_url.rstrip("/")
        self._prefix = prefix.strip("/")
        self._session = aioboto3.Session()

    def _build_key(self, nombre_archivo: str) -> str:
        """Genera una key única que no expone el nombre de archivo original."""
        ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else "bin"
        return f"{self._prefix}/{uuid.uuid4().hex}.{ext}"

    def _key_from_url(self, url: str) -> str:
        """Extrae la key del objeto a partir de su URL pública."""
        return url.removeprefix(self._public_url).lstrip("/")

    def _make_client_kwargs(self) -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": self._endpoint_url,
            "aws_access_key_id": self._access_key_id,
            "aws_secret_access_key": self._secret_access_key,
            "region_name": "auto",
        }

    async def subir(
        self, contenido: bytes, nombre_archivo: str, tipo_contenido: str
    ) -> str:
        key = self._build_key(nombre_archivo)
        async with self._session.client(**self._make_client_kwargs()) as s3:
            await s3.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=contenido,
                ContentType=tipo_contenido,
            )
        return f"{self._public_url}/{key}"

    async def subir_con_key(
        self, contenido: bytes, key: str, tipo_contenido: str
    ) -> str:
        """Sube el objeto a una key explícita (convención fija, sin UUID aleatorio).
        Usada por el campo único imagen_url de repuesto (repuestos/{codigo}/1.jpg) —
        a diferencia de subir(), que genera una key aleatoria para la galería."""
        async with self._session.client(**self._make_client_kwargs()) as s3:
            await s3.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=contenido,
                ContentType=tipo_contenido,
            )
        return f"{self._public_url}/{key}"

    async def eliminar(self, url: str) -> None:
        key = self._key_from_url(url)
        async with self._session.client(**self._make_client_kwargs()) as s3:
            await s3.delete_object(Bucket=self._bucket_name, Key=key)
