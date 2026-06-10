'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import { Clock, ArrowRight, Building2, Tag } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import CountUp from '@/components/CountUp';

const TIPO_TINT = {
  DNU: 'tint-red', DECRETO: 'tint-amber', LEY: 'tint-green', RESOLUCION: 'tint-blue',
  DISPOSICION: 'tint-purple', PROYECTO: 'tint-cyan', COMUNICACION: 'tint-pink', OTRA: 'tint-gray',
};

const TIPO_DOT = {
  DNU: '#F87171', DECRETO: '#F6B40E', LEY: '#34D399', RESOLUCION: '#74ACDF',
  DISPOSICION: '#A78BFA', PROYECTO: '#22D3EE', COMUNICACION: '#F472B6', OTRA: '#8892A8',
};

const IMPACTO_TINT = { alto: 'tint-red', medio: 'tint-amber', bajo: 'tint-gray' };

function WeekTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-navy-700 border border-border-medium rounded-lg px-3 py-2 shadow-lg">
      <p className="text-[10px] font-mono text-text-tertiary mb-0.5">semana del {label}</p>
      <p className="text-[12px] font-bold text-text-primary font-mono">{payload[0].value.toLocaleString('es-AR')} normas</p>
    </div>
  );
}

/* Strip de actividad semanal — flotante, sin card */
function ActivityStrip() {
  const [weeks, setWeeks] = useState([]);

  useEffect(() => {
    api.series({ months: 3, granularity: 'week' }).then(setWeeks).catch(() => {});
  }, []);

  if (!weeks.length) return null;
  const data = weeks.map((w) => ({ semana: w.mes.slice(5), total: w.total }));
  const lastFull = weeks.length > 1 ? weeks[weeks.length - 2] : weeks[weeks.length - 1];

  return (
    <FadeIn delay={80}>
      <div className="mb-8 border-t-2 border-text-primary/70 pt-4">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="shrink-0">
            <p className="eyebrow mb-2"><span className="eyebrow-num">ACTIVIDAD</span><span className="ml-2">últimas 12 semanas</span></p>
            <p className="font-mono font-bold text-4xl text-celeste leading-none">
              <CountUp value={lastFull?.total || 0} />
            </p>
            <p className="text-[11px] text-text-tertiary mt-1">normas la semana pasada</p>
          </div>
          <div className="flex-1 min-w-[260px] max-w-xl">
            <ResponsiveContainer width="100%" height={72}>
              <BarChart data={data} margin={{ top: 4, bottom: 0, left: 0, right: 0 }}>
                <XAxis dataKey="semana" tick={{ fill: '#636E85', fontSize: 9 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <Tooltip content={<WeekTooltip />} cursor={{ fill: 'rgba(116,172,223,0.07)' }} />
                <Bar dataKey="total" radius={[2, 2, 0, 0]} animationDuration={900}>
                  {data.map((_, i) => (
                    <Cell key={i} fill={i >= data.length - 1 ? '#F6B40E' : '#74ACDF'} fillOpacity={i >= data.length - 1 ? 0.9 : 0.55} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </FadeIn>
  );
}

function NormRow({ norma, onClick, index }) {
  const tipoMeta = TIPOS_NORMA[norma.tipo] || TIPOS_NORMA.OTRA;
  return (
    <div
      onClick={onClick}
      className="group cursor-pointer border-b border-border-light py-4 transition-all duration-300 hover:bg-celeste/[0.03] hover:pl-3"
      style={{ animationDelay: `${Math.min(index * 35, 400)}ms` }}
    >
      <div className="flex items-start gap-3">
        <div className="w-1 self-stretch rounded-full shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" style={{ backgroundColor: TIPO_DOT[norma.tipo] || TIPO_DOT.OTRA }} />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-semibold uppercase tracking-wide border ${TIPO_TINT[norma.tipo] || TIPO_TINT.OTRA}`}>
              {tipoMeta.label}{norma.numero ? ` ${norma.numero}` : ''}
            </span>
            {norma.impacto && (
              <span className={`px-2 py-0.5 rounded-full text-[9px] font-medium border ${IMPACTO_TINT[norma.impacto]}`}>
                impacto {norma.impacto}
              </span>
            )}
            {norma.fecha_publicacion && (
              <span className="text-[10px] text-text-tertiary ml-auto flex items-center gap-1 font-mono shrink-0">
                <Clock size={9} /> {norma.fecha_publicacion}
              </span>
            )}
          </div>

          <h3 className="text-[14px] font-semibold text-text-primary leading-snug mb-1 group-hover:text-celeste-bright transition-colors" style={{ fontFamily: 'var(--font-display)' }}>
            {norma.titulo}
          </h3>

          {norma.resumen && (
            <p className="text-[12px] text-text-secondary leading-relaxed line-clamp-2 mb-1.5">{norma.resumen}</p>
          )}

          <div className="flex flex-wrap items-center gap-3 text-[10px] text-text-tertiary">
            {norma.organismo && <span className="flex items-center gap-1 truncate max-w-[280px]"><Building2 size={10} /> {norma.organismo}</span>}
            {norma.sector && <span className="flex items-center gap-1"><Tag size={10} /> {norma.sector}</span>}
            <span className="ml-auto flex items-center gap-1 text-celeste font-medium opacity-0 group-hover:opacity-100 transition-all shrink-0">
              Ver detalle <ArrowRight size={10} className="group-hover:translate-x-0.5 transition-transform" />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FeedView() {
  const router = useRouter();
  const [filterTipo, setFilterTipo] = useState('TODOS');
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listNormas({ tipo: filterTipo !== 'TODOS' ? filterTipo : undefined, limit: 30 })
      .then(setData)
      .catch(() => setData({ items: [], total: 0 }))
      .finally(() => setLoading(false));
  }, [filterTipo]);

  return (
    <div className="max-w-4xl mx-auto">
      <FadeIn>
        <div className="mb-7 pt-2">
          <p className="eyebrow mb-1"><span className="eyebrow-num">VIGÍA / FEED</span><span className="ml-2">Lo último publicado</span></p>
          <h2 className="display-section text-text-primary mb-1">Feed <em>normativo.</em></h2>
          <p className="text-[13px] text-text-tertiary font-mono">Boletín Oficial · Congreso · actualización diaria</p>
        </div>
      </FadeIn>

      <ActivityStrip />

      {/* Filtros flotantes */}
      <FadeIn delay={140}>
        <div className="flex flex-wrap items-center gap-2 mb-2 pb-4 border-b border-border-light">
          {['TODOS', ...Object.keys(TIPOS_NORMA)].map((tipo) => (
            <button
              key={tipo}
              onClick={() => setFilterTipo(tipo)}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-200 border ${
                filterTipo === tipo
                  ? 'bg-celeste/10 text-celeste-bright border-celeste/40 scale-105'
                  : 'bg-transparent text-text-secondary border-border-light hover:border-celeste/30 hover:text-text-primary'
              }`}
            >
              {tipo === 'TODOS' ? 'Todos' : TIPOS_NORMA[tipo].label}
            </button>
          ))}
          <span className="ml-auto text-[11px] text-text-tertiary font-mono">
            {loading ? '…' : <><span className="text-text-primary font-bold">{data.total.toLocaleString('es-AR')}</span> normas</>}
          </span>
        </div>
      </FadeIn>

      {loading ? (
        <div className="py-20 text-center">
          <p className="text-text-tertiary text-sm font-mono animate-pulse">Cargando el Boletín…</p>
        </div>
      ) : (
        <div>
          {data.items.map((norma, i) => (
            <div key={norma.id} className="animate-fade-in" style={{ animationDelay: `${Math.min(i * 35, 400)}ms`, animationFillMode: 'both' }}>
              <NormRow norma={norma} index={i} onClick={() => router.push(`/norma/${norma.id}`)} />
            </div>
          ))}
        </div>
      )}

      {!loading && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-text-tertiary text-sm">No hay normas que coincidan con el filtro.</p>
        </div>
      )}
    </div>
  );
}
