'use client';

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, CartesianGrid,
} from 'recharts';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import { FileText, Shield, Scale, Gavel } from 'lucide-react';

const COLORS = ['#1e3a5f', '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#db2777', '#64748b'];

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded bg-bg-secondary">
          <Icon size={16} className="text-inst-blue" />
        </div>
      </div>
      <p className="text-2xl font-bold text-text-primary mb-0.5">{value}</p>
      <p className="text-[12px] font-medium text-text-primary">{title}</p>
      <p className="text-[11px] text-text-tertiary">{subtitle}</p>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-border-light rounded-lg p-3 shadow-lg">
      <p className="text-xs font-semibold text-text-primary mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-[11px] text-text-secondary">
          <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: entry.color }} />
          {entry.name}: <span className="font-semibold text-text-primary">{entry.value}</span>
        </p>
      ))}
    </div>
  );
}

export default function DashboardView() {
  const [dash, setDash] = useState(null);
  const [dnu, setDnu] = useState(null);

  useEffect(() => {
    api.dashboard().then(setDash).catch(() => setDash(null));
    api.dnuStats().then(setDnu).catch(() => setDnu(null));
  }, []);

  const tipoData = (dash?.por_tipo || []).map((t) => ({
    tipo: (TIPOS_NORMA[t.tipo] || TIPOS_NORMA.OTRA).label,
    cantidad: t.cantidad,
  }));
  const sectorData = (dash?.por_sector || []).map((s) => ({ name: s.sector, value: s.cantidad }));
  const leyes = dash?.por_tipo?.find((t) => t.tipo === 'LEY')?.cantidad ?? 0;
  const decretos = dash?.por_tipo?.find((t) => t.tipo === 'DECRETO')?.cantidad ?? 0;

  return (
    <div className="max-w-7xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Estadísticas</h2>
        <p className="text-sm text-text-tertiary">Producción legislativa y regulatoria — datos reales InfoLEG / Boletín Oficial</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard title="Normas ingestadas" value={dash?.total_normas ?? '—'} subtitle="Corpus actual" icon={FileText} />
        <StatCard title="DNU en seguimiento" value={dnu?.total ?? 0} subtitle={`${dnu?.pendientes ?? 0} pendientes bicameral`} icon={Shield} />
        <StatCard title="Leyes" value={leyes} subtitle="En el corpus" icon={Scale} />
        <StatCard title="Decretos" value={decretos} subtitle="En el corpus" icon={Gavel} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className="lg:col-span-2 card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-0.5">Normas por tipo</h3>
          <p className="text-[11px] text-text-tertiary mb-5">Distribución del corpus actual</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={tipoData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ebeef3" />
              <XAxis dataKey="tipo" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="cantidad" name="Normas" fill="#1e3a5f" radius={[4, 4, 0, 0]} barSize={36} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-text-primary mb-0.5">Por sector</h3>
          <p className="text-[11px] text-text-tertiary mb-4">Sectores detectados</p>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={sectorData} cx="50%" cy="50%" innerRadius={45} outerRadius={72} paddingAngle={1} dataKey="value">
                {sectorData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-3">
            {sectorData.slice(0, 6).map((s, i) => (
              <div key={s.name} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLORS[i] }} />
                <span className="text-[10px] text-text-secondary truncate">{s.name} ({s.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-0.5">Estado de DNU</h3>
        <p className="text-[11px] text-text-tertiary mb-5">Seguimiento bicameral</p>
        <div className="space-y-4">
          {[
            { label: 'Total en seguimiento', value: dnu?.total ?? 0, color: '#1e3a5f' },
            { label: 'Pendientes', value: dnu?.pendientes ?? 0, color: '#d97706' },
            { label: 'Aprobados', value: dnu?.aprobados ?? 0, color: '#059669' },
            { label: 'Rechazados', value: dnu?.rechazados ?? 0, color: '#dc2626' },
          ].map((item) => {
            const total = dnu?.total || 0;
            const pct = total ? (item.value / total) * 100 : 0;
            return (
              <div key={item.label}>
                <div className="flex justify-between text-[12px] mb-1.5">
                  <span className="text-text-secondary">{item.label}</span>
                  <span className="font-semibold text-text-primary">{item.value}</span>
                </div>
                <div className="w-full bg-bg-tertiary rounded-full h-1.5">
                  <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: item.color }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
