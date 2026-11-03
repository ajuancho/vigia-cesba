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

## Reportes

Módulo `/reportes` (solo usuarios logueados): constructor de reportes sobre el
corpus (sección, tipo de procedimiento, etapa, organismo, período, texto) con
listado, gráficos, CSV, impresión y análisis escrito con IA. Los reportes
guardados viven en la tabla `reporte` (migración `0009_reportes`).

Al actualizar a esta versión:

```bash
git pull
# Construir desde este repo: las imágenes ghcr.io/colossus-lab/* son las del
# upstream y NO traen los cambios del CESBA. La API suma la dependencia anthropic.
docker compose -f docker-compose.prod.yml build api migrate
docker compose -f docker-compose.prod.yml run --rm --no-deps migrate   # aplica 0009_reportes
docker compose -f docker-compose.prod.yml up -d --no-build api
```

**Historial:** los reportes analizan lo que haya en la base. Para tener un año
de licitaciones, backfill de 365 días (idempotente; ~365 llamadas a la API del
BOCBA) y después el matching silencioso del Paso 3:

```bash
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.tasks import ingest_bocba as t; print(t(lookback_days=365))"
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.alerts import match_alertas as t; print(t(notify=False))"
```

**Análisis con IA:** usa la misma configuración que los resúmenes
(`VIGIA_AI_PROVIDER`, ver "Resúmenes IA"). Apagado, el botón responde
`503 ia_no_configurada` y el resto del reporte funciona igual.

**Reportes programados** (migración `0010_reporte_programacion`): un reporte
guardado puede enviarse por email (diario, semanal o mensual, hora ART) con
resumen, primeras 25 filas, CSV adjunto y análisis IA opcional. Lo manda la task
`enviar_reportes_programados` del worker, cada 15 min por **celery beat**, así
que beat tiene que estar corriendo. Usa el mismo backend de email que las
alertas (`SMTP_*` o `RESEND_API_KEY`) y `WEB_BASE_URL` para el link "Abrir en
el monitor". Estado de cada envío en `reporte.ultimo_estado`.

En Railway: el push redeploya API y worker; la migración se aplica desde la
consola del servicio **worker** (`alembic -c db/alembic.ini upgrade head`).

**Límite actual:** montos y adjudicatarios no vienen en la API del BOCBA (solo
en el PDF de cada aviso); su extracción queda para una fase 2.

---

## Legislatura porteña

Fuente `legislatura`: expedientes de la Legislatura (proyectos de ley,
resolución, declaración, etc.) desde el web service del buscador oficial
(`parlamentaria.legislatura.gob.ar/webservices/Json.asmx/GetExpedienteAvanzada`,
no documentado). Se guardan en `norma` como `PROYECTO` con
`bora_seccion = 'Legislatura'`: entran en Buscador, Alertas y Reportes, tienen
su página `/legislatura` y NO aparecen en "Boletín del día".

Beat: diario 07:30 ART (expedientes iniciados en los últimos 30 días, con su
estado actual) y domingos 06:30 (refresco de estado de los últimos 400 días).

Primera carga (Railway: consola del servicio **worker**), sin migración:

```bash
python -c "from vigia_workers.tasks import ingest_legislatura as t; print(t(dry_run=True, lookback_days=7))"
python -c "from vigia_workers.tasks import ingest_legislatura as t; print(t(lookback_days=400))"
python -c "from vigia_workers.alerts import match_alertas as t; print(t(notify=False))"
```

Filtros por fuente (migración `0011_alerta_fuentes`): las alertas pueden
vigilar Boletín, Legislatura o ambas; el Buscador tiene filtro "Fuente" y en
Reportes la "Etapa" de un expediente es su estado de trámite (o "Sancionado").
Aplicar con `alembic -c db/alembic.ini upgrade head` desde la consola del worker.

El último comando registra los matches del backfill sin mandar emails (si no,
las alertas notificarían cientos de expedientes viejos). Si el servicio cambia
de formato, falla `packages/connectors/tests/test_legislatura.py` contra el
fixture y la fuente aparece en error en `GET /health/sources`.

---

## Membresías

No hay período de prueba: todos los workspaces tienen acceso pleno. Para
marcar un workspace como miembro (dato informativo):

```bash
# Ver todos los workspaces
docker compose -f docker-compose.prod.yml exec db \
  psql -U bocba bocba -c "SELECT slug, name, plan, created_at FROM workspace;"

# Otorgar membresía permanente
docker compose -f docker-compose.prod.yml exec db \
  psql -U bocba bocba -c "UPDATE workspace SET plan = 'member' WHERE slug = '<slug>';"
```

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
