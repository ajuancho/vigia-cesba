'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import { Clock, ArrowRight, Building2, Tag } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import CountUp from '@/components/CountUp';

const TIPO_TINT = {
  DNU: 'tint-red', DECRETO: 'tint-amber', LEY: 'tint-green', RESOLUCION: 'tint-blue',
  DISPOSICION: 'tint-purple', PROYECTO: 'tint-cyan', COMUNICACION: 'tint-pink',
  CONSULTA: 'tint-orange', OTRA: 'tint-gray',
};

const TIPO_DOT = {
  DNU: '#F87171', DECRETO: '#F6B40E', LEY: '#34D399', RESOLUCION: '#74ACDF',
  DISPOSICION: '#A78BFA', PROYECTO: '#22D3EE', COMUNICACION: '#F472B6',
  CONSULTA: '#FB923C', OTRA: '#8892A8',
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

function fmtEdicionFecha(iso) {
  const d = new Date(`${iso}T12:00:00`);
  const s = d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function resumenEdicion(ed) {
  const partes = Object.entries(ed.resumen || {})
    .filter(([t]) => t !== 'OTRA')
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([t, c]) => `${c} ${(TIPOS_NORMA[t]?.label || t).toLowerCase()}${c !== 1 ? (t === 'LEY' ? 'es' : 's') : ''}`);
  return partes.join(' · ');
}

/* Una edición del diario: header del día + destacados + trámite colapsado */
function Edicion({ edicion, onOpen }) {
  const [verTramite, setVerTramite] = useState(false);
  const tramiteCount = edicion.tramite_total || 0;

  return (
    <section className="mb-10">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-t-2 border-text-primary/70 pt-3 mb-1">
        <h3 className="text-[16px] font-bold text-text-primary" style={{ fontFamily: 'var(--font-display)' }}>
          {fmtEdicionFecha(edicion.fecha)}
        </h3>
        <p className="text-[10px] text-text-tertiary font-mono">{resumenEdicion(edicion)}</p>
      </div>

      {edicion.destacados.map((norma, i) => (
        <div key={norma.id} className="animate-fade-in" style={{ animationDelay: `${Math.min(i * 30, 300)}ms`, animationFillMode: 'both' }}>
          <NormRow norma={norma} index={i} onClick={() => onOpen(norma.id)} />
        </div>
      ))}
      {edicion.destacados.length === 0 && tramiteCount === 0 && (
        <p className="text-[12px] text-text-tertiary py-4">Sin publicaciones.</p>
      )}
      {edicion.destacados_total > edicion.destacados.length && (
        <p className="text-[11px] text-text-tertiary font-mono py-2">
          +{edicion.destacados_total - edicion.destacados.length} destacados más en el Buscador
        </p>
      )}

      {tramiteCount > 0 && (
        <div className="mt-1">
          <button
            onClick={() => setVerTramite((v) => !v)}
            className="group w-full flex items-center gap-2 py-2.5 text-left text-[12px] text-text-tertiary hover:text-text-secondary transition-colors"
          >
            <span className={`inline-block transition-transform duration-200 ${verTramite ? 'rotate-90' : ''}`}>▸</span>
            <span className="font-mono">{tramiteCount} de trámite</span>
            <span className="hidden sm:inline">— edictos, designaciones y ceremoniales</span>
            <span className="flex-1 border-b border-dashed border-border-light group-hover:border-border-medium transition-colors" />
          </button>
          {verTramite && (
            <div className="border-l border-border-light ml-1 mb-2">
              {edicion.tramite.map((n) => (
                <div
                  key={n.id}
                  onClick={() => onOpen(n.id)}
                  className="flex items-center gap-2 pl-4 py-1.5 cursor-pointer text-[12px] text-text-secondary hover:text-text-primary hover:bg-celeste/[0.03] transition-colors"
                >
                  <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: TIPO_DOT[n.tipo] || TIPO_DOT.OTRA, opacity: 0.6 }} />
                  <span className="truncate">{n.titulo}</span>
                  {n.organismo && <span className="text-[10px] text-text-tertiary shrink-0 hidden md:inline truncate max-w-[180px]">{n.organismo}</span>}
                </div>
              ))}
              {edicion.tramite_total > edicion.tramite.length && (
                <p className="pl-4 py-1.5 text-[10px] text-text-tertiary font-mono">
                  +{edicion.tramite_total - edicion.tramite.length} más
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function FeedView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // Deep-link desde el Universo: /feed?tipo=LEY&sector=Energía
  const tipoParam = searchParams.get('tipo');
  const sectorParam = searchParams.get('sector');
  const [filterTipo, setFilterTipo] = useState(
    tipoParam && TIPOS_NORMA[tipoParam] ? tipoParam : 'TODOS'
  );
  const [filterSector, setFilterSector] = useState(sectorParam || null);
  const [ediciones, setEdiciones] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [offsetDias, setOffsetDias] = useState(0);
  const [loading, setLoading] = useState(true);

  // El feed son ediciones diarias (como un diario): cambiar el filtro
  // resetea la paginación; "cargar más días" appendea.
  useEffect(() => {
    setLoading(true);
    api
      .ediciones({
        dias: 5,
        offset_dias: offsetDias,
        tipo: filterTipo !== 'TODOS' ? filterTipo : undefined,
        sector: filterSector || undefined,
      })
      .then((d) => {
        setEdiciones((prev) => (offsetDias === 0 ? d.ediciones : [...prev, ...d.ediciones]));
        setHasMore(d.has_more);
      })
      .catch(() => { setEdiciones([]); setHasMore(false); })
      .finally(() => setLoading(false));
  }, [filterTipo, filterSector, offsetDias]);

  const changeFilter = (setter) => (value) => { setOffsetDias(0); setter(value); };

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
              onClick={() => changeFilter(setFilterTipo)(tipo)}
              className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-200 border ${
                filterTipo === tipo
                  ? 'bg-celeste/10 text-celeste-bright border-celeste/40 scale-105'
                  : 'bg-transparent text-text-secondary border-border-light hover:border-celeste/30 hover:text-text-primary'
              }`}
            >
              {tipo === 'TODOS' ? 'Todos' : TIPOS_NORMA[tipo].label}
            </button>
          ))}
          {filterSector && (
            <button
              onClick={() => changeFilter(setFilterSector)(null)}
              className="px-3 py-1 rounded-full text-[11px] font-medium border bg-sol/10 text-sol border-sol/40 hover:border-sol transition-all"
              title="Quitar filtro de sector"
            >
              {filterSector} ×
            </button>
          )}
        </div>
      </FadeIn>

      {loading && ediciones.length === 0 ? (
        <div className="py-20 text-center">
          <p className="text-text-tertiary text-sm font-mono animate-pulse">Cargando el Boletín…</p>
        </div>
      ) : (
        <div>
          {ediciones.map((ed) => (
            <Edicion key={ed.fecha} edicion={ed} onOpen={(id) => router.push(`/norma/${id}`)} />
          ))}
        </div>
      )}

      {!loading && ediciones.length === 0 && (
        <div className="text-center py-16">
          <p className="text-text-tertiary text-sm">No hay normas que coincidan con el filtro.</p>
        </div>
      )}

      {hasMore && !loading && (
        <div className="text-center py-8">
          <button
            onClick={() => setOffsetDias((o) => o + 5)}
            className="px-5 py-2 rounded-full text-[12px] font-medium border border-border-light text-text-secondary hover:border-celeste/40 hover:text-celeste transition-colors"
          >
            Cargar ediciones anteriores ↓
          </button>
        </div>
      )}
      {loading && ediciones.length > 0 && (
        <p className="text-center py-6 text-[11px] font-mono text-text-tertiary animate-pulse">Cargando…</p>
      )}
    </div>
  );
}

export default function FeedPage() {
  return (
    <Suspense fallback={<div className="max-w-4xl mx-auto text-text-tertiary text-sm pt-6">Cargando…</div>}>
      <FeedView />
    </Suspense>
  );
}
