'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Landmark, ExternalLink, Users, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import FadeIn from '@/components/FadeIn';

const PAGE = 30;

// Tipos de expediente más frecuentes (raw.tipo_nombre del conector).
const FILTROS = [
  { label: 'Todos', valor: null },
  { label: 'Proyectos de ley', valor: 'Proyecto de ley' },
  { label: 'Resoluciones', valor: 'Proyecto de resolución' },
  { label: 'Declaraciones', valor: 'Proyecto de declaración' },
  { label: 'Decretos', valor: 'Proyecto de decreto' },
];

const fmtFecha = (s) => (s ? s.split('-').reverse().join('/') : '—');

function autoria(resumen) {
  const m = /Autoría: (.+)\.$/.exec(resumen || '');
  if (!m) return null;
  const autores = m[1].split('; ');
  return autores.length > 2 ? `${autores[0]} y ${autores.length - 1} más` : autores.join(' y ');
}

function Expediente({ e }) {
  const sancionado = (e.estado || '').includes('SANCIONADO');
  const estado = (e.estado || '').replace(' · SANCIONADO', '');
  return (
    <article className="card card-hover px-5 py-4 mb-3">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-[0.06em] tint-green border">
          {e.tipo_nombre || 'Expediente'}
        </span>
        <span className="text-[12px] font-semibold text-petroleo tabular-nums">Expte. {e.numero}</span>
        {sancionado && (
          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-[0.06em] bg-petroleo text-white">Sancionado</span>
        )}
        <span className="ml-auto text-[12px] text-text-tertiary inline-flex items-center gap-1 tabular-nums">
          <Clock size={12} /> {fmtFecha(e.fecha_publicacion)}
        </span>
      </div>
      <Link href={`/norma/${e.id}`} className="block text-[15px] font-semibold leading-snug text-petroleo hover:text-cian-hover">
        {e.titulo}
      </Link>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[12px] text-text-tertiary">
        {autoria(e.resumen) && <span className="inline-flex items-center gap-1"><Users size={12} /> {autoria(e.resumen)}</span>}
        {estado && <span>{estado.toLowerCase()}</span>}
        {e.url && (
          <a href={e.url} target="_blank" rel="noopener noreferrer" className="ml-auto inline-flex items-center gap-1 text-celeste font-semibold hover:text-petroleo">
            Ver en la Legislatura <ExternalLink size={12} />
          </a>
        )}
      </div>
    </article>
  );
}

export default function LegislaturaView() {
  const [filtro, setFiltro] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [err, setErr] = useState('');

  const cargar = async (offset = 0) => {
    setCargando(true);
    setErr('');
    try {
      const r = await api.listNormas({ seccion: 'Legislatura', tipo_nombre: filtro || undefined, limit: PAGE, offset });
      setItems((prev) => (offset === 0 ? r.items : [...prev, ...r.items]));
      setTotal(r.total);
    } catch {
      setErr('No se pudo cargar la información de la Legislatura.');
      if (offset === 0) setItems([]);
    }
    setCargando(false);
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { cargar(0); }, [filtro]);

  return (
    <div className="max-w-4xl mx-auto">
      <FadeIn>
        <div className="mb-7 pt-2">
          <p className="eyebrow mb-1"><span className="eyebrow-num">BOCBA / LEGISLATURA</span><span className="ml-2">Expedientes parlamentarios</span></p>
          <div className="title-rule flex flex-col gap-1">
            <h2 className="display-section text-text-primary">Legislatura <em>porteña</em></h2>
            <p className="text-[15px] text-text-tertiary">proyectos y expedientes ingresados, con su estado actual · actualización diaria</p>
          </div>
        </div>
      </FadeIn>

      <div className="flex flex-wrap gap-2 mb-5 pb-4 border-b border-border-light" role="group" aria-label="Filtrar por tipo">
        {FILTROS.map((f) => (
          <button key={f.label} type="button" onClick={() => setFiltro(f.valor)} aria-pressed={filtro === f.valor}
            className={`text-[12px] px-3 min-h-9 rounded border ${filtro === f.valor ? 'bg-petroleo text-white border-petroleo' : 'bg-white text-text-secondary border-border-medium hover:border-cian'}`}>
            {f.label}
          </button>
        ))}
        <span className="ml-auto self-center text-[12px] text-text-tertiary tabular-nums">{total.toLocaleString('es-AR')} expedientes</span>
      </div>

      {err && <p role="alert" className="text-[13px] text-status-red mb-4">{err}</p>}

      {items.map((e) => <Expediente key={e.id} e={e} />)}

      {!cargando && !err && items.length === 0 && (
        <div className="card p-6 text-[14px] text-text-tertiary flex items-center gap-3">
          <Landmark size={20} strokeWidth={1.75} className="text-petroleo" />
          Todavía no hay expedientes cargados. Se actualizan todos los días a las 7:30.
        </div>
      )}

      {items.length < total && (
        <button type="button" onClick={() => cargar(items.length)} disabled={cargando}
          className="mt-2 text-[12px] font-semibold uppercase tracking-[0.06em] text-celeste hover:text-petroleo min-h-10 disabled:opacity-50">
          {cargando ? 'Cargando…' : `Cargar ${Math.min(PAGE, total - items.length)} más`}
        </button>
      )}
    </div>
  );
}
