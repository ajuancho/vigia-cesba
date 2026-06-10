"""Verificación dev del reconcile BORA↔InfoLEG contra la DB local.

Inserta una gemela InfoLEG sintética del Decreto 436/2026 (que existe como
fila BORA tras ingest_bora_primera), un alerta_match sobre la fila BORA, corre
el reconcile y verifica: fila BORA borrada, match trasplantado con
notified=true, y que la Decisión Administrativa 21/2026 NO se cruzó con un
Decreto 21/2026 falso (guard de instrumento).
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import text

from vigia_shared.db import session_scope
from vigia_workers.reconcile import _reconcile


async def main() -> None:
    async with session_scope() as session:
        bora_id = await session.scalar(
            text("SELECT id FROM source_catalog WHERE code = 'bora_primera'")
        )
        # Fila BORA del Decreto 436/2026 (debe existir tras la ingesta).
        bora_norma = await session.scalar(
            text(
                "SELECT id FROM norma WHERE source_id = :sid AND numero = '436/2026' "
                "AND tipo = 'DECRETO' AND fecha_publicacion = :f"
            ),
            {"sid": bora_id, "f": date(2026, 6, 10)},
        )
        assert bora_norma, "no está la fila BORA del Decreto 436/2026"

        # Source InfoLEG (crearlo si la DB local nunca ingestó InfoLEG).
        infoleg_id = await session.scalar(
            text("SELECT id FROM source_catalog WHERE code = 'infoleg'")
        )
        if infoleg_id is None:
            infoleg_id = await session.scalar(
                text(
                    "INSERT INTO source_catalog (code, name, kind, base_url) "
                    "VALUES ('infoleg', 'InfoLEG (test)', 'feed', 'https://datos.jus.gob.ar') "
                    "RETURNING id"
                )
            )

        # Gemela InfoLEG sintética (mismo número/fecha, instrumento Decreto)
        # + un señuelo DA 21/2026 como "Decreto" para verificar el guard.
        canon_id = await session.scalar(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo,
                                   fecha_publicacion, jurisdiccion, organismo, estado, raw)
                VALUES (:sid, 'TEST-436', 'DECRETO', '436', 'GEMELA INFOLEG TEST',
                        :f, 'Nacional', 'MINISTERIO DE SEGURIDAD NACIONAL', 'Publicada',
                        '{"tipo_norma": "Decreto"}'::jsonb)
                ON CONFLICT (source_id, external_id) DO UPDATE SET numero = EXCLUDED.numero
                RETURNING id
                """
            ),
            {"sid": infoleg_id, "f": date(2026, 6, 10)},
        )
        decoy_id = await session.scalar(
            text(
                """
                INSERT INTO norma (source_id, external_id, tipo, numero, titulo,
                                   fecha_publicacion, jurisdiccion, estado, raw)
                VALUES (:sid, 'TEST-DA21-DECOY', 'DECRETO', '21', 'DECRETO 21 SENUELO (no es la DA 21)',
                        :f, 'Nacional', 'Publicada', '{"tipo_norma": "Decreto"}'::jsonb)
                ON CONFLICT (source_id, external_id) DO UPDATE SET numero = EXCLUDED.numero
                RETURNING id
                """
            ),
            {"sid": infoleg_id, "f": date(2026, 6, 10)},
        )

        # Alerta + match sobre la fila BORA (simula notificación ya enviada).
        ws_id = await session.scalar(text("SELECT id FROM workspace ORDER BY id LIMIT 1"))
        if ws_id is None:
            ws_id = await session.scalar(
                text("INSERT INTO workspace (slug, name) VALUES ('test-rec', 'Test') RETURNING id")
            )
        alerta_id = await session.scalar(
            text(
                "INSERT INTO alerta (workspace_id, keyword, activa) "
                "VALUES (:ws, 'test-reconcile', true) RETURNING id"
            ),
            {"ws": ws_id},
        )
        await session.execute(
            text(
                "INSERT INTO alerta_match (alerta_id, norma_id, notified) "
                "VALUES (:a, :n, true) ON CONFLICT DO NOTHING"
            ),
            {"a": alerta_id, "n": bora_norma},
        )

    result = await _reconcile()
    print("reconcile:", result)

    async with session_scope() as session:
        bora_still = await session.scalar(
            text("SELECT id FROM norma WHERE id = :id"), {"id": bora_norma}
        )
        transplanted = await session.scalar(
            text(
                "SELECT notified FROM alerta_match WHERE alerta_id = :a AND norma_id = :n"
            ),
            {"a": alerta_id, "n": canon_id},
        )
        # La fila BORA de la DA 21/2026 debe seguir viva (el señuelo no la matchea).
        da_alive = await session.scalar(
            text(
                "SELECT COUNT(*) FROM norma WHERE numero = '21/2026' "
                "AND raw->>'tipo_linea' ILIKE 'Decisi%'"
            )
        )

        assert bora_still is None, "FAIL: la fila BORA del 436/2026 sigue viva"
        assert transplanted is True, "FAIL: el match no se trasplantó con notified=true"
        assert (da_alive or 0) >= 1, "FAIL: el guard de instrumento no protegió a la DA 21/2026"
        assert result["merged"] == 1, f"FAIL: se esperaba 1 merge, hubo {result['merged']}"

        # Limpieza de los artefactos sintéticos.
        await session.execute(text("DELETE FROM alerta WHERE id = :a"), {"a": alerta_id})
        await session.execute(
            text("DELETE FROM norma WHERE id IN (:c, :d)"), {"c": canon_id, "d": decoy_id}
        )

    print("OK: merge correcto, match trasplantado, guard de instrumento respetado")


if __name__ == "__main__":
    asyncio.run(main())
