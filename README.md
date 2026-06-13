<p align="center">
  <a href="https://vigia.openarg.org">
    <img src="docs/hero.png" alt="Vigía — La normativa argentina, vigilada" width="100%">
  </a>
</p>

<h1 align="center">Vigía — Inteligencia Legislativa y Regulatoria</h1>

<p align="center">
  <strong>La normativa argentina, vigilada.</strong><br>
  Monitoreo del Boletín Oficial, el Congreso y el sector público — en tiempo real y en lenguaje claro.
</p>

<p align="center">
  <a href="https://vigia.openarg.org"><strong>🔗 Abrir Vigía → vigia.openarg.org</strong></a><br>
  <sub>Proyecto open source de <a href="https://colossuslab.com.ar">Colossus Lab</a> · familia <a href="https://openarg.org">OpenArg</a> · Licencia MIT</sub>
</p>

---

## ¿Qué es Vigía?

Vigía centraliza, analiza y alerta sobre toda la producción normativa argentina. En vez de leer
el Boletín Oficial a mano, accedés a un solo radar que ingesta **533.000+ normas** de ocho fuentes
oficiales, las resume con IA en lenguaje claro y te avisa cuando algo que te importa cambia.

Pensado para **empresas, estudios jurídicos y áreas de compliance** que necesitan saber, cada
mañana, qué se publicó y a quién afecta — sin ruido.

