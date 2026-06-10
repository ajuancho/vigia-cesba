# Vigía — Plan de trabajo pendiente

Estado al 2026-06-10: **Fases 0–4 completas y en producción** + **expansión
multi-fuente implementada y verificada en local** (commits en `main` SIN
pushear — ver §0). Lo que sigue, en orden sugerido:

---

## 0. Deploy de la expansión multi-fuente — ⚠️ PENDIENTE (commits locales)

5 commits en `main` local listos (free trial + fundación + BORA 1ª + bicameral
DNU/BCRA + movimientos HCDN + consultas + Radar societario). Para desplegar:

1. `git push origin main` → CI (pytest + build de imágenes) + Vercel redeploya el web.
2. En el EC2: `git pull` + pull/up del compose (runbook `infra/DEPLOY.md`).
   El servicio `migrate` aplica 0004 (bicameral) y 0005 (aviso_societario).
3. Backfills (orden del runbook "Alta de una fuente nueva", con matching
   silencioso): `ingest_bora_primera()`, `ingest_bcra_comunicaciones(backfill=300)`,
   `ingest_bicameral_dnu()`, `ingest_hcdn_movimientos()`,
   `ingest_consultas_publicas()`, `ingest_bora_segunda(lookback_days=5)`.
4. Smoke: `/health/sources` todo `ok` (8 fuentes), `/stats/dashboard`
   recientes.semana > 0, `/stats/dnu` con dictaminados > 0.

Fuentes nuevas y beat (ART): BORA 1ª 07:00+12:00 · reconcile 04:30 · HCDN
movimientos 08:30 · bicameral 09:30 · BORA 2ª 10:30 · consultas 12:00 ·
BCRA 20:30 · check-sources cada 6 h.

**Pospuesto con motivo**: Senado (sin export estructurado de proyectos /
sanciones — los JSON de DatosAbiertos son administrativos; HCDN ya cubre
proyectos vía `exp_senado` y las sanciones llegan por BORA). ENRE/ENARGAS
(fusionados en ENREGE: sus resoluciones ya entran por BORA 1ª con organismo —
medir cobertura en prod antes de invertir en scraper del espejo CAMMESA).
UIF (requiere credenciales). Alertas sobre avisos societarios (extender el
matcher — fase posterior).

---

## 1. Google OAuth — ✅ ACTIVADO (2026-06-10)

Login con Google **vivo en producción**: OAuth client creado por el usuario
(proyecto GCP, redirect `https://vigia.openarg.org/api/auth/callback/google`),
env vars en Vercel (`AUTH_GOOGLE_ID/SECRET`, `AUTH_SECRET`, `AUTH_ENABLED`,
`NEXT_PUBLIC_AUTH_ENABLED`), API del EC2 en modo gated (`AUTH_ENABLED=true`).
Verificado: provider Google registrado en NextAuth, 401 sin token en
`/workspaces`, datos públicos intactos.

**Pendiente de validación humana:** completar un login real (necesita una
cuenta Google interactiva) → onboarding → alerta persistente → invitación.
Si el login falla con un error de `headers()`: es el known issue de NextAuth
v5-beta + Next 16 → bumpear `next-auth` (documentado en `../investarg`).

---

## 2. Emails de alertas (Resend)

El worker ya compone y "envía" digests (no-op sin API key). Activar:
1. Cuenta en https://resend.com → API key. Verificar dominio `openarg.org`
   (DNS records que da Resend) para enviar desde `alertas@openarg.org`.
2. En el EC2: `RESEND_API_KEY=...` en `.env.production`/`.env` → restart worker.
3. Probar: crear alerta con keyword frecuente → correr `match_alertas` → revisar inbox.

Alternativa sin cuenta nueva: AWS SES (ya hay cuenta AWS; requiere salir del
sandbox de SES y verificar dominio).

---

## 3. Backups de la base (S3)

Hoy los datos viven solo en el EBS del EC2 (la ingesta es re-ejecutable, pero
los datos de usuarios/alertas no).
1. Bucket `vigia-backups` + lifecycle (30 días).
2. IAM role mínimo (`s3:PutObject`) como instance profile del EC2.
3. Cron diario en el host: `docker compose exec -T db pg_dump -U vigia vigia | gzip | aws s3 cp - s3://vigia-backups/vigia-$(date +%F).sql.gz`.

## 4. Hardening menor

- `SENTRY_DSN` (API + workers ya lo soportan; web requiere agregar @sentry/nextjs).
- Snapshot/AMI del EC2 post-setup.
- Considerar staging si el producto suma usuarios reales.

## 5. Fase 5 — IA (diferida por decisión de producto)

- `resumen_ia` + entidades (NER) vía Bedrock/Anthropic (patrón InvestArg; env vars ya previstas).
- Embeddings pgvector (la extensión ya está instalada) para búsqueda semántica.
- Heurística/modelo de `impacto` (hoy null — el filtro del feed existe pero sin datos).

## 6. Más fuentes (backlog)

✅ Hecho en la expansión multi-fuente (ver §0): BORA 1ª y 2ª, BCRA
Comunicaciones, bicameral DNU, movimientos HCDN, consultas públicas.

Queda en backlog:
- Senado: re-evaluar si publican export estructurado de proyectos/sanciones
  (los actuales son administrativos); alternativa: scrape HTML de listados.
- BORA 3ª sección (contrataciones) — otro módulo estilo Radar societario.
- CNV, ENACOM, ARCA biblioteca propia (hoy cubiertos parcialmente vía BORA).
- SAIJ / normativa provincial (datos.jus.gob.ar) — radar provincial.
- Alertas sobre avisos societarios (matcher propio sobre aviso_societario).
