'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Building2, Search, ExternalLink, Clock } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

const SELECT_CLS =
  'w-full bg-transparent border-b border-border-light px-1 py-2 text-[12px] text-text-secondary focus:outline-none focus:border-celeste transition-colors';

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
