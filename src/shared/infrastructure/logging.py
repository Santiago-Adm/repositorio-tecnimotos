"""
Logging estructurado JSON (02 §1.6, RNT-06).
JSONFormatter con 5 campos obligatorios + request_id vía ContextVar.
Librería: logging estándar de Python — sin structlog ni loguru.
"""
import json
import logging
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# ContextVar para propagación de request_id por corrutina.
# Se establece en CorrelationMiddleware ANTES de call_next.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def _current_request_id() -> str:
    rid = request_id_var.get("")
    return rid if rid else str(uuid.uuid4())


class JSONFormatter(logging.Formatter):
    """
    Formateador JSON con campos obligatorios declarados en 02 §1.6.
    Lanza ValueError en desarrollo si falta alguno de los 5 campos.
    """

    REQUIRED_FIELDS = {"timestamp", "level", "service", "version", "environment"}

    def __init__(
        self,
        service: str,
        version: str,
        environment: str,
        strict: bool = False,
    ) -> None:
        super().__init__()
        self._service = service
        self._version = version
        self._environment = environment
        self._strict = strict  # True en desarrollo: falla si falta campo obligatorio

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self._service,
            "version": self._version,
            "environment": self._environment,
            "request_id": _current_request_id(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            entry["stack_info"] = self.formatStack(record.stack_info)

        # Campos extra agregados al log record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            } and not key.startswith("_"):
                entry[key] = value

        if self._strict:
            missing = self.REQUIRED_FIELDS - set(entry.keys())
            if missing:
                raise ValueError(
                    f"JSONFormatter: campos obligatorios ausentes: {missing}"
                )

        return json.dumps(entry, default=str, ensure_ascii=False)


def configure_logging(
    service: str,
    version: str,
    environment: str,
    level: int = logging.INFO,
) -> None:
    """Configura el logger raíz con JSONFormatter."""
    strict = environment == "development"
    formatter = JSONFormatter(
        service=service,
        version=version,
        environment=environment,
        strict=strict,
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
