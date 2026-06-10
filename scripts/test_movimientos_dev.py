"""Verificación dev de movimientos HCDN: siembra un proyecto real (HCDN291681,
que tiene "PASA A SENADO" en el dataset), corre la ingesta real y verifica
estado derivado + timeline en raw."""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import text

from vigia_shared.db import session_scope

PID = "HCDN291681"


async def seed() -> None:
    async with session_scope() as s:
        sid = await s.scalar(text("SELECT id FROM source_catalog WHERE code = 'hcdn_proyectos'"))
        assert sid, "falta source hcdn_proyectos (corré antes test_bicameral_dev o una ingesta)"
        await s.execute(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo,
                                   fecha_publicacion, jurisdiccion, estado, raw)
                VALUES (:sid, :pid, 'PROYECTO', '0001-D-2026', 'PROYECTO TEST MOVIMIENTOS',
                        :f, 'Nacional', 'En trámite', '{}'::jsonb)
                ON CONFLICT (source_id, external_id)
                DO UPDATE SET estado = 'En trámite', raw = '{}'::jsonb
                """
            ),
            {"sid": sid, "pid": PID, "f": date(2026, 3, 1)},
        )


async def check() -> None:
    async with session_scope() as s:
        row = (
            await s.execute(
                text(
                    "SELECT estado, jsonb_array_length(raw->'movimientos') AS nmovs "
                    "FROM norma WHERE external_id = :pid"
                ),
                {"pid": PID},
            )
        ).first()
        print("estado:", row.estado, "| movimientos en timeline:", row.nmovs)
        assert row.estado == "Media sanción", f"FAIL: {row.estado}"
        assert (row.nmovs or 0) >= 1, "FAIL: sin timeline"
        await s.execute(text("DELETE FROM norma WHERE external_id = :pid"), {"pid": PID})
    print("OK: estado derivado y timeline en raw")


if __name__ == "__main__":
    asyncio.run(seed())
    from vigia_workers.movimientos import ingest_hcdn_movimientos

    r = ingest_hcdn_movimientos()
    print({k: r.get(k) for k in ("actualizados", "con_estado_derivado")})
    asyncio.run(check())
