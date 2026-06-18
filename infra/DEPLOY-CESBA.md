# Deploy — Monitor Normativo CABA (CESBA)

Runbook de despliegue de la instancia CABA del monitor, basada en el fork de Vigía.
La instancia está configurada para ingestar **exclusivamente el BOCBA** y mostrar
solo normativa porteña (`VIGIA_JURISDICCION_SCOPE=CABA`).

---

## Arquitectura

```
navegador ───▶ Vercel / servidor web   (apps/web — Next.js)
                      │ HTTPS
               ┌──────▼──────────────────────────┐
               │  Docker Compose (servidor CESBA) │
               │   Caddy (TLS) ──▶ api (FastAPI)  │
               │   worker + worker-beat (Celery)  │
               └──────┬──────────────┬────────────┘
                      │              │
                ┌─────▼──────┐  ┌───▼──────┐
                │ Postgres16 │  │  Redis   │
                │ +pgvector  │  │          │
                └────────────┘  └──────────┘
```

---

## Paso 1 — Clonar y configurar

```bash
git clone https://github.com/colossus-lab/vigia.git bocba
cd bocba

# Copiar y completar el .env
cp .env.cesba.example .env
# Editar .env: DATABASE_URL, REDIS_URL, AUTH_SECRET, dominios
```

---

## Paso 2 — Levantar la base y aplicar migraciones

```bash
# Levantar Postgres + Redis (all-in-one)
docker compose -f docker-compose.prod.yml --profile local-data up -d db redis

# Aplicar todas las migraciones (incluida 0008_bocba: índice + seed de fuente)
docker compose -f docker-compose.prod.yml run --rm --no-deps migrate
```

La migración `0008_bocba` crea el índice `ix_norma_jurisdiccion` y siembra la fila
`bocba` en `source_catalog`. Verificar:

```bash
docker compose -f docker-compose.prod.yml exec db \
  psql -U bocba bocba -c "SELECT code, name FROM source_catalog;"
```

---

## Paso 3 — Primer backfill del BOCBA

Ejecutar una ingesta inicial (últimos 30 días) para poblar la base antes de activar el beat:

```bash
# Dry-run primero (sin escribir en la DB)
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.tasks import ingest_bocba as t; print(t(dry_run=True, lookback_days=5))"

# Si el dry-run muestra normas, backfill real con lookback extendido
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "
from vigia_workers.tasks import ingest_bocba
from datetime import date, timedelta
import asyncio

# Ingestar los últimos 30 días hábiles de forma iterativa
result = ingest_bocba(dry_run=False, lookback_days=30)
print(result)
"

# Matching silencioso (no spamear alertas con normas viejas del backfill)
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.alerts import match_alertas as t; print(t(notify=False))"
```

---

## Paso 4 — Levantar la API y los workers

```bash
docker compose -f docker-compose.prod.yml --profile local-data pull
docker compose -f docker-compose.prod.yml --profile local-data up -d api worker worker-beat caddy
```

El beat schedule incluye solo las tasks BOCBA relevantes. **Los beats nacionales
(InfoLEG, BORA, HCDN, BCRA) están presentes en el código pero no impactan
negativamente** — simplemente no encontrarán configuración de fuente activa y
fallarán silenciosamente. Si se quiere deshabilitar explícitamente para ahorrar
llamadas, comentar las entradas correspondientes en `celery_app.py` antes del deploy.

---

## Paso 5 — Desplegar el frontend

### Opción A — Vercel (recomendado)

1. Vercel → New Project → importar el repo.
2. **Root Directory** → `apps/web`. Framework: Next.js.
3. Variables de entorno en Vercel:
   ```
   NEXT_PUBLIC_API_URL=https://normativa-api.cesba.gob.ar
   INTERNAL_API_URL=https://normativa-api.cesba.gob.ar
   NEXT_PUBLIC_AUTH_ENABLED=false
   AUTH_ENABLED=false
   AUTH_SECRET=<mismo valor que el backend>
   ```
4. Dominio: `normativa.cesba.gob.ar` (o el que defina el equipo CESBA).

### Opción B — Servidor propio

```bash
cd apps/web
npm install
npm run build
npm start  # o servir la carpeta .next con un proxy Nginx/Caddy
```

---

## Paso 6 — Activar Google OAuth (opcional)

Solo si se requiere login institucional (cuentas `@cesba.gob.ar` o `@buenosaires.gob.ar`).

