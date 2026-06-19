"""Celery application + beat schedule para la ingesta de Vigía."""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "vigia",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "vigia_workers.tasks",
        "vigia_workers.alerts",
        "vigia_workers.freshness",
        "vigia_workers.reconcile",
        "vigia_workers.bicameral",
        "vigia_workers.movimientos",
        "vigia_workers.societario",
        "vigia_workers.maintenance",
    ],
)

# Sentry — no-op si falta SENTRY_DSN.
_sentry_dsn = os.environ.get("SENTRY_DSN")
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[CeleryIntegration()],
            traces_sample_rate=0.05,
            environment=os.environ.get("VIGIA_ENV", "dev"),
        )
    except Exception as e:  # pragma: no cover
        print(f"[sentry] init failed: {e!r}")

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    timezone="America/Argentina/Buenos_Aires",
    enable_utc=False,
    beat_schedule={
        # ─────────────────────────────────────────────────────────────────
        # Instancia CESBA — solo BOCBA (Boletín Oficial CABA).
        # Las tasks nacionales (InfoLEG, BORA, HCDN, Senado, BCRA, bicameral,
        # consultas públicas) están deshabilitadas en este fork: no aplican al
        # corpus porteño y sus fuentes no están configuradas. El código sigue
        # disponible si en el futuro se quiere ampliar el alcance.
        # ─────────────────────────────────────────────────────────────────
        # BOCBA — Boletín Oficial de la Ciudad de Buenos Aires. API REST sin
        # autenticación. Publica normalmente a las 08:00–09:00 ART; retry 13:00
        # por si la edición sale tarde. Lookback 5 días idempotente.
        "ingest-bocba": {
            "task": "vigia_workers.tasks.ingest_bocba",
            "schedule": crontab(hour=9, minute=0),
        },
        "ingest-bocba-retry": {
            "task": "vigia_workers.tasks.ingest_bocba",
            "schedule": crontab(hour=13, minute=0),
        },
        # Matching de alertas + notificaciones — cada hora.
        "match-alertas": {
            "task": "vigia_workers.alerts.match_alertas",
            "schedule": crontab(minute=15),
        },
        # Frescura de fuentes contra SLOs (vigia_shared.sources) — cada 6 h.
        # Detecta datasets estancados aunque la task corra "ok".
        "check-sources": {
            "task": "vigia_workers.freshness.check_sources",
            "schedule": crontab(hour="*/6", minute=45),
        },
        # Retención de audit_log (IP/user-agent) — semanal, domingo 05:00 ART.
        # Borra registros más viejos que VIGIA_AUDIT_RETENTION_DAYS (Ley 25.326,
        # art. 4: limitación temporal). Fuera de la ventana de ingesta.
        "purge-audit-log": {
            "task": "vigia_workers.maintenance.purge_audit_log",
            "schedule": crontab(day_of_week=0, hour=5, minute=0),
        },
    },
)