> **Empezá ahora:** entrá a **[vigia.openarg.org](https://vigia.openarg.org)**. El feed, el buscador
> y las estadísticas son **públicos** (no requieren cuenta). Crear una cuenta gratuita habilita las
> alertas por email y un workspace para tu equipo.

---

## Guía de uso

Vigía son **seis módulos, un solo radar**. Así se usa cada uno:

### 📰 Feed Normativo — `/feed`
El Boletín del día como un diario: lo importante arriba, el trámite colapsado. Cada norma nueva
viene con su **resumen IA** en lenguaje claro (qué resuelve y a quién afecta), su tipo (DNU, decreto,
ley, resolución, proyecto…), organismo y sector.

> **Tip:** filtrá por tipo o sector para quedarte solo con lo que te incumbe.

### 🔎 Buscador — `/search`
Búsqueda **full-text en español** sobre todo el corpus normativo. Escribí en lenguaje natural y
obtené resultados rankeados con snippets resaltados. Combiná con filtros por tipo, sector y
jurisdicción para acotar.

### 🔔 Alertas — `/alerts`  *(requiere cuenta)*
Suscribite por **keyword y sector**. Cuando una norma, comunicación o edicto matchea tu criterio,
te llega un **digest por email**. Ideal para vigilar un tema regulatorio, un organismo o una
palabra clave de tu industria sin revisar el feed todos los días.

1. Iniciá sesión y entrá a **Alertas**.
2. Creá una alerta con tus keywords y/o sectores.
3. Vigía hace el matching automáticamente (cada hora) y te notifica.

### 🛡️ Tracker DNU — `/dnu`
Seguimiento de cada **Decreto de Necesidad y Urgencia** con su estado bicameral real: dictaminados,
pendientes y sin tratamiento, derivado de los datos del Congreso.

### 🏢 Radar societario — `/avisos`
La **2ª sección del Boletín**, buscable: constituciones, asambleas y edictos societarios. Vigilá una
empresa por razón social y enterate de sus movimientos.

### 📊 Estadísticas — `/dashboard`
El pulso normativo en números: actividad por tipo y sector, organismos más activos y tendencias de
producción legislativa.

### 👤 Cuenta, workspaces y prueba gratuita
- **Modo demo:** sin login, con acceso público a los datos (feed, buscador, stats).
- **Cuenta gratuita:** habilita alertas y un **workspace** para tu equipo (miembros e invitaciones).
- **Prueba gratuita:** 30 días por workspace para las funciones gestionadas; al vencer se solicita
  pasar a un plan de miembro.

---

## Fuentes de datos

Datos **públicos y verificables**, refrescados cada mañana con SLOs de frescura por fuente:

- **Boletín Oficial (BORA)** — 1ª sección (normas) y 2ª sección (avisos societarios)
- **InfoLEG** — base de legislación nacional (Min. de Justicia)
- **HCDN — Diputados** — proyectos, movimientos y dictámenes
- **Comisión Bicameral de DNU** — estado de tratamiento
- **BCRA** — Comunicaciones "A"
- **Consultas públicas** nacionales

---

## Stack técnico

Monorepo full-stack en producción, calcado del patrón de InvestArg / Colossus Lab:

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI async · SQLAlchemy 2.0 · Pydantic v2 |
| Base de datos | PostgreSQL 16 + pgvector · Alembic |
| Búsqueda | Postgres FTS con GIN (español) sobre `norma.search_vector` |
| Broker / cache | Redis 7 |
| Workers | Celery 5 + beat (cron de ingesta y matching de alertas) |
| Frontend | Next.js 16 App Router · React 19 · Tailwind 4 · Recharts |
| Conectores | InfoLEG · BORA · HCDN · BCRA |
| Despliegue | Vercel (web) + AWS EC2 (API + workers + Postgres + Redis) |

**En producción:** web [vigia.openarg.org](https://vigia.openarg.org) (Vercel) ·
API [vigia-api.openarg.org](https://vigia-api.openarg.org) (EC2).

---

## Instalación (desarrollo)

Requisitos: Python 3.12+, Node 20+ con pnpm 9+, Docker.

```powershell
# 1. Levantar Postgres (pgvector) + Redis
docker compose up -d db redis

# 2. Crear venv e instalar los packages Python editables
python -m venv .venv
.venv\Scripts\pip install -e packages\shared -e packages\connectors -e apps\workers -e apps\api

# 3. Migraciones
$env:DATABASE_URL="postgresql+asyncpg://vigia:vigia@localhost:5432/vigia"
.venv\Scripts\alembic -c db\alembic.ini upgrade head

# 4. Carga inicial de datos de muestra (~990 normas, dataset de dev)
.venv\Scripts\python -c "from vigia_workers.tasks import ingest_infoleg as t; print(t())"

# 5. API (http://localhost:8000/docs)
.venv\Scripts\python -m uvicorn vigia_api.main:app --reload --port 8000

# 6. Web (otra terminal — http://localhost:3000)
cd apps\web; pnpm install; pnpm dev
```

> El dataset del paso 4 es un muestreo estático de 2022 (solo para dev). La frescura real la dan los
> workers diarios (`ingest_infoleg_full`, `ingest_hcdn_*`, BORA, BCRA) que corren en producción.

### Activar autenticación (Google OAuth)

Por defecto la app corre en **modo demo** (datos públicos, sin login). Para activar Google OAuth +
multi-tenant, seteá en `.env` (API) y `apps/web/.env.local` (web):

```
AUTH_ENABLED=true                  # API
NEXT_PUBLIC_AUTH_ENABLED=true      # web
AUTH_SECRET=<openssl rand -hex 32> # compartido entre API y web
AUTH_GOOGLE_ID=<google client id>
AUTH_GOOGLE_SECRET=<google client secret>
```

Los endpoints de datos (`/normas`, `/search`, `/stats`) son públicos siempre; la auth aplica a
`/workspaces`, invitaciones y alertas.

---

## Estructura del proyecto

```
vigia/
├── apps/
│   ├── api/          FastAPI (vigia_api) — routers: health, normas, search, stats, auth, workspaces, invitations, alerts, avisos
│   ├── web/          Next.js 16 (App Router) — Feed, Buscador, Alertas, DNU, Radar societario, Dashboard
│   └── workers/      Celery + beat (vigia_workers) — ingesta + matching de alertas
├── packages/
│   ├── connectors/   vigia_connectors — InfoLEG · BORA · HCDN · BCRA
│   └── shared/       vigia_shared — modelos SQLAlchemy + schemas Pydantic + constantes + registry de fuentes
├── db/alembic/       migraciones (0001 inicial, 0002 multitenant, 0003 alertas)
├── infra/            Caddyfile, ec2-user-data.sh, DEPLOY.md (runbook completo)
└── docker-compose.yml
```

---

## Roadmap

- [x] **Fase 0** — Scaffold del monorepo (Docker, Postgres+pgvector, Alembic)
- [x] **Fase 1** — Datos reales end-to-end: conector InfoLEG → Postgres → API → web Next.js
- [x] **Fase 2** — Auth + multi-tenant: NextAuth + Google OAuth, workspaces, miembros e invitaciones
- [x] **Fase 3** — Alertas persistentes por workspace + matching FTS + digest por email
- [x] **Fase 4** — **EN PRODUCCIÓN**: [vigia.openarg.org](https://vigia.openarg.org) + [vigia-api.openarg.org](https://vigia-api.openarg.org) (runbook [`infra/DEPLOY.md`](infra/DEPLOY.md))
- [x] **Fase 5** — Más fuentes (BORA directo, 2ª sección societaria, HCDN, BCRA) + resúmenes IA
- [ ] **Próximo** — Embeddings pgvector (búsqueda semántica), NER y más fuentes regulatorias (ver [`PLAN.md`](PLAN.md))

---

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE).
