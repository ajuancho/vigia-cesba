# Vigía — Plan de trabajo pendiente

Estado al 2026-06-11: **Fases 0–4 + expansión multi-fuente DESPLEGADAS EN
PRODUCCIÓN**. Lo que sigue, en orden sugerido:

---

## 0. Expansión multi-fuente — ✅ DESPLEGADA (2026-06-11)

8 fuentes vivas en prod (verificado vía `/health/sources`, todas `ok`):
InfoLEG + HCDN proyectos (previas) + **BORA 1ª** (108 normas, frescura del
día — "esta semana" pasó de 0 a 110), **BCRA Comunicaciones** (300, hasta
A8445), **bicameral DNU** (228 dictaminados + 709 sin_tratamiento: el
tracker dejó de decir 1187 pendientes/0/0), **movimientos HCDN** (19.807
proyectos con estado real), **consultas públicas** (72 — ojo: la paginación
de DemocracyOS es 0-indexed), **BORA 2ª → Radar societario** (300 avisos,
FTS por razón social). Migraciones 0004/0005 aplicadas. Emails Resend
activos (dominio openarg.org verificado, key en el `.env` del EC2). Free
trial + cartel de membresía vivos.

Beat (ART): infoleg 03:00 · reconcile 04:30 · BORA 1ª 07:00+12:00 · HCDN
08:00/08:30 · bicameral 09:30 · BORA 2ª 10:30 · consultas 12:00 · BCRA
20:30 · match-alertas :15 · check-sources cada 6 h.

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

## 2. Emails de alertas (Resend) — ✅ LISTO salvo cargar la key en el EC2

**Dominio `openarg.org` VERIFICADO en Resend (2026-06-10)**: DKIM
(`resend._domainkey`) + SPF (MX/TXT en `send.openarg.org`) cargados en
Route53. Digest de alertas con links al detalle; emails de invitación a
workspaces al crearlas. La key NO está en el repo (a propósito) — al
desplegar, en el EC2:

```bash
# agregar a ~/vigia/.env.production Y ~/vigia/.env (la key la tiene el usuario):
RESEND_API_KEY=<la key de Resend>
ALERTS_FROM_EMAIL=Vigía <alertas@openarg.org>
WEB_BASE_URL=https://vigia.openarg.org
# opcional, avisos de fuentes caídas/estancadas:
OPS_ALERT_EMAIL=devops@colossuslab.org
```

→ restart api + worker. Probar: crear alerta con keyword frecuente → correr
`match_alertas` → revisar inbox.

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

**PLAN DE MEJORA — diseñado el 2026-06-11, NO implementar hasta validar la
plataforma actual con usuarios.** La decisión de diferir es deliberada: el
feed con jerarquía heurística funciona bien; la IA es refinamiento, no
necesidad.

**Vía: AWS Bedrock, calcando OpenArg** (verificado en
`../Open Arg/openarg_backend/src/app/infrastructure/adapters/llm/bedrock_llm_adapter.py`):
boto3 → `bedrock-runtime` con Converse API, región us-east-1, modelo
`us.anthropic.claude-haiku-4-5-20251001-v1:0`. La cuenta (812661756823) ya
tiene acceso a los modelos porque OpenArg los usa. Sin API keys: IAM puro,
los datos no salen de la cuenta.

**Orden de implementación sugerido (por valor):**
1. **`impacto` + `resumen_ia` en una sola pasada** (mismo prompt): task
   post-ingesta (~13:30 ART, después de todas las fuentes) que toma las
   normas del día con `impacto IS NULL` y completa impacto
   (alto/medio/bajo), resumen en castellano llano y entidades básicas.
   `impacto` refina el split destacado/trámite de
   `vigia_shared/relevancia.py` (la heurística regex queda de fallback) y
   alimenta el filtro de impacto que ya existe en API + UI.
2. **NER (`entidades`)**: empresas/organismos/leyes citadas → habilita
   "seguir a una empresa" cruzando normas + avisos societarios + BCRA.
3. **Embeddings pgvector** (extensión ya instalada; OpenArg tiene
   `BedrockEmbeddingAdapter` para calcar): búsqueda semántica + alertas
   semánticas (más allá del keyword FTS).

**Prerequisito de infra (único)**: instance profile para el EC2
`vigia-production` con `bedrock:InvokeModel` — aprovechar y sumarle
`s3:PutObject` para los backups (§3), un solo rol para ambos pendientes.

**Costo estimado**: ~200 normas/día × ~1.5k tokens con Haiku 4.5 ≈ $5-10/mes.
Backfill histórico opcional por lotes empezando por lo reciente (todo el
corpus ≈ $300 — no vale la pena de entrada).

Las columnas destino (`impacto`, `resumen_ia`, `entidades`) existen vacías
desde la migración 0001 y la API ya las expone: no hay migración.

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
