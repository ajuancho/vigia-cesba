'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Scale, FileDown, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import FadeIn from '@/components/FadeIn';

const PAGE = 30;

// Secretarías del TSJ (raw.tipo_nombre del conector `vigia_connectors.tsj`).
const FILTROS = [
  { label: 'Todas', valor: null },
  { label: 'Laborales', valor: 'Asuntos Laborales' },
  { label: 'Civiles y Comerciales', valor: 'Asuntos Civiles y Comerciales' },
  { label: 'Contencioso Adm. y Tributarios', valor: 'Asuntos Contencioso Administrativos y Tributarios' },
  { label: 'Penales y Contravencionales', valor: 'Asuntos Penales, Penales Juveniles, Contravencionales y de Faltas' },
  { label: 'Originarios', valor: 'Asuntos Originarios y Relaciones con la Comunidad' },
  { label: 'Generales', valor: 'Asuntos Generales' },
];

const fmtFecha = (s) => (s ? s.split('-').reverse().join('/') : '—');

function temas(resumen) {
  const m = /Temas: (.+)\.$/.exec(resumen || '');
  return m ? m[1].split('; ') : [];
}

function Sentencia({ s }) {
  const t = temas(s.resumen);
  return (
    <article className="card card-hover px-5 py-4 mb-3">
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-[0.06em] tint-purple border">
          {s.tipo_nombre || 'Sentencia'}
        </span>
        <span className="text-[12px] font-semibold text-petroleo tabular-nums">Expte. {s.numero}</span>
        <span className="ml-auto text-[12px] text-text-tertiary inline-flex items-center gap-1 tabular-nums">
          <Clock size={12} /> {fmtFecha(s.fecha_publicacion)}
        </span>
      </div>
      <Link href={`/norma/${s.id}`} className="block text-[14px] font-semibold leading-snug text-petroleo hover:text-cian-hover">
        {s.titulo}
      </Link>
      {t.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {t.slice(0, 6).map((x) => (
            <span key={x} className="px-2 py-0.5 rounded-full text-[11px] border tint-gray">{x.toLowerCase()}</span>
          ))}
          {t.length > 6 && <span className="text-[11px] text-text-tertiary self-center">+{t.length - 6}</span>}
        </div>
      )}
      {s.url && (
        <div className="flex justify-end mt-2">
          <a href={s.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[12px] text-celeste font-semibold hover:text-petroleo">
            <FileDown size={13} /> Sentencia (PDF)
          </a>
        </div>
      )}
    </article>
  );
}

export default function TribunalView() {
  const [filtro, setFiltro] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(true);
  const [err, setErr] = useState('');

  const cargar = async (offset = 0) => {
    setCargando(true);
    setErr('');
    try {
      const r = await api.listNormas({ seccion: 'Tribunal Superior', tipo_nombre: filtro || undefined, limit: PAGE, offset });
      setItems((prev) => (offset === 0 ? r.items : [...prev, ...r.items]));
      setTotal(r.total);
    } catch {
      setErr('No se pudo cargar la información del Tribunal Superior.');
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
          <p className="eyebrow mb-1"><span className="eyebrow-num">BOCBA / TSJ</span><span className="ml-2">Jurisprudencia</span></p>
          <div className="title-rule flex flex-col gap-1">
            <h2 className="display-section text-text-primary">Tribunal <em>Superior</em></h2>
            <p className="text-[15px] text-text-tertiary">sentencias y resoluciones del tribunal superior de justicia de la ciudad · actualización diaria</p>
          </div>
        </div>
      </FadeIn>

      <div className="flex flex-wrap gap-2 mb-5 pb-4 border-b border-border-light" role="group" aria-label="Filtrar por secretaría">
        {FILTROS.map((f) => (
          <button key={f.label} type="button" onClick={() => setFiltro(f.valor)} aria-pressed={filtro === f.valor}
            className={`text-[12px] px-3 min-h-9 rounded border ${filtro === f.valor ? 'bg-petroleo text-white border-petroleo' : 'bg-white text-text-secondary border-border-medium hover:border-cian'}`}>
            {f.label}
          </button>
        ))}
        <span className="ml-auto self-center text-[12px] text-text-tertiary tabular-nums">{total.toLocaleString('es-AR')} resoluciones</span>
      </div>

      {err && <p role="alert" className="text-[13px] text-status-red mb-4">{err}</p>}

      {items.map((s) => <Sentencia key={s.id} s={s} />)}

      {!cargando && !err && items.length === 0 && (
        <div className="card p-6 text-[14px] text-text-tertiary flex items-center gap-3">
          <Scale size={20} strokeWidth={1.75} className="text-petroleo" />
          Todavía no hay sentencias cargadas. Se actualizan todos los días a las 7:45.
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
