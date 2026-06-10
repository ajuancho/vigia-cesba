'use client';

import { useEffect, useReducer } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';

/* Demo de búsqueda con tipeo (idioma del TranscriptDemo de OpenArg).
   Loop: type → hold → erase → siguiente query. Click lleva a /search?q=. */

const QUERIES = [
  'régimen minero litio salta',
  'DNU pendientes comisión bicameral',
  'ciberseguridad entidades financieras',
  'salario mínimo vital y móvil',
  'energía renovable beneficios fiscales',
];

const TYPE_MS = 45;
const HOLD_MS = 2100;
const ERASE_MS = 16;

function reducer(state, action) {
  switch (action.type) {
    case 'tick': {
      const q = QUERIES[state.idx];
      if (state.phase === 'typing') {
        if (state.typed.length < q.length) return { ...state, typed: q.slice(0, state.typed.length + 1) };
        return { ...state, phase: 'hold' };
      }
      if (state.phase === 'hold') return { ...state, phase: 'erasing' };
      if (state.phase === 'erasing') {
        if (state.typed.length > 0) return { ...state, typed: state.typed.slice(0, -1) };
        return { phase: 'typing', typed: '', idx: (state.idx + 1) % QUERIES.length };
      }
      return state;
    }
    default:
      return state;
  }
}

export default function TypingDemo() {
  const router = useRouter();
  const [state, dispatch] = useReducer(reducer, { phase: 'typing', typed: '', idx: 0 });

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const delay = state.phase === 'hold' ? HOLD_MS : state.phase === 'erasing' ? ERASE_MS : TYPE_MS + Math.random() * 25;
    const t = setTimeout(() => dispatch({ type: 'tick' }), delay);
    return () => clearTimeout(t);
  }, [state]);

  const go = () => router.push(`/search?q=${encodeURIComponent(QUERIES[state.idx])}`);

  return (
    <button
      onClick={go}
      className="group w-full max-w-xl mx-auto flex items-center gap-3 card card-hover px-4 py-3 text-left cursor-pointer transition-all"
      aria-label="Probar el buscador"
    >
      <Search size={15} className="text-text-tertiary shrink-0 group-hover:text-celeste transition-colors" />
      <span className="flex-1 font-mono text-[13px] text-text-secondary min-h-[1.3em]">
        {state.typed}
        <span className="caret" />
      </span>
      <span className="text-[11px] font-semibold text-celeste shrink-0 flex items-center gap-1">
        Buscar <span className="arrow inline-block transition-transform group-hover:translate-x-1">→</span>
      </span>
    </button>
  );
}
