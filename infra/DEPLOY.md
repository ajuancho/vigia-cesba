# Deploy de Vigía — Runbook (Fase 4)

Arquitectura de producción (patrón Laboratorio Colossus):

```
                 ┌─────────────┐
   navegador ───▶│   Vercel    │  apps/web (Next.js 16)
                 └──────┬──────┘
                        │ HTTPS (NEXT_PUBLIC_API_URL)
                 ┌──────▼───────────────────────────┐
                 │ EC2  ·  docker compose            │
                 │  Caddy (TLS) ─▶ api (FastAPI)     │
                 │                worker + beat       │
                 └───────┬───────────────┬───────────┘
                         │               │
                   ┌─────▼─────┐   ┌──────▼──────┐
                   │ RDS PG16  │   │ ElastiCache │
                   │ +pgvector │   │   Redis     │
                   └───────────┘   └─────────────┘
```

- **Web** → Vercel (root `apps/web`).
- **Backend** (api + workers + beat) → EC2 con `docker-compose.prod.yml` + Caddy.
- **DB** → RDS Postgres 16 (pgvector). **Cache/broker** → ElastiCache Redis.
- Imágenes → GHCR (`ghcr.io/colossus-lab/vigia-{api,workers}`), via CI.

## Cuenta AWS

- Account `812661756823`, IAM user `dante` (AWS CLI v2 ya autenticado en el equipo).
- Verificar: `aws sts get-caller-identity`.
- Región sugerida: `us-east-1` (igual que el resto del lab / Bedrock).

---

## A. Aprovisionar infraestructura (una vez)

> Reemplazar `<...>`. Anotar los endpoints que devuelve cada comando.

### A.1 RDS Postgres 16 + pgvector
```bash
aws rds create-db-instance \
  --db-instance-identifier vigia-db \
  --engine postgres --engine-version 16 \
  --db-instance-class db.t4g.micro \
  --allocated-storage 20 --storage-type gp3 \
  --master-username vigia --master-user-password '<DB_PASS>' \
  --db-name vigia --backup-retention-period 7 \
  --vpc-security-group-ids <SG_DB> --no-publicly-accessible
```
Tras crearse, conectarse una vez y habilitar extensiones (las migra 0001 igual,
pero conviene dejarlas listas):
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

### A.2 ElastiCache Redis 7
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id vigia-redis \
  --engine redis --cache-node-type cache.t4g.micro \
  --num-cache-nodes 1 --security-group-ids <SG_REDIS>
```

### A.3 EC2 (backend host)
- AMI Amazon Linux 2023, `t3.small` (2 vCPU / 2 GB), 20 GB gp3.
- Security group: inbound 80/443 (mundo), 22 (tu IP). Outbound all.
- Instalar Docker + compose plugin:
  ```bash
  sudo dnf install -y docker && sudo systemctl enable --now docker
  sudo usermod -aG docker ec2-user
  # compose plugin
  sudo dnf install -y docker-compose-plugin || \
    (sudo mkdir -p /usr/local/lib/docker/cli-plugins && \
     sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
       -o /usr/local/lib/docker/cli-plugins/docker-compose && \
     sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose)
  ```
- Los SG de RDS y Redis deben permitir ingreso desde el SG del EC2 (5432 / 6379).

### A.4 Secrets (recomendado)
Guardar `AUTH_SECRET`, `AUTH_GOOGLE_*`, `RESEND_API_KEY`, `DATABASE_URL`,
`REDIS_URL` en AWS Secrets Manager y volcarlos a `.env.production` en el deploy:
```bash
aws secretsmanager create-secret --name vigia/prod --secret-string file://.env.production.json
```

---

## B. Construir y publicar imágenes

**Vía CI (recomendado):** push a `main` dispara `.github/workflows/build-images.yml`
→ publica `vigia-api` y `vigia-workers` a GHCR. Requiere que el repo tenga
permisos de packages (automático con `GITHUB_TOKEN`).

**Manual (desde el equipo):**
```bash
echo $GHCR_TOKEN | docker login ghcr.io -u <user> --password-stdin
docker build -t ghcr.io/colossus-lab/vigia-api:latest     -f apps/api/Dockerfile .
docker build -t ghcr.io/colossus-lab/vigia-workers:latest -f apps/workers/Dockerfile .
docker push ghcr.io/colossus-lab/vigia-api:latest
docker push ghcr.io/colossus-lab/vigia-workers:latest
```

---

## C. Desplegar el backend en EC2

```bash
# en el EC2
git clone https://github.com/colossus-lab/vigia.git && cd vigia
cp .env.production.example .env.production    # completar con los endpoints de A
docker login ghcr.io                          # si las imágenes son privadas