En Google Cloud Console (proyecto CESBA/GCBA):
- **Authorized JavaScript origins**: `https://normativa.cesba.gob.ar`
- **Authorized redirect URIs**: `https://normativa.cesba.gob.ar/api/auth/callback/google`

En `.env`:
```bash
AUTH_GOOGLE_ID=<client id>
AUTH_GOOGLE_SECRET=<client secret>
AUTH_ENABLED=true
NEXT_PUBLIC_AUTH_ENABLED=true
```

Para restringir el login a dominios institucionales, configurar en Google Cloud:
`APIs & Services → OAuth consent screen → Authorized domains`.

---

## Verificación post-deploy

```bash
# Salud de la API
curl https://normativa-api.cesba.gob.ar/health
# → {"status":"ok"}

# Fuentes registradas (debe aparecer bocba en ok)
curl https://normativa-api.cesba.gob.ar/health/sources
# → [..., {"code":"bocba","status":"ok","max_fecha":"2026-06-18",...}]

# Normas CABA (todas deben tener jurisdiccion=CABA)
curl "https://normativa-api.cesba.gob.ar/normas?limit=3" | python -m json.tool

# Búsqueda full-text
curl "https://normativa-api.cesba.gob.ar/search?q=salud&limit=5"
```

**Web**: abrir `https://normativa.cesba.gob.ar/feed` → debe mostrar el boletín
del día con normas porteñas. El badge del header debe decir
`"● Datos reales · Boletín Oficial CABA"`.

---

## Operación diaria

### Beat schedule activo (BOCBA)

| Task | Horario | Descripción |
|---|---|---|
| `ingest-bocba` | 09:00 ART | Ingesta principal del boletín del día |
| `ingest-bocba-retry` | 13:00 ART | Retry si el boletín salió tarde |
| `match-alertas` | cada hora (:15) | Notificaciones a usuarios suscritos |
| `check-sources` | cada 6h (:45) | SLO de frescura — alerta si el BOCBA se atrasa |
| `purge-audit-log` | dom 05:00 ART | Retención de logs (Ley 25.326) |

### Ver estado de las fuentes (sin SSH)

```
GET /health/sources
```

Campos relevantes: `last_run_at`, `last_status` (`ok` / `warn` / `error`),
`max_fecha_publicacion`, `stale` (bool).

### Forzar una ingesta manual

```bash
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.tasks import ingest_bocba as t; print(t())"
```

### Rollback de una ingesta (si los datos quedaron mal)

```sql
-- Conectarse al Postgres y borrar las normas de bocba
DELETE FROM norma
WHERE source_id = (SELECT id FROM source_catalog WHERE code = 'bocba');
```

Luego forzar una re-ingesta manual.

---

## Resúmenes IA (opcional)

Para activar los resúmenes automáticos de cada norma en lenguaje claro,
configurar en `.env`:

```bash
# Con AWS Bedrock (IAM role del servidor — recomendado)
VIGIA_AI_PROVIDER=bedrock
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_HAIKU=us.anthropic.claude-haiku-4-5-20251001-v1:0

# O con API directa de Anthropic
VIGIA_AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=<api key>
```

Los resúmenes aparecen en el feed como "Análisis automático" debajo de cada norma.

---

## Otorgar membresía (bypass del trial)

Para que los usuarios del CESBA no vean el cartel de trial:

```bash
# Ver todos los workspaces
docker compose -f docker-compose.prod.yml exec db \
  psql -U bocba bocba -c "SELECT slug, name, plan, created_at FROM workspace;"

# Otorgar membresía permanente
docker compose -f docker-compose.prod.yml exec db \
  psql -U bocba bocba -c "UPDATE workspace SET plan = 'member' WHERE slug = '<slug>';"
```

O simplemente dejar `VIGIA_TRIAL_DAYS=3650` en el `.env` (10 años de trial
efectivo — adecuado para uso interno sin facturación).

---

## Costos estimados (self-hosted, Argentina)

| Componente | Opción económica | Opción recomendada |
|---|---|---|
| Servidor backend | VPS 2 vCPU / 4 GB RAM (~$10/mo) | Instancia AWS t3.small (~$15/mo) |
| Base de datos | Misma VPS (all-in-one) | RDS t4g.micro (~$13/mo) |
| Redis | Misma VPS | ElastiCache t4g.micro (~$12/mo) |
| Frontend | Vercel (free) | Vercel Pro o Nginx en la misma VPS |
| **Total** | **~$10/mo** | **~$40/mo** |

Para volumen bajo (CESBA, herramienta interna), el **all-in-one en una VPS de $10/mo**
es más que suficiente.
