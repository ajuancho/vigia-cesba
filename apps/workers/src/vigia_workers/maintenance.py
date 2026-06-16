"""Tareas de mantenimiento / retención de datos.

`purge_audit_log` borra los registros de `audit_log` (que incluyen IP y
user-agent) más viejos que `VIGIA_AUDIT_RETENTION_DAYS`. Aplica el principio de
limitación temporal de la Ley 25.326 (art. 4): no conservar datos personales por
más tiempo del necesario para la finalidad que los justificó.
"""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import text

from vigia_shared.db import session_scope
from vigia_workers.celery_app import celery_app
from vigia_workers.persistence import run_async

DEFAULT_RETENTION_DAYS = 365


def _retention_days() -> int:
    try:
        return max(1, int(os.environ.get("VIGIA_AUDIT_RETENTION_DAYS", str(DEFAULT_RETENTION_DAYS))))
    except (TypeError, ValueError):
        return DEFAULT_RETENTION_DAYS


async def _purge(days: int) -> dict[str, Any]:
    async with session_scope() as session:
        result = await session.execute(
            text("DELETE FROM audit_log WHERE created_at < now() - make_interval(days => :days)"),
            {"days": days},
        )
    return {"deleted": result.rowcount, "retention_days": days}


@celery_app.task(name="vigia_workers.maintenance.purge_audit_log")
def purge_audit_log() -> dict[str, Any]:
    return run_async(_purge(_retention_days()))