# levantar (RDS + ElastiCache externos). El servicio `migrate` aplica Alembic.
docker compose -f docker-compose.prod.yml up -d

# EC2 all-in-one (sin RDS/ElastiCache): agregar el perfil local-data
# docker compose -f docker-compose.prod.yml --profile local-data up -d
```

`migrate` corre `alembic upgrade head` antes de la API. Para cargar datos
iniciales (InfoLEG):
```bash
docker compose -f docker-compose.prod.yml run --rm worker \
  python -c "from vigia_workers.tasks import ingest_infoleg_full as t; print(t())"
```

### Caddy + DNS
- Apuntar `api.vigia.legal` (A record) a la IP elástica del EC2.
- `infra/caddy/Caddyfile` ya hace `reverse_proxy api:8000` con TLS automático
  (Let's Encrypt). Editar el dominio si difiere.

---

## D. Desplegar el web en Vercel

1. https://vercel.com/new → importar `colossus-lab/vigia`.
2. **Root Directory** → `apps/web`. Framework: Next.js. Install: `pnpm install`. Build: `pnpm build`.
3. Env vars en Vercel:
   ```
   NEXT_PUBLIC_API_URL=https://api.vigia.legal
   INTERNAL_API_URL=https://api.vigia.legal
   NEXT_PUBLIC_AUTH_ENABLED=true
   AUTH_ENABLED=true
   AUTH_SECRET=<mismo que el backend>
   AUTH_GOOGLE_ID=<google client id>
   AUTH_GOOGLE_SECRET=<google client secret>
   ```
4. Dominio: `vigia.legal` / `www.vigia.legal` (debe coincidir con `API_CORS_ORIGINS` del backend).

## E. Google OAuth

En Google Cloud Console → OAuth client (Web):
- Authorized origin: `https://vigia.legal`
- Redirect URI: `https://vigia.legal/api/auth/callback/google`

---

## F. Verificación post-deploy

```bash
curl https://api.vigia.legal/health                 # {"status":"ok"}
curl https://api.vigia.legal/health/detailed         # conteo de normas + fuentes
curl "https://api.vigia.legal/normas?limit=1"        # datos reales
```
- Web: abrir `https://vigia.legal/feed` → normas reales; login Google → onboarding.
- Crear una alerta → `match_alertas` corre por beat (o `docker compose ... run --rm worker python -c "from vigia_workers.alerts import match_alertas as t; print(t())"`) → llega email (si `RESEND_API_KEY`).

## Costos aproximados (us-east-1)
EC2 t3.small (~$15) + RDS t4g.micro (~$13) + ElastiCache t4g.micro (~$12) ≈ **$40/mo**.
Web en Vercel: free/pro. Bajar costos: EC2 all-in-one con perfil `local-data` (~$15/mo) hasta tener tráfico.

## Conocidos
- **NextAuth v5-beta ↔ Next 16**: si al activar OAuth real aparece el error de
  `headers()` async, bumpear `next-auth` a la primera versión que soporte Next 16
  nativo (mismo issue documentado en InvestArg).
- Endpoints de datos (`/normas`, `/search`, `/stats`) son públicos a propósito
  (datos legislativos abiertos); el gating aplica a `/workspaces` y `/alerts`.
