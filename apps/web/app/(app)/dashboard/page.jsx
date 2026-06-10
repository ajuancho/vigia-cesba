'use client';

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, CartesianGrid, Legend,
} from 'recharts';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import { CalendarDays, CalendarRange, FileStack, Shield, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const COLORS = ['#74ACDF', '#F6B40E', '#34D399', '#A78BFA', '#F87171', '#93C5F8', '#FFD04A', '#8892A8'];

// Colores por tipo para la serie temporal (paleta Argentina).
const SERIE_TIPOS = [
  { key: 'RESOLUCION', color: '#74ACDF' },
  { key: 'DISPOSICION', color: '#5A8FBD' },
  { key: 'DECRETO', color: '#F6B40E' },
  { key: 'PROYECTO', color: '#22D3EE' },
  { key: 'LEY', color: '#34D399' },
  { key: 'DNU', color: '#F87171' },
  { key: 'OTRA', color: '#8892A8' },
];

function Delta({ actual, anterior }) {
  if (!anterior) return <span className="text-[10px] text-text-tertiary">—</span>;
  const pct = Math.round(((actual - anterior) / anterior) * 100);
  if (pct === 0) {
    return (
      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full tint-gray border inline-flex items-center gap-0.5">
        <Minus size={9} /> 0%
      </span>
    );
  }
  const up = pct > 0;
  return (
    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full border inline-flex items-center gap-0.5 ${up ? 'tint-green' : 'tint-red'}`}>
      {up ? <TrendingUp size={9} /> : <TrendingDown size={9} />} {up ? '+' : ''}{pct}%
    </span>
  );
}

function KpiCard({ title, value, subtitle, icon: Icon, delta }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-lg bg-celeste/10 border border-celeste/20">
          <Icon size={15} className="text-celeste" />
        </div>
        {delta}
      </div>
      <p className="text-2xl font-bold text-text-primary mb-0.5 font-mono">{value}</p>
      <p className="text-[12px] font-medium text-text-primary">{title}</p>
      <p className="text-[11px] text-text-tertiary">{subtitle}</p>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-navy-700 border border-border-medium rounded-lg p-3 shadow-lg">
      <p className="text-xs font-semibold text-text-primary mb-1 font-mono">{label}</p>
      {payload.filter((e) => e.value > 0).map((entry, i) => (
        <p key={i} className="text-[11px] text-text-secondary">
          <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: entry.color || entry.fill }} />
          {entry.name}: <span className="font-semibold text-text-primary font-mono">{entry.value.toLocaleString('es-AR')}</span>
        </p>
      ))}
    </div>
  );
}

const fmtMes = (ym) => {
  const [y, m] = ym.split('-');
  const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  return `${meses[parseInt(m, 10) - 1]} ${y.slice(2)}`;
};

export default function DashboardView() {
  const [dash, setDash] = useState(null);
  const [dnu, setDnu] = useState(null);
  const [serie, setSerie] = useState([]);
  const [organismos, setOrganismos] = useState([]);

  useEffect(() => {
    api.dashboard().then(setDash).catch(() => {});
    api.dnuStats().then(setDnu).catch(() => {});
    api.series({ months: 24 }).then(setSerie).catch(() => {});
    api.organismos({ days: 90, limit: 10 }).then(setOrganismos).catch(() => {});
  }, []);

  const rec = dash?.recientes;
  const sectorData = (dash?.por_sector || []).slice(0, 8).map((s) => ({ name: s.sector, value: s.cantidad }));
  const serieData = serie.map((p) => ({ mes: fmtMes(p.mes), ...p.por_tipo }));
  const maxOrg = organismos[0]?.cantidad || 1;
  const dnuHist = (dnu?.historico || []).filter((d) => d.anio >= 1994);

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Estadísticas</h2>
        <p className="text-sm text-text-tertiary">
          Pulso regulatorio sobre {dash ? dash.total_normas.toLocaleString('es-AR') : '…'} normas — InfoLEG / BORA / HCDN
        </p>
      </div>

      {/* KPIs con tendencia */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          title="Normas esta semana" value={rec ? rec.semana.toLocaleString('es-AR') : '—'}
          subtitle="vs. semana anterior" icon={CalendarDays}
          delta={rec && <Delta actual={rec.semana} anterior={rec.semana_anterior} />}
        />
        <KpiCard
          title="Últimos 30 días" value={rec ? rec.mes.toLocaleString('es-AR') : '—'}
          subtitle="vs. 30 días previos" icon={CalendarRange}
          delta={rec && <Delta actual={rec.mes} anterior={rec.mes_anterior} />}
        />
        <KpiCard
          title="Proyectos presentados" value={rec ? rec.proyectos_30d.toLocaleString('es-AR') : '—'}
          subtitle="Últimos 30 días · Congreso" icon={FileStack}
        />
        <KpiCard
          title={`DNU en ${new Date().getFullYear()}`} value={rec ? rec.dnu_anio.toLocaleString('es-AR') : '—'}
          subtitle={`${(dnu?.total ?? 0).toLocaleString('es-AR')} históricos en seguimiento`} icon={Shield}
        />
      </div>

      {/* Pulso regulatorio */}
      <div className="card p-5 mb-4">
        <h3 className="text-sm font-semibold text-text-primary mb-0.5">Pulso regulatorio</h3>
        <p className="text-[11px] text-text-tertiary mb-5">Producción normativa mensual por tipo — últimos 24 meses</p>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={serieData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(116, 172, 223, 0.10)" />
            <XAxis dataKey="mes" tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} formatter={(v) => (TIPOS_NORMA[v] || { label: v }).label} />
            {SERIE_TIPOS.map(({ key, color }) => (
              <Area
                key={key} type="monotone" dataKey={key} stackId="1"
                stroke={color} fill={color} fillOpacity={0.35} strokeWidth={1.2}
                name={key}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Quién regula */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-0.5">Quién regula</h3>
          <p className="text-[11px] text-text-tertiary mb-5">Top organismos emisores — últimos 90 días</p>
          <div className="space-y-3">
            {organismos.map((o, i) => (
              <div key={o.organismo}>
                <div className="flex items-baseline justify-between gap-3 mb-1">
                  <span className="text-[12px] text-text-secondary truncate" title={o.organismo}>
                    <span className="font-mono text-[10px] text-celeste mr-2">{String(i + 1).padStart(2, '0')}</span>
                    {o.organismo}
                  </span>
                  <span className="text-[12px] font-bold text-text-primary font-mono shrink-0">{o.cantidad.toLocaleString('es-AR')}</span>
                </div>
                <div className="w-full bg-bg-tertiary rounded-full h-1">
                  <div
                    className="h-1 rounded-full transition-all duration-700"
                    style={{ width: `${(o.cantidad / maxOrg) * 100}%`, backgroundColor: COLORS[i % COLORS.length] }}
                  />
                </div>
              </div>
            ))}
            {organismos.length === 0 && <p className="text-[12px] text-text-tertiary">Sin datos del período.</p>}
          </div>
        </div>

        {/* DNU histórico */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-0.5">DNU por año</h3>
          <p className="text-[11px] text-text-tertiary mb-5">Decretos de Necesidad y Urgencia desde 1994 — se nota cada gestión</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dnuHist}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(116, 172, 223, 0.10)" />
              <XAxis dataKey="anio" tick={{ fill: '#6B7280', fontSize: 9 }} axisLine={false} tickLine={false} interval={3} />
              <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="cantidad" name="DNU" fill="#F87171" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Por sector */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-0.5">Por sector</h3>
        <p className="text-[11px] text-text-tertiary mb-4">Distribución sectorial del corpus (detección automática)</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={sectorData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={1} dataKey="value">
                {sectorData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
            {sectorData.map((s, i) => (
              <div key={s.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                <span className="text-[11px] text-text-secondary truncate">{s.name}</span>
                <span className="text-[11px] font-mono text-text-primary ml-auto">{s.value.toLocaleString('es-AR')}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
