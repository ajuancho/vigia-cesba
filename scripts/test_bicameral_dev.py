"""Verificación dev del tracking bicameral contra la DB local.

Siembra: el proyecto de comunicación HCDN182484 (título real con la referencia
al DNU 223/2016), el DNU 223/2016 con tracking pendiente, y un DNU de 1995
(pre ley 26.122). Corre ingest_bicameral_dnu (descarga el CSV REAL de HCDN) y
verifica: 223/2016 → dictaminado con veredicto en notas; 1995 → sin_tratamiento.
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import text

from vigia_shared.db import session_scope


async def seed() -> tuple[int, int]:
    async with session_scope() as session:
        hcdn_id = await session.scalar(
            text("SELECT id FROM source_catalog WHERE code = 'hcdn_proyectos'")
        )
        if hcdn_id is None:
            hcdn_id = await session.scalar(
                text(
                    "INSERT INTO source_catalog (code, name, kind) "
                    "VALUES ('hcdn_proyectos', 'HCDN (test)', 'feed') RETURNING id"
                )
            )
        await session.execute(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo, fecha_publicacion, jurisdiccion)
                VALUES (:sid, 'HCDN182484', 'PROYECTO', '1-PE-2016',
                        'COMUNICACION DEL DECRETO DE NECESIDAD Y URGENCIA 223 DEL 25 DE ENERO DE 2016, POR EL CUAL SE SUSTITUYE LA DENOMINACION DEL MINISTERIO',
                        :f, 'Nacional')
                ON CONFLICT (source_id, external_id) DO NOTHING
                """
            ),
            {"sid": hcdn_id, "f": date(2016, 2, 1)},
        )

        infoleg_id = await session.scalar(
            text("SELECT id FROM source_catalog WHERE code = 'infoleg'")
        )
        dnu_id = await session.scalar(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo, fecha_publicacion, jurisdiccion, raw)
                VALUES (:sid, 'TEST-DNU-223', 'DNU', '223/2016', 'DNU 223/2016 TEST', :f, 'Nacional',
                        '{"fecha_sancion": "2016-01-25"}'::jsonb)
                ON CONFLICT (source_id, external_id) DO UPDATE SET numero = EXCLUDED.numero
                RETURNING id
                """
            ),
            {"sid": infoleg_id, "f": date(2016, 1, 26)},
        )
        viejo_id = await session.scalar(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo, fecha_publicacion, jurisdiccion)
                VALUES (:sid, 'TEST-DNU-1995', 'DNU', '100/1995', 'DNU VIEJO TEST', :f, 'Nacional')
                ON CONFLICT (source_id, external_id) DO UPDATE SET numero = EXCLUDED.numero
                RETURNING id
                """
            ),
            {"sid": infoleg_id, "f": date(1995, 3, 1)},
        )
        for nid in (dnu_id, viejo_id):
            await session.execute(
                text(
                    "INSERT INTO dnu_tracking (norma_id, estado_bicameral) "
                    "VALUES (:n, 'pendiente') ON CONFLICT (norma_id) DO UPDATE SET estado_bicameral = 'pendiente'"
                ),
                {"n": nid},
            )
        return dnu_id, viejo_id


async def verify(dnu_id: int, viejo_id: int) -> None:
    async with session_scope() as session:
        row = (
            await session.execute(
                text(
                    "SELECT estado_bicameral, fecha_dictamen, notas, raw->>'veredicto' AS veredicto "
                    "FROM dnu_tracking WHERE norma_id = :n"
                ),
                {"n": dnu_id},
            )
        ).first()
        assert row is not None, "FAIL: sin tracking para el DNU 223/2016"
        assert row.estado_bicameral == "dictaminado", f"FAIL: estado={row.estado_bicameral}"
        assert row.veredicto == "validez", f"FAIL: veredicto={row.veredicto}"
        assert row.fecha_dictamen == date(2016, 2, 25), f"FAIL: fecha={row.fecha_dictamen}"
        print(f"OK 223/2016 -> dictaminado ({row.veredicto}, {row.fecha_dictamen})")
        print(f"   notas: {row.notas[:120]}")

        viejo = await session.scalar(
            text("SELECT estado_bicameral FROM dnu_tracking WHERE norma_id = :n"), {"n": viejo_id}
        )
        assert viejo == "sin_tratamiento", f"FAIL: DNU 1995 quedó '{viejo}'"
        print("OK DNU 1995 -> sin_tratamiento")

        # Limpieza.
        await session.execute(
            text("DELETE FROM norma WHERE id IN (:a, :b)"), {"a": dnu_id, "b": viejo_id}
        )
        await session.execute(
            text(
                "DELETE FROM norma WHERE external_id = 'HCDN182484' "
                "AND source_id = (SELECT id FROM source_catalog WHERE code = 'hcdn_proyectos')"
            )
        )


if __name__ == "__main__":
    dnu_id, viejo_id = asyncio.run(seed())
    from vigia_workers.bicameral import ingest_bicameral_dnu

    result = ingest_bicameral_dnu()
    print("ingest:", result)
    asyncio.run(verify(dnu_id, viejo_id))
    print("OK: pipeline bicameral completo")
