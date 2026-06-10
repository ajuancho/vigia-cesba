'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { api } from '@/lib/api';
import { Clock, ArrowRight, Scale, Building2 } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import CountUp from '@/components/CountUp';

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-navy-700 border border-border-medium rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[10px] font-mono text-text-tertiary mb-0.5">{label}</p>
      <p className="text-[12px] font-bold text-text-primary font-mono">{payload[0].value} DNU</p>
    </div>
  );
}

export default function DNUTrackerView() {
  const router = useRouter();
  const [dnu, setDnu] = useState(null);
  const [normas, setNormas] = useState([]);

  useEffect(() => {
    api.dnuStats().then(setDnu).catch(() => {});
    api.listNormas({ tipo: 'DNU', limit: 30 }).then((d) => setNormas(d.items || [])).catch(() => {});
  }, []);

  const hist = (dnu?.historico || []).filter((d) => d.anio >= 1994);
  const anioActual = new Date().getFullYear();
  const dnuEsteAnio = hist.find((h) => h.anio === anioActual)?.cantidad ?? 0;
  const pico = hist.reduce((m, h) => (h.cantidad > m.cantidad ? h : m), { anio: '—', cantidad: 0 });

  const KPIS = [
    { label: 'Históricos', value: dnu?.total, sub: 'en seguimiento', color: 'text-text-primary' },
    { label: `En ${anioActual}`, value: dnuEsteAnio, sub: 'emitidos este año', color: 'text-status-red' },
    { label: 'Pendientes', value: dnu?.pendientes, sub: 'sin dictamen bicameral', color: 'text-sol' },
    { label: `Pico: ${pico.anio}`, value: pico.cantidad, sub: 'el año más intenso', color: 'text-celeste' },
  ];

  return (
    <div className="max-w-5xl mx-auto">
      <FadeIn>
        <div className="mb-7 pt-2">
          <p className="eyebrow mb-1"><span className="eyebrow-num">VIGÍA / DNU</span><span className="ml-2">Decretos de Necesidad y Urgencia</span></p>
          <h2 className="display-section text-text-primary mb-1">El Ejecutivo, <em>legislando.</em></h2>
          <p className="text-[13px] text-text-tertiary font-mono">seguimiento bicameral · Art. 99 inc. 3 CN</p>
        </div>
      </FadeIn>

      {/* Contexto editorial */}
      <FadeIn delay={80}>
        <div className="flex items-start gap-3 border-l-2 border-sol pl-4 py-1 mb-10">
          <Scale size={14} className="text-sol shrink-0 mt-0.5" />
          <p className="text-[12px] text-text-secondary leading-relaxed max-w-2xl">
            Los DNU son medidas legislativas dictadas por el Poder Ejecutivo en circunstancias excepcionales.
            <strong className="text-sol"> Mantienen vigencia por aprobación tácita</strong>: solo caen si ambas
            cámaras los rechazan. La Comisión Bicameral tiene 10 días para dictaminar.
          </p>
        </div>
      </FadeIn>

      {/* KPIs monumentales */}
      <div className="grid grid-cols-2 lg:grid-cols-4 border-t-2 border-text-primary/70 mb-12">
        {KPIS.map(({ label, value, sub, color }, i) => (
          <FadeIn key={label} delay={i * 90} className="h-full">
            <div className="pt-5 pb-6 lg:border-r border-border-light lg:px-5 first:pl-0 h-full transition-colors duration-300 hover:bg-celeste/[0.03]">
              <p className={`font-mono font-bold tracking-tight text-[clamp(2rem,3.5vw,3rem)] leading-none mb-2 ${color}`}>
                {value != null ? <CountUp value={value} /> : '—'}
              </p>
              <p className="text-[13px] font-bold text-text-primary mb-0.5" style={{ fontFamily: 'var(--font-display)' }}>{label}</p>
              <p className="text-[11px] text-text-tertiary">{sub}</p>
            </div>
          </FadeIn>
        ))}
      </div>

      {/* Histórico */}
      <section className="mb-12">
        <FadeIn>
          <p className="eyebrow mb-1"><span className="eyebrow-num">I.</span><span className="ml-2">Histórico 1994 → {anioActual}</span></p>
          <h3 className="text-[17px] font-bold text-text-primary mb-6" style={{ fontFamily: 'var(--font-display)' }}>
            Cada gestión deja <em className="text-sol italic">su huella.</em>
          </h3>
        </FadeIn>
        <FadeIn delay={120}>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={hist} margin={{ left: -14, right: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(116, 172, 223, 0.08)" vertical={false} />
              <XAxis dataKey="anio" tick={{ fill: '#636E85', fontSize: 9 }} axisLine={false} tickLine={false} interval={2} />
              <YAxis tick={{ fill: '#636E85', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(116,172,223,0.06)' }} />
              <Bar dataKey="cantidad" name="DNU" fill="#F87171" radius={[3, 3, 0, 0]} animationDuration={1100} />
            </BarChart>
          </ResponsiveContainer>
        </FadeIn>
      </section>

      {/* Recientes */}
      <section>
        <FadeIn>
          <p className="eyebrow mb-1"><span className="eyebrow-num">II.</span><span className="ml-2">Los últimos</span></p>
          <h3 className="text-[17px] font-bold text-text-primary mb-4" style={{ fontFamily: 'var(--font-display)' }}>
            DNU <em className="text-sol italic">recientes.</em>
          </h3>
        </FadeIn>
        <div className="border-t border-border-light">
          {normas.map((d, i) => (
            <div
              key={d.id}
              onClick={() => router.push(`/norma/${d.id}`)}
              className="group cursor-pointer border-b border-border-light py-3.5 transition-all duration-300 hover:bg-celeste/[0.03] hover:pl-3 animate-fade-in"
              style={{ animationDelay: `${Math.min(i * 35, 350)}ms`, animationFillMode: 'both' }}
            >
              <div className="flex items-start gap-3">
                <div className="w-1 self-stretch rounded-full bg-status-red shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" />
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-0.5">
                    <span className="text-[9px] font-semibold text-status-red uppercase tracking-[0.1em]">DNU {d.numero || ''}</span>
                    <span className="px-2 py-0.5 rounded-full text-[9px] font-medium border tint-amber">pendiente bicameral</span>
                    {d.fecha_publicacion && <span className="text-[10px] text-text-tertiary font-mono ml-auto flex items-center gap-1"><Clock size={9} /> {d.fecha_publicacion}</span>}
                  </div>
                  <h4 className="text-[13px] font-semibold text-text-primary group-hover:text-celeste-bright transition-colors mb-0.5" style={{ fontFamily: 'var(--font-display)' }}>{d.titulo}</h4>
                  {d.organismo && (
                    <p className="text-[10px] text-text-tertiary flex items-center gap-1"><Building2 size={9} /> {d.organismo}</p>
                  )}
                </div>
                <ArrowRight size={12} className="text-text-tertiary group-hover:text-celeste group-hover:translate-x-0.5 shrink-0 mt-2 transition-all" />
              </div>
            </div>
          ))}
          {normas.length === 0 && <p className="text-[12px] text-text-tertiary py-6">Cargando…</p>}
        </div>
      </section>
    </div>
  );
}
