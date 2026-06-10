"""Verificación dev del Radar societario: FTS por razón social y rubros."""
from __future__ import annotations

import asyncio

from sqlalchemy import text

from vigia_shared.db import session_scope


async def main() -> None:
    async with session_scope() as s:
        razon = await s.scalar(
            text("SELECT razon_social FROM aviso_societario WHERE razon_social IS NOT NULL LIMIT 1")
        )
        palabra = razon.split()[0]
        print("buscando:", palabra)
        rows = (
            await s.execute(
                text(
                    "SELECT razon_social, rubro FROM aviso_societario "
                    "WHERE search_vector @@ plainto_tsquery('spanish', :q) LIMIT 3"
                ),
                {"q": palabra},
            )
        ).all()
        assert rows, "FAIL: el FTS no encontró nada"
        for r in rows:
            print("-", r.razon_social, "|", (r.rubro or "")[:45])
        rubros = (
            await s.execute(
                text("SELECT rubro, COUNT(*) FROM aviso_societario GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
            )
        ).all()
        print("top rubros:", [(str(r[0])[:40], r[1]) for r in rubros if r[0]])
    print("OK: FTS societario funcionando")


if __name__ == "__main__":
    asyncio.run(main())
