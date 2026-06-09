# Vigía — Inteligencia Legislativa y Regulatoria

**Plataforma Open Source de inteligencia legislativa y regulatoria argentina en tiempo real.**

Monitoreo del Boletín Oficial, Congreso y sector público. Un proyecto de código abierto impulsado por [Colossus Lab](https://colossuslab.com.ar).

---

## ¿Qué es Vigía?

Vigía es una herramienta de inteligencia legislativa que centraliza, analiza y alerta sobre la producción normativa argentina. Permite a empresas, estudios jurídicos y áreas de compliance monitorear el Boletín Oficial, la actividad del Congreso y la regulación sectorial desde un único dashboard.

### Funcionalidades

| Módulo | Descripción |
|---|---|
| **Feed Normativo** | Timeline en tiempo real de DNU, decretos, leyes, resoluciones y proyectos |
| **Dashboard** | KPIs, producción legislativa mensual, distribución sectorial, estado de DNU |
| **Buscador** | Búsqueda por keyword con filtros por tipo, sector y jurisdicción |
| **Alertas** | Monitoreo automatizado por keywords y sectores con notificaciones |
| **Tracker DNU** | Seguimiento de Decretos de Necesidad y Urgencia y su tratamiento bicameral |
| **Detalle de Norma** | Análisis automático, texto resumido, entidades identificadas (NER), tags |

### Fuentes de datos

- Boletín Oficial de la República Argentina (BORA)
- Honorable Cámara de Diputados y Senado de la Nación
- InfoLEG — Base de datos de legislación nacional
- Organismos regulatorios sectoriales (BCRA, CNV, SSN, ENACOM, etc.)

---

## Stack técnico

Monorepo (calcado del patrón de InvestArg / Colossus Lab):

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI 0.115 async · SQLAlchemy 2.0 · Pydantic v2 |
| Base de datos | PostgreSQL 16 + pgvector · Alembic |
| Búsqueda | Postgres FTS con GIN (español) sobre `norma.search_vector` |
| Broker / cache | Redis 7 |
| Workers | Celery 5 + beat (cron de ingesta) |
| Frontend | Next.js 16 App Router · React 19 · Tailwind 4 · Recharts |
| Iconos | Lucide React |
| Conectores | InfoLEG / Boletín Oficial (live) · HCDN/Senado (roadmap) |
| Despliegue | Vercel (web) + AWS (api+workers+db+redis) |

## Instalación (desarrollo)

Requisitos: Python 3.12+, Node 20+ con pnpm 9+, Docker Desktop.

```powershell
# 1. Levantar Postgres (pgvector) + Redis
docker compose up -d db redis

# 2. Crear venv e instalar packages Python editables
python -m venv .venv
.venv\Scripts\pip install -e packages\shared -e packages\connectors -e apps\workers -e apps\api

# 3. Migraciones
$env:DATABASE_URL="postgresql+asyncpg://vigia:vigia@localhost:5432/vigia"
.venv\Scripts\alembic -c db\alembic.ini upgrade head

# 4. Carga inicial de datos reales (muestreo InfoLEG ~990 normas)
.venv\Scripts\python -c "from vigia_workers.tasks import ingest_infoleg as t; print(t())"

# 5. API (http://localhost:8000/docs)
.venv\Scripts\python -m uvicorn vigia_api.main:app --reload --port 8000

# 6. Web (otra terminal — http://localhost:3000)
cd apps\web; pnpm install; pnpm dev
```

## Activar autenticación (Fase 2)

Por defecto la app corre en **modo demo** (datos públicos, sin login). Para
activar Google OAuth + multi-tenant, seteá en `.env` (API) y `apps/web/.env.local` (web):

```
AUTH_ENABLED=true                  # API
NEXT_PUBLIC_AUTH_ENABLED=true      # web
AUTH_SECRET=<openssl rand -hex 32> # compartido entre API y web
AUTH_GOOGLE_ID=<google client id>
AUTH_GOOGLE_SECRET=<google client secret>
```

Redirect URI de Google: `http://localhost:3000/api/auth/callback/google`.
Los endpoints de datos (`/normas`, `/search`, `/stats`) son públicos siempre;
la auth aplica a `/workspaces`, invitaciones y (Fase 3) alertas.

## Estructura del proyecto

```
vigia/
├── apps/
│   ├── api/          FastAPI (vigia_api) — /normas, /search, /stats, /health
│   ├── web/          Next.js 16 (App Router) — Feed, Dashboard, Buscador, Alertas, DNU
│   └── workers/      Celery + beat (vigia_workers) — ingesta InfoLEG
├── packages/
│   ├── connectors/   vigia_connectors — conector InfoLEG / Boletín Oficial
│   └── shared/       vigia_shared — modelos SQLAlchemy + schemas Pydantic + constantes
├── db/
│   ├── alembic/      migraciones (0001 inicial)
│   └── init/         extensiones pgvector, pg_trgm, unaccent
├── infra/caddy/      reverse proxy para prod
└── docker-compose.yml
```

> Nota: los archivos del SPA Vite original (`src/`, `index.html`, `vite.config.js`,
> `mockData.js`) quedaron en la raíz tras la migración a `apps/web` y ya no se usan;
> se pueden borrar con seguridad.

## Roadmap

- [x] **Fase 0** — Scaffold del monorepo (Docker, Postgres+pgvector, Alembic)
- [x] **Fase 1** — Datos reales end-to-end: conector InfoLEG → Postgres → API → web Next.js (sin mock)
- [x] **Fase 2** — Auth + multi-tenant: NextAuth + Google OAuth, `/auth/sync`, workspaces B2C/B2B, miembros e invitaciones (dormido en modo demo hasta setear credenciales)
- [x] **Fase 3** — Alertas persistentes por workspace + matching FTS + digest por email (Resend; no-op sin API key)
- [~] **Fase 4** — Deploy producción: config lista y verificada (Dockerfiles, `docker-compose.prod.yml`, CI a GHCR, Caddy, runbook [`infra/DEPLOY.md`](infra/DEPLOY.md)). Falta el push a AWS/Vercel (requiere credenciales)
- [ ] **Fase 5** — IA (resúmenes + NER), embeddings pgvector, scrapers BORA directo / Congreso

---

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE).
