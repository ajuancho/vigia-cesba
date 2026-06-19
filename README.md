<h1 align="center">Monitor Normativo CABA — CESBA</h1>

<p align="center">
  <strong>La normativa porteña, al día.</strong><br>
  Monitoreo del Boletín Oficial de la Ciudad de Buenos Aires (BOCBA) — indexado,
  resumido en lenguaje claro y con alertas por email.
</p>

<p align="center">
  <sub>Herramienta interna del <a href="https://www.cesba.gob.ar">CESBA</a> — Consejo Económico
  y Social de la Ciudad de Buenos Aires.</sub>
</p>

---

## 🙏 Atribución y créditos

Este proyecto es una **adaptación (fork) de [Vigía](https://github.com/colossus-lab/vigia)**,
una plataforma open source de inteligencia legislativa y regulatoria desarrollada por
**[Colossus Lab](https://colossuslab.com.ar)** (familia [OpenArg](https://openarg.org)).

> El trabajo original — la arquitectura completa, los conectores, el pipeline de ingesta,
> el sistema de alertas, el frontend y todo el diseño — fue creado por Colossus Lab y se
> distribuye bajo Licencia MIT. Esta versión únicamente **adapta Vigía para el Boletín
> Oficial de la Ciudad de Buenos Aires** y lo rebrandea para uso interno del CESBA.
>
> **Todo el crédito por la base técnica corresponde a Colossus Lab.**
> Repositorio original: **https://github.com/colossus-lab/vigia**

Si este proyecto te resulta útil, considerá visitar y apoyar el trabajo original de
Colossus Lab.

---

## ¿Qué es esto?

El **Monitor Normativo CABA** centraliza, indexa y alerta sobre la producción normativa
de la Ciudad de Buenos Aires. En vez de leer el Boletín Oficial porteño a mano, accedés a
un solo radar que ingesta el BOCBA todos los días, lo organiza por tipo, organismo y sector,
y te avisa cuando algo que te importa se publica.

### Diferencias respecto del Vigía original

Esta adaptación se enfoca **exclusivamente en la jurisdicción CABA**:

- **Fuente única:** la [API REST oficial del BOCBA](https://api-restboletinoficial.buenosaires.gob.ar)
  (en lugar de las ocho fuentes nacionales del proyecto original).
- **Scope automático:** todas las consultas se acotan a `jurisdiccion = CABA` vía la
  variable `VIGIA_JURISDICCION_SCOPE`, sin filtros manuales en el frontend.
- **Branding CESBA:** paleta institucional GCBA, identidad del Consejo y módulos acotados
  a lo porteño (sin tracker de DNU nacionales ni radar societario).

---

## Módulos

### 📰 Boletín del día — `/feed`
El BOCBA del día como un diario: lo importante arriba, el trámite colapsado. Cada norma con
su tipo, organismo emisor y sector.

### 🔎 Buscador — `/search`
Búsqueda **full-text en español** sobre toda la normativa porteña indexada, con snippets
resaltados y filtros por tipo y sector.

### 🔔 Alertas — `/alerts` *(requiere cuenta)*
Suscribite por **keyword y sector**. Cuando una norma matchea tu criterio, te llega un
**digest por email**. El matching corre automáticamente cada hora.

### 📊 Estadísticas — `/dashboard`
El pulso normativo porteño en números: actividad por tipo y sector, organismos más activos
y tendencias históricas.

---

## Stack técnico

Heredado del proyecto original (Colossus Lab):

- **Backend:** FastAPI + SQLAlchemy 2.0 async + Postgres 16/pgvector
- **Workers:** Celery + Redis (ingesta diaria + matching de alertas vía beat schedule)
- **Frontend:** Next.js 16 (App Router) + NextAuth (Google OAuth)
- **Conector BOCBA:** cliente async sobre la API REST oficial (`packages/connectors`)

Guía de despliegue de esta instancia: [`infra/DEPLOY-CESBA.md`](infra/DEPLOY-CESBA.md).

---

## Licencia

Distribuido bajo [Licencia MIT](LICENSE) — **Copyright (c) 2026 Colossus Lab**.

Esta adaptación conserva la licencia y el copyright originales conforme exige la MIT.
Las modificaciones para CESBA se publican bajo los mismos términos.
