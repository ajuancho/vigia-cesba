'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid, XAxis, YAxis,
} from 'recharts';
import { api } from '@/lib/api';
import { Building2, Search, ExternalLink, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import CountUp from '@/components/CountUp';

const SELECT_CLS =
  'w-full bg-transparent border-b border-border-light px-1 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-celeste transition-colors';

const RUBRO_COLORS = ['#74ACDF', '#F6B40E', '#34D399', '#A78BFA', '#F87171', '#93C5F8', '#FFD04A', '#8892A8'];

// Rubros vienen en MAYÚSCULAS del BORA; los mostramos en Sentence case.
const sentence = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s);

// top-N rubros + resto agrupado en "Otros" para que la torta sea legible.
function pieFromRubros(porRubro, topN = 7) {
  const sorted = [...(porRubro || [])].sort((a, b) => b.cantidad - a.cantidad);
  const slices = sorted.slice(0, topN).map((r) => ({ name: r.rubro, value: r.cantidad }));
  const resto = sorted.slice(topN).reduce((s, r) => s + r.cantidad, 0);
  if (resto > 0) slices.push({ name: 'Otros', value: resto });
  return slices;
}

function Delta({ actual, anterior }) {
  if (!anterior) return null;
  const pct = Math.round(((actual - anterior) / anterior) * 100);
  const up = pct > 0;
  const Icon = pct === 0 ? Minus : up ? TrendingUp : TrendingDown;
  const cls = pct === 0 ? 'text-text-tertiary' : up ? 'text-status-green' : 'text-status-red';
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold font-mono ${cls}`}>
      <Icon size={11} /> {up ? '+' : ''}{pct}%
    </span>
  );
}

function RubroTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="bg-navy-700 border border-border-medium rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[11px] font-bold text-text-primary">{sentence(p.name)}</p>
      <p className="text-[11px] font-mono text-text-tertiary">{p.value.toLocaleString('es-AR')} avisos</p>
    </div>
  );
}

function SemanaTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-navy-700 border border-border-medium rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[10px] font-mono text-text-tertiary mb-0.5">semana del {label}</p>
      <p className="text-[12px] font-bold text-text-primary font-mono">{payload[0].value.toLocaleString('es-AR')} avisos</p>
    </div>
  );
}

/* Panel societario: KPIs con delta + pulso semanal + torta por rubro (calca /dashboard). */
function SocietarioStats() {
  const [s, setS] = useState(null);

  useEffect(() => {
    api.avisosStats().then(setS).catch(() => {});
  }, []);

  if (!s || !s.total_historico) return null;
  const pie = pieFromRubros(s.por_rubro);
  const serie = (s.serie || []).map((p) => ({ semana: p.semana.slice(5), total: p.total }));

  const KPIS = [
    { label: 'Esta semana', value: s.semana, sub: 'vs. semana anterior', color: 'text-celeste', delta: <Delta actual={s.semana} anterior={s.semana_anterior} /> },
    { label: 'Últimos 30 días', value: s.mes, sub: 'vs. 30 días previos', color: 'text-sol', delta: <Delta actual={s.mes} anterior={s.mes_anterior} /> },
    { label: 'Rubros activos', value: s.rubros_distintos, sub: 'últimos 30 días', color: 'text-sol-bright', delta: null },
    { label: 'Total histórico', value: s.total_historico, sub: 'avisos indexados', color: 'text-text-primary', delta: null },
  ];

  return (
    <FadeIn delay={60}>
      <div className="mb-10">
        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 border-t-2 border-text-primary/70">
          {KPIS.map(({ label, value, sub, color, delta }, i) => (
            <div key={label} className="pt-4 pb-5 pr-4 lg:border-r border-border-light lg:px-5 first:pl-0">
              <p className={`font-mono font-bold tracking-tight text-[clamp(1.9rem,3.4vw,2.8rem)] leading-none mb-1.5 ${color}`}>
                {value != null ? <CountUp value={value} /> : '—'}
              </p>
              <div className="flex items-center gap-2 mb-0.5">
                <p className="text-[12px] font-bold text-text-primary" style={{ fontFamily: 'var(--font-display)' }}>{label}</p>
                {delta}
              </div>
              <p className="text-[10px] text-text-tertiary">{sub}</p>
            </div>
          ))}
        </div>

        {/* Pulso semanal + torta por rubro */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-8 mt-8">
          <div>
            <p className="eyebrow mb-3"><span className="eyebrow-num">PULSO</span><span className="ml-2">altas por semana · 12 semanas</span></p>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={serie} margin={{ left: -16, right: 4, top: 4 }}>
                <defs>
                  <linearGradient id="fillAvisos" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#74ACDF" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#74ACDF" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(116, 172, 223, 0.08)" vertical={false} />
                <XAxis dataKey="semana" tick={{ fill: '#636E85', fontSize: 9 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fill: '#636E85', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<SemanaTooltip />} cursor={{ stroke: 'rgba(116,172,223,0.2)' }} />
                <Area type="monotone" dataKey="total" stroke="#74ACDF" strokeWidth={2} fill="url(#fillAvisos)" animationDuration={1100} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div>
            <p className="eyebrow mb-3"><span className="eyebrow-num">TIPOS</span><span className="ml-2">por rubro · 30 días</span></p>
            <div className="flex items-center gap-3">
              <div className="w-[130px] h-[130px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pie} cx="50%" cy="50%" innerRadius={38} outerRadius={62} paddingAngle={1.5} dataKey="value" animationDuration={1000} stroke="none">
                      {pie.map((_, i) => (
                        <Cell key={i} fill={RUBRO_COLORS[i % RUBRO_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<RubroTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <ul className="flex-1 space-y-1 min-w-0">
                {pie.map((slice, i) => (
                  <li key={slice.name} className="flex items-center gap-2 text-[11px] text-text-secondary">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: RUBRO_COLORS[i % RUBRO_COLORS.length] }} />
                    <span className="truncate flex-1" title={sentence(slice.name)}>{sentence(slice.name)}</span>
                    <span className="font-mono text-text-tertiary shrink-0 tabular-nums">{slice.value}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </FadeIn>
  );
}

export default function AvisosView() {
  const [q, setQ] = useState('');
  const [rubro, setRubro] = useState('');
  const [rubros, setRubros] = useState([]);
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback((params) => {
    setLoading(true);
    api
      .listAvisos({ limit: 30, ...params })
      .then(setPage)
      .catch(() => setPage({ items: [], total: 0 }))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load({});
    api.avisosRubros({ days: 30 }).then(setRubros).catch(() => {});
  }, [load]);

  const submit = (e) => {
    e?.preventDefault();
    load({ q: q || undefined, rubro: rubro || undefined });
  };

  return (
    <div className="max-w-5xl mx-auto">
      <FadeIn>
        <div className="mb-7 pt-2">
          <p className="eyebrow mb-1">
            <span className="eyebrow-num">VIGÍA / SOCIETARIO</span>
            <span className="ml-2">Boletín Oficial · Segunda Sección</span>
          </p>
          <h2 className="display-section text-text-primary mb-1">
            Las empresas, <em>en movimiento.</em>
          </h2>
          <p className="text-[13px] text-text-tertiary font-mono">
            constituciones · asambleas · edictos — actualización diaria
          </p>
        </div>
      </FadeIn>

      <SocietarioStats />

      <FadeIn delay={80}>
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-[1fr_280px_auto] gap-4 mb-8 items-end">
          <div>
            <label className="text-[10px] font-mono uppercase tracking-[0.15em] text-text-tertiary">
              Razón social o palabra clave
            </label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="p. ej. una empresa que te interese vigilar"
              className={SELECT_CLS}
            />
          </div>
          <div>
            <label className="text-[10px] font-mono uppercase tracking-[0.15em] text-text-tertiary">Rubro</label>
            <select value={rubro} onChange={(e) => setRubro(e.target.value)} className={SELECT_CLS}>
              <option value="">Todos</option>
              {rubros.map((r) => (
                <option key={r.rubro} value={r.rubro}>
                  {r.rubro.slice(0, 60)} ({r.cantidad})
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="flex items-center gap-1.5 text-[12px] font-medium text-celeste border border-celeste/30 rounded-lg px-4 py-2 hover:bg-celeste/10 transition-colors"
          >
            <Search size={12} /> Buscar
          </button>
        </form>
      </FadeIn>

      <div className="border-t border-border-light">
        {loading && <p className="text-[12px] text-text-tertiary py-6 font-mono animate-pulse">Cargando…</p>}
        {!loading && page?.items?.length === 0 && (
          <p className="text-[12px] text-text-tertiary py-6">
            Sin avisos todavía. La ingesta diaria corre a las 10:30 — si buscaste algo, probá otra razón social.
          </p>
        )}
        {!loading &&
          (page?.items || []).map((a, i) => (
            <a
              key={a.id}
              href={a.url || '#'}
              target="_blank"
              rel="noreferrer"
              className="group block border-b border-border-light py-3.5 transition-all duration-300 hover:bg-celeste/[0.03] hover:pl-3 animate-fade-in"
              style={{ animationDelay: `${Math.min(i * 30, 300)}ms`, animationFillMode: 'both' }}
            >
              <div className="flex items-start gap-3">
                <Building2 size={13} className="text-text-tertiary group-hover:text-celeste shrink-0 mt-1 transition-colors" />
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-0.5">
                    {a.rubro && (
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-medium border tint-gray uppercase tracking-wide">
                        {a.rubro.slice(0, 50)}
                      </span>
                    )}
                    {a.fecha && (
                      <span className="text-[10px] text-text-tertiary font-mono ml-auto flex items-center gap-1">
                        <Clock size={9} /> {a.fecha}
                      </span>
                    )}
                  </div>
                  <h4
                    className="text-[13px] font-semibold text-text-primary group-hover:text-celeste-bright transition-colors"
                    style={{ fontFamily: 'var(--font-display)' }}
                  >
                    {a.razon_social || `Aviso ${a.aviso_id}`}
                  </h4>
                </div>
                <ExternalLink size={11} className="text-text-tertiary group-hover:text-celeste shrink-0 mt-2 transition-colors" />
              </div>
            </a>
          ))}
      </div>
      {page?.total > 0 && (
        <p className="text-[11px] text-text-tertiary font-mono mt-4">
          {page.items.length} de {page.total} avisos
        </p>
      )}
    </div>
  );
}
