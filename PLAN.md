# Vigía — Plan de trabajo pendiente

Estado al 2026-06-10: **Fases 0–4 completas y en producción** (web + API + datos
completos con actualización diaria automática). Lo que sigue, en orden sugerido:

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

- Senado (proyectos + sanciones) — CKAN datos.gob.ar.
- BORA segunda/tercera sección y avisos.
- Organismos: BCRA Comunicaciones (conector ya existe en `../investarg`), CNV, ENACOM.
- Estado de tratamiento de proyectos (dataset `movimientos-de-proyectos` de HCDN)
  para enriquecer `dnu_tracking`/estados.
