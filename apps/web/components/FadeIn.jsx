'use client';

import { useEffect, useRef } from 'react';

/**
 * Reveal on-scroll mínimo (filosofía OpenArg: movimiento solo al entrar en
 * viewport, nada ambient). Respeta prefers-reduced-motion.
 */
export default function FadeIn({ children, delay = 0, className = '' }) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // Sin animación cuando no hay render que la justifique: reduced-motion o
    // documento oculto (background tab, prerender) — IO no notifica ahí.
    if (
      window.matchMedia('(prefers-reduced-motion: reduce)').matches ||
      document.visibilityState === 'hidden'
    ) {
      el.classList.add('is-visible');
      return;
    }
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('is-visible');
          obs.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    obs.observe(el);
    // Failsafe: si IO no disparó en 1.2s (edge cases), revelar igual.
    const failsafe = setTimeout(() => el.classList.add('is-visible'), 1200);
    return () => {
      obs.disconnect();
      clearTimeout(failsafe);
    };
  }, []);

  return (
    <div ref={ref} className={`reveal ${className}`} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>
      {children}
    </div>
  );
}
