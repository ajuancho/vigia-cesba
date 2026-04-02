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

| Componente | Tecnología |
|---|---|
| Frontend | React 19 + Vite 7 |
| Estilos | Tailwind CSS v4 |
| Gráficos | Recharts |
| Routing | React Router v7 |
| Iconos | Lucide React |
| Tipografía | Inter + JetBrains Mono |

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/ColossusLab/Vigia-normativo-Colossus-Lab.git
cd Vigia-normativo-Colossus-Lab

# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev
```

## Estructura del proyecto

```
src/
├── components/
│   ├── Sidebar.jsx         # Navegación principal
│   └── Header.jsx          # Barra superior
├── data/
│   └── mockData.js         # Datos simulados
├── views/
│   ├── FeedView.jsx        # Feed de normativa
│   ├── DashboardView.jsx   # Estadísticas y KPIs
│   ├── SearchView.jsx      # Buscador con filtros
│   ├── AlertsView.jsx      # Gestión de alertas
│   ├── NormDetailView.jsx  # Detalle de norma
│   └── DNUTrackerView.jsx  # Tracker de DNU
├── App.jsx                 # Router + Layout
├── index.css               # Design system
└── main.jsx                # Entry point
```

## Roadmap

- [ ] Backend: scrapers para BORA, Congreso, InfoLEG
- [ ] IA: reemplazar análisis simulados con NLP real
- [ ] Auth: login con Firebase para alertas persistentes
- [ ] Datos reales: conectar APIs de datos abiertos
- [ ] Deploy: hosting en producción

---

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENSE).
