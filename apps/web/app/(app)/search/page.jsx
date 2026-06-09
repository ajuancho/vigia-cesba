'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TIPOS_NORMA, SECTORES, JURISDICCIONES } from '@/lib/constants';
import { Search as SearchIcon, SlidersHorizontal, ArrowRight } from 'lucide-react';

const TIPO_DOT_COLORS = {
  DNU: '#dc2626', DECRETO: '#d97706', LEY: '#059669',
  RESOLUCION: '#2563eb', DISPOSICION: '#7c3aed', PROYECTO: '#0891b2', OTRA: '#64748b',
};

export default function SearchView() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [tipo, setTipo] = useState('');
  const [sector, setSector] = useState('');
  const [jurisdiccion, setJurisdiccion] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState([]);
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    const active = query || tipo || sector || jurisdiccion;
    if (!active) {
      setResults([]);
      setTouched(false);
      return;
    }
    setTouched(true);
    const t = setTimeout(() => {
      api
        .search({ q: query, tipo, sector, jurisdiccion, limit: 50 })
        .then((r) => setResults(r.hits || []))
        .catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(t);
  }, [query, tipo, sector, jurisdiccion]);

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Buscador</h2>
        <p className="text-sm text-text-tertiary">Búsqueda full-text sobre normativa argentina</p>
      </div>

      <div className="card p-1.5 mb-3 flex items-center gap-2 focus-within:border-inst-accent transition-colors">
        <SearchIcon size={16} className="text-text-tertiary ml-2.5 shrink-0" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar por norma, sector, organismo, keyword..."
          className="flex-1 bg-transparent text-[13px] text-text-primary placeholder-text-tertiary focus:outline-none py-2.5"
        />
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`p-2 rounded transition-colors ${showFilters ? 'bg-navy-800 text-white' : 'text-text-tertiary hover:bg-bg-secondary'}`}
        >
          <SlidersHorizontal size={14} />
        </button>
      </div>

      {showFilters && (
        <div className="card p-4 mb-3 grid grid-cols-1 md:grid-cols-3 gap-3 animate-slide-up">
          <div>
            <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Tipo</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="w-full bg-white border border-border-light rounded px-3 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-inst-accent">
              <option value="">Todos</option>
              {Object.entries(TIPOS_NORMA).map(([key, val]) => <option key={key} value={key}>{val.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Sector</label>
            <select value={sector} onChange={(e) => setSector(e.target.value)} className="w-full bg-white border border-border-light rounded px-3 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-inst-accent">
              <option value="">Todos</option>
              {SECTORES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Jurisdicción</label>
            <select value={jurisdiccion} onChange={(e) => setJurisdiccion(e.target.value)} className="w-full bg-white border border-border-light rounded px-3 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-inst-accent">
              <option value="">Todas</option>
              {JURISDICCIONES.map((j) => <option key={j} value={j}>{j}</option>)}
            </select>
          </div>
        </div>
      )}

      <p className="text-[11px] text-text-tertiary mb-3">
        {touched ? <><span className="font-semibold text-text-primary">{results.length}</span> resultados</> : 'Ingresá un término para buscar'}
      </p>

      <div className="space-y-2">
        {results.map((norma) => (
          <div
            key={norma.id}
            onClick={() => router.push(`/norma/${norma.id}`)}
            className="card card-hover p-4 cursor-pointer group transition-all"
          >
            <div className="flex items-start gap-3">
              <div className="w-1 h-10 rounded-full shrink-0 mt-0.5" style={{ backgroundColor: TIPO_DOT_COLORS[norma.tipo] || TIPO_DOT_COLORS.OTRA }} />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: TIPO_DOT_COLORS[norma.tipo] || TIPO_DOT_COLORS.OTRA }}>
                    {(TIPOS_NORMA[norma.tipo] || TIPOS_NORMA.OTRA).label} {norma.numero || ''}
                  </span>
                  {norma.fecha_publicacion && <span className="text-[11px] text-text-tertiary">{norma.fecha_publicacion}</span>}
                </div>
                <h4 className="text-[13px] font-semibold text-text-primary group-hover:text-inst-accent transition-colors mb-0.5 truncate">{norma.titulo}</h4>
                <p className="text-[12px] text-text-tertiary line-clamp-1">{norma.snippet || norma.resumen}</p>
                {norma.tags && norma.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {norma.tags.map((tag) => (
                      <span key={tag} className="text-[9px] px-2 py-0.5 bg-bg-secondary text-text-tertiary rounded border border-border-light">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
              <ArrowRight size={12} className="text-text-tertiary group-hover:text-inst-accent shrink-0 mt-2 transition-colors" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
