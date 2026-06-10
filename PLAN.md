# Vigía — Plan de trabajo pendiente

Estado al 2026-06-10: **Fases 0–4 completas y en producción** (web + API + datos
completos con actualización diaria automática). Lo que sigue, en orden sugerido:

---

## 1. Google OAuth — activar login real ⬅️ PRÓXIMO

Hoy el sitio corre en **modo demo** (`AUTH_ENABLED=false`): datos públicos sin
login, alertas solo client-side. Todo el backend de auth (Fase 2: `/auth/sync`,
workspaces, invitaciones, JWT) y el de alertas (Fase 3: persistencia + matching
+ digests) ya está construido y verificado — solo le falta la llave.

### Pasos (requiere acción del usuario en Google Cloud Console)
1. Crear proyecto en https://console.cloud.google.com → APIs & Services →
   Credentials → **Create OAuth client ID** (tipo: Web application):
   - Authorized JavaScript origins: `https://vigia.openarg.org`
   - Authorized redirect URI: `https://vigia.openarg.org/api/auth/callback/google`
   - (Para dev local agregar también `http://localhost:3000` y su callback.)
2. Configurar la OAuth consent screen (External, publicada).
3. Guardar `Client ID` y `Client Secret`.

### Pasos (los ejecuta Claude con las credenciales)
4. **Vercel** (production env): `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET`,
   `AUTH_SECRET` (el mismo del backend — está en `.env.production` del EC2),
   `AUTH_ENABLED=true`, `NEXT_PUBLIC_AUTH_ENABLED=true` → redeploy.
5. **EC2** (`~/vigia/.env.production` + `.env`): `AUTH_ENABLED=true` → restart api.
6. Probar el flujo completo: login Google → `/auth/sync` crea user+workspace →
   onboarding → crear alerta persistente → invitar un segundo usuario.

### Riesgo conocido
NextAuth `5.0.0-beta.31` + Next 16 tiene un issue con `headers()` async que
puede aparecer recién al activar OAuth real. Si revienta: bumpear `next-auth`
a la última beta o mover el sync a un route handler (documentado en
`../investarg` README, sección "Conocidos Fase 4").

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

- Senado (proyectos + sanciones) — CKAN datos.gob.ar.
- BORA segunda/tercera sección y avisos.
- Organismos: BCRA Comunicaciones (conector ya existe en `../investarg`), CNV, ENACOM.
- Estado de tratamiento de proyectos (dataset `movimientos-de-proyectos` de HCDN)
  para enriquecer `dnu_tracking`/estados.
