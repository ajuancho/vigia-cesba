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
        # InfoLEG / Boletín Oficial — corpus completo (incluye lo último publicado),
        # diario 03:00 ART. El dataset oficial se refresca semanalmente, correrlo
        # a diario garantiza tomar cada actualización apenas sale.
        "ingest-infoleg-full": {
            "task": "vigia_workers.tasks.ingest_infoleg_full",
            "schedule": crontab(hour=3, minute=0),
        },
        # Reconcile BORA↔InfoLEG post corpus full: la gemela InfoLEG reemplaza
        # a la fila BORA (anti-duplicados del feed).
        "reconcile-bora-infoleg": {
            "task": "vigia_workers.reconcile.reconcile_bora_infoleg",
            "schedule": crontab(hour=4, minute=30),
        },
        # BORA 1ª sección — frescura diaria real (el BO publica de madrugada).
        # Retry 12:00 por si la edición sale tarde. Lookback 5 días idempotente.
        "ingest-bora-primera": {
            "task": "vigia_workers.tasks.ingest_bora_primera",
            "schedule": crontab(hour=7, minute=0),
        },
        "ingest-bora-primera-retry": {
            "task": "vigia_workers.tasks.ingest_bora_primera",
            "schedule": crontab(hour=12, minute=0),
        },
        # HCDN proyectos parlamentarios — el dataset se actualiza a diario.
        "ingest-hcdn-proyectos": {
            "task": "vigia_workers.tasks.ingest_hcdn_proyectos",
            "schedule": crontab(hour=8, minute=0),
        },
        # Dictámenes de la Comisión Bicameral DNU (HCDN CKAN) — diario.
        # Después de hcdn-proyectos (08:00): el join usa los proyectos del día.
        "ingest-bicameral-dnu": {
            "task": "vigia_workers.bicameral.ingest_bicameral_dnu",
            "schedule": crontab(hour=9, minute=30),
        },
        # Comunicaciones A del BCRA — diario post-publicación (patrón InvestArg).
        "ingest-bcra-comunicaciones": {
            "task": "vigia_workers.tasks.ingest_bcra_comunicaciones",
            "schedule": crontab(hour=20, minute=30),
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
    },
)
