'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { TIPOS_NORMA, TIPOS_CABA, SECTORES, FUENTES } from '@/lib/constants';
import { Search as SearchIcon, SlidersHorizontal, ArrowRight, X } from 'lucide-react';
import { detectarFuente } from '@/lib/fuentes';
import FadeIn from '@/components/FadeIn';

const TIPO_DOT_COLORS = {
  DNU: '#A0175A', DECRETO: '#4DB4B0', LEY: '#1D1D1B',
  RESOLUCION: '#E62580', DISPOSICION: '#8F82BA', PROYECTO: '#D3D93A',
  COMUNICACION: '#6E6E68', CONSULTA: '#B4B4AE', OTRA: '#93938D',
};

const SELECT_CLS = 'w-full bg-transparent border-b border-border-light px-1 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-celeste transition-colors';

function SearchView() {
  const router = useRouter();
  const params = useSearchParams();
  const [query, setQuery] = useState(params.get('q') || '');
  const [tipo, setTipo] = useState('');
  const [sector, setSector] = useState('');
  const [fuente, setFuente] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [touched, setTouched] = useState(false);
  const [ignorarDeteccion, setIgnorarDeteccion] = useState(false);

  // "vivienda boletín oficial": el nombre de la fuente se aplica como filtro y
  // se quita del texto (las normas no dicen "boletín oficial" en su contenido).
  const det = detectarFuente(query);
  const usarDeteccion = Boolean(det.fuente) && !ignorarDeteccion && (!fuente || fuente === det.fuente);
  const fuenteEfectiva = fuente || (usarDeteccion ? det.fuente : '');
  const texto = usarDeteccion ? det.texto : query;

  useEffect(() => { if (!det.fuente) setIgnorarDeteccion(false); }, [det.fuente]);

  const elegirFuente = (key) => {
    setFuente(key);
    if (!key && det.fuente) setIgnorarDeteccion(true);
  };

  useEffect(() => {
    const active = texto || tipo || sector || fuenteEfectiva;
    if (!active) {
      setResults([]);
      setTotal(0);
      setTouched(false);
      return;
    }
    setTouched(true);
    const t = setTimeout(() => {
      api
        .search({ q: texto, tipo, sector, fuente: fuenteEfectiva, limit: 50 })
        .then((r) => { setResults(r.hits || []); setTotal(r.total || 0); })
        .catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(t);
  }, [texto, tipo, sector, fuenteEfectiva]);

  return (
    <div className="max-w-4xl mx-auto">
      <FadeIn>
        <div className="mb-7 pt-2">
          <p className="eyebrow mb-1"><span className="eyebrow-num">MONITOR / SEARCH</span><span className="ml-2">Full-text en español</span></p>
          <h2 className="display-section text-text-primary mb-1">Buscar en <em>todo el corpus</em></h2>
          <p className="text-[13px] text-text-tertiary font-mono">boletín oficial, legislatura y tribunal superior · ranking por relevancia y fragmentos en contexto</p>
        </div>
      </FadeIn>

      {/* Barra de búsqueda flotante — solo una hairline */}
      <FadeIn delay={100}>
        <div className="flex items-center gap-3 border-b-2 border-text-primary/70 pb-3 mb-4 focus-within:border-celeste transition-colors duration-300">
          <SearchIcon size={18} className="text-text-tertiary shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="litio, ciberseguridad, régimen penal tributario…"
            autoFocus
            className="flex-1 bg-transparent text-[16px] text-text-primary placeholder-text-tertiary focus:outline-none py-1"
            style={{ fontFamily: 'var(--font-display)' }}
          />
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-all duration-200 ${showFilters ? 'bg-celeste/15 text-celeste scale-105' : 'text-text-tertiary hover:text-text-primary'}`}
          >
            <SlidersHorizontal size={15} />
          </button>
        </div>
      </FadeIn>

      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5 animate-slide-up">
          <div>
            <label className="eyebrow text-[9px] block mb-1">Tipo</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className={SELECT_CLS}>
              <option value="">Todos</option>
              {TIPOS_CABA.map((key) => <option key={key} value={key}>{TIPOS_NORMA[key].label}</option>)}
            </select>
          </div>
          <div>
            <label className="eyebrow text-[9px] block mb-1">Sector</label>
            <select value={sector} onChange={(e) => setSector(e.target.value)} className={SELECT_CLS}>
              <option value="">Todos</option>
              {SECTORES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      )}

      {/* Fuente: siempre a la vista */}
      <div className="flex flex-wrap items-center gap-2 mb-3" role="group" aria-label="Fuente">
        {[['', 'Todas'], ...Object.entries(FUENTES)].map(([key, label]) => {
          const on = fuenteEfectiva === key;
          return (
            <button key={key || 'todas'} type="button" onClick={() => elegirFuente(key)} aria-pressed={on}
              className={`text-[12px] px-3 min-h-9 rounded-full border transition-colors ${
                on ? 'bg-carbon text-white border-carbon' : 'bg-white text-text-secondary border-border-medium hover:border-cian'
              }`}>
              {label}
            </button>
          );
        })}
      </div>
      {usarDeteccion && !fuente && (
        <p className="flex flex-wrap items-center gap-2 text-[12px] text-text-tertiary mb-3" role="status">
          <span className="inline-flex items-center gap-1.5 pl-3 pr-1.5 min-h-8 rounded-full bg-lima text-carbon font-semibold">
            Fuente: {FUENTES[det.fuente]}
            <button type="button" onClick={() => setIgnorarDeteccion(true)} aria-label="Quitar el filtro de fuente y buscar esas palabras"
              className="inline-flex items-center justify-center w-6 h-6 rounded-full hover:bg-carbon/10">
              <X size={13} />
            </button>
          </span>
          <span>detectada en tu búsqueda{det.texto ? <> · buscando «{det.texto}»</> : ''}</span>
        </p>
      )}

      <p className="text-[11px] text-text-tertiary mb-2 font-mono">
        {touched
          ? <><span className="font-bold text-text-primary">{total.toLocaleString('es-AR')}</span> resultados{results.length < total ? ` · mostrando ${results.length}` : ''}</>
          : 'Escribí un término para buscar'}
      </p>

      <div>
        {results.map((norma, i) => (
          <div
            key={norma.id}
            onClick={() => router.push(`/norma/${norma.id}`)}
            className="group cursor-pointer border-b border-border-light py-3.5 transition-all duration-300 hover:bg-celeste/[0.03] hover:pl-3 animate-fade-in"
            style={{ animationDelay: `${Math.min(i * 30, 350)}ms`, animationFillMode: 'both' }}
          >
            <div className="flex items-start gap-3">
              <div className="w-1 self-stretch rounded-full shrink-0 opacity-70 group-hover:opacity-100 transition-opacity" style={{ backgroundColor: TIPO_DOT_COLORS[norma.tipo] || TIPO_DOT_COLORS.OTRA }} />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                  <span className="text-[9px] font-semibold uppercase tracking-[0.1em]" style={{ color: TIPO_DOT_COLORS[norma.tipo] || TIPO_DOT_COLORS.OTRA }}>
                    {(TIPOS_NORMA[norma.tipo] || TIPOS_NORMA.OTRA).label} {norma.numero || ''}
                  </span>
                  {norma.fecha_publicacion && <span className="text-[10px] text-text-tertiary font-mono">{norma.fecha_publicacion}</span>}
                </div>
                <h4 className="text-[13px] font-semibold text-text-primary group-hover:text-celeste-bright transition-colors mb-0.5 truncate" style={{ fontFamily: 'var(--font-display)' }}>
                  {norma.titulo}
                </h4>
                <p className="text-[12px] text-text-tertiary line-clamp-1">{norma.snippet || norma.resumen_ia || norma.resumen}</p>
              </div>
              <ArrowRight size={12} className="text-text-tertiary group-hover:text-celeste group-hover:translate-x-0.5 shrink-0 mt-2 transition-all" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={null}>
      <SearchView />
    </Suspense>
  );
}
