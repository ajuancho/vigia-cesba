"""Prueba de envío real de emails (digest + invitación) vía Resend.

Requiere RESEND_API_KEY en el entorno del proceso (NUNCA en archivos del
repo). Uso: $env:RESEND_API_KEY="..."; python scripts/test_email_dev.py <destinatario>
"""
from __future__ import annotations

import sys

from vigia_workers.notifications import render_digest, send_email

to = sys.argv[1] if len(sys.argv) > 1 else "devops@colossuslab.org"

items = [
    {"id": 421573, "keyword": "estructura", "tipo": "DECRETO", "numero": "404",
     "titulo": "ESTRUCTURA ORGANIZATIVA - MODIFICACION DECRETOS 50/2019 Y 735/2024"},
    {"id": 421579, "keyword": "tarifas", "tipo": "RESOLUCION", "numero": "52",
     "titulo": "REFINERIA DEL NORTE SOCIEDAD ANONIMA - CUADROS TARIFARIOS"},
]
result = send_email(
    to=to,
    subject="Vigía — prueba de digest de alertas (2 coincidencias)",
    html=render_digest("Colossus Lab", items),
)
print("digest:", result)
assert result.get("sent") or result.get("skipped"), f"FAIL: {result}"
