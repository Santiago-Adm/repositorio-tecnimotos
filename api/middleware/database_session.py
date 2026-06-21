"""
Middleware que crea una AsyncSession por request y la almacena en request.state.db.
Si no hay db_session_factory configurada (tests sin BD), pasa sin session.
Los _get_repo() de cada router detectan request.state.db para elegir PG vs InMemory.
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        factory = getattr(request.app.state, "db_session_factory", None)
        if factory is None:
            return await call_next(request)

        async with factory() as session:
            request.state.db = session
            try:
                response = await call_next(request)
                if response.status_code < 500:
                    await session.commit()
                else:
                    await session.rollback()
                return response
            except Exception:
                await session.rollback()
                raise
