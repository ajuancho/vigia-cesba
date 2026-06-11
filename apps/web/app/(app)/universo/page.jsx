'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import { ArrowLeft } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

const TIPO_COLOR = {
  DNU: '#F87171', DECRETO: '#F6B40E', LEY: '#34D399', RESOLUCION: '#74ACDF',
  DISPOSICION: '#A78BFA', PROYECTO: '#22D3EE', COMUNICACION: '#F472B6',
  CONSULTA: '#FB923C', OTRA: '#8892A8',
};
// Paleta para el nivel sectores (rota por índice).
const SECTOR_COLORS = ['#74ACDF', '#F6B40E', '#34D399', '#A78BFA', '#22D3EE', '#F472B6', '#FB923C', '#F87171', '#93C5F8', '#8892A8', '#FFD04A', '#5A8FBD'];

/* ---------- física: deriva en cero gravedad + repulsión suave ---------- */

function buildBodies(items, W, H, colorFor) {
  const max = Math.max(...items.map((d) => d.cantidad), 1);
  const min = Math.min(...items.map((d) => d.cantidad), max);
  const rMin = Math.min(W, H) * 0.045;
  const rMax = Math.min(W, H) * 0.16;
  return items.map((d, i) => {
    // Escala por sqrt (área ∝ cantidad) con piso para que lo chico sea clickeable.
    const t = max === min ? 1 : (Math.sqrt(d.cantidad) - Math.sqrt(min)) / (Math.sqrt(max) - Math.sqrt(min));
    const r = rMin + t * (rMax - rMin);
    const angle = (i / items.length) * Math.PI * 2;
    return {
      ...d,
      color: colorFor(d, i),
      r,
      x: W / 2 + Math.cos(angle) * Math.min(W, H) * 0.26,
      y: H / 2 + Math.sin(angle) * Math.min(W, H) * 0.26,
      vx: (Math.random() - 0.5) * 0.18,
      vy: (Math.random() - 0.5) * 0.18,
    };
  });
}

function stepBodies(bodies, W, H) {
  const PAD = 70; // margen para los callouts
  for (const b of bodies) {
    b.x += b.vx;
    b.y += b.vy;
    // leve atracción al centro para que no se vayan a los bordes
    b.vx += (W / 2 - b.x) * 0.000012 * b.r;
    b.vy += (H / 2 - b.y) * 0.000012 * b.r;
    // paredes blandas
    if (b.x - b.r < PAD) b.vx += 0.02;
    if (b.x + b.r > W - PAD) b.vx -= 0.02;
    if (b.y - b.r < PAD) b.vy += 0.02;
    if (b.y + b.r > H - PAD) b.vy -= 0.02;
    // fricción mínima: deriva perpetua, sin acelerarse
    b.vx *= 0.998;
    b.vy *= 0.998;
  }
  // repulsión suave entre burbujas (colisión elástica amortiguada)
  for (let i = 0; i < bodies.length; i++) {
    for (let j = i + 1; j < bodies.length; j++) {
      const a = bodies[i], b = bodies[j];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.hypot(dx, dy) || 1;
      const overlap = a.r + b.r + 14 - dist;
      if (overlap > 0) {
        const f = (overlap / dist) * 0.012;
        a.vx -= dx * f; a.vy -= dy * f;
        b.vx += dx * f; b.vy += dy * f;
      }
    }
  }
}

/* ---------- componente ---------- */

export default function UniversoView() {
  const router = useRouter();
  const [nivel, setNivel] = useState({ tipo: null }); // null = universo de tipos
  const [items, setItems] = useState(null);
  const [hover, setHover] = useState(null);
  const wrapRef = useRef(null);
  const svgRef = useRef(null);
  const bodiesRef = useRef([]);
  const rafRef = useRef(null);
  const [, forceRender] = useState(0);

  // datos del nivel actual
  useEffect(() => {
    setItems(null);
    api
      .universo(nivel.tipo ? { tipo: nivel.tipo } : {})
      .then(setItems)
      .catch(() => setItems([]));
  }, [nivel]);

  // armar cuerpos cuando hay datos + tamaño
  useEffect(() => {
    if (!items || !wrapRef.current) return;
    const { clientWidth: W, clientHeight: H } = wrapRef.current;
    const colorFor = nivel.tipo
      ? (_, i) => SECTOR_COLORS[i % SECTOR_COLORS.length]
      : (d) => TIPO_COLOR[d.key] || TIPO_COLOR.OTRA;
    bodiesRef.current = buildBodies(items.slice(0, 14), W, H, colorFor);
    forceRender((n) => n + 1);
  }, [items, nivel]);

  // loop de animación (respeta prefers-reduced-motion)
  useEffect(() => {
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;
    let mounted = true;
    const tick = () => {
      if (!mounted || !wrapRef.current) return;
      const { clientWidth: W, clientHeight: H } = wrapRef.current;
      stepBodies(bodiesRef.current, W, H);
      // mutación directa del DOM SVG: 60fps sin re-render de React
      const svg = svgRef.current;
      if (svg) {
        for (const b of bodiesRef.current) {
          const g = svg.querySelector(`[data-id="${CSS.escape(b.key)}"]`);
          if (g) g.setAttribute('transform', `translate(${b.x}, ${b.y})`);
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { mounted = false; cancelAnimationFrame(rafRef.current); };
  }, [items, nivel]);

  const onClickBubble = useCallback(
    (b) => {
      if (!nivel.tipo) {
        setNivel({ tipo: b.key }); // drill-down: tipos -> sectores
      } else {
        const sector = b.key === 'Sin clasificar' ? undefined : b.key;
        router.push(`/feed?tipo=${encodeURIComponent(nivel.tipo)}${sector ? `&sector=${encodeURIComponent(sector)}` : ''}`);
      }
    },
    [nivel, router]
  );

  const bodies = bodiesRef.current;
  const tipoMeta = nivel.tipo ? (TIPOS_NORMA[nivel.tipo] || TIPOS_NORMA.OTRA) : null;

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col">
      <FadeIn>
        <div className="pt-2 mb-2 flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow mb-1">
              <span className="eyebrow-num">VIGÍA / UNIVERSO</span>
              <span className="ml-2">{nivel.tipo ? `${tipoMeta.label} · por sector` : 'el corpus normativo argentino'}</span>
            </p>
            <h2 className="display-section text-text-primary">
              {nivel.tipo ? (
                <>{tipoMeta.label}, <em>por dentro.</em></>
              ) : (
                <>El universo, <em>en órbita.</em></>
              )}
            </h2>
          </div>
          {nivel.tipo ? (
            <button
              onClick={() => setNivel({ tipo: null })}
              className="group flex items-center gap-1.5 text-text-tertiary hover:text-text-primary text-[12px] transition-colors shrink-0 pb-1"
            >
              <ArrowLeft size={13} className="group-hover:-translate-x-0.5 transition-transform" /> volver al universo
            </button>
          ) : (
            <p className="text-[11px] text-text-tertiary font-mono shrink-0 pb-1 hidden md:block">
              click en una órbita para explorar →
            </p>
          )}
        </div>
      </FadeIn>

      <div ref={wrapRef} className="flex-1 relative min-h-[420px]">
        {!items && (
          <p className="absolute inset-0 flex items-center justify-center text-[12px] font-mono text-text-tertiary animate-pulse">
            Cargando el universo…
          </p>
        )}
        <svg ref={svgRef} className="w-full h-full" role="list" aria-label="Universo normativo">
          {bodies.map((b) => {
            const label = nivel.tipo ? b.key : (TIPOS_NORMA[b.key]?.label || b.key);
            const isHover = hover === b.key;
            // callout hacia afuera del centro
            const cx = wrapRef.current ? wrapRef.current.clientWidth / 2 : 0;
            const dirX = b.x >= cx ? 1 : -1;
            const lineLen = b.r * 0.5 + 26;
            return (
              <g
                key={b.key}
                data-id={b.key}
                transform={`translate(${b.x}, ${b.y})`}
                onClick={() => onClickBubble(b)}
                onMouseEnter={() => setHover(b.key)}
                onMouseLeave={() => setHover(null)}
                style={{ cursor: 'pointer' }}
                role="listitem"
                aria-label={`${label}: ${b.cantidad.toLocaleString('es-AR')} normas`}
              >
                <circle
                  r={b.r}
                  fill={b.color}
                  fillOpacity={isHover ? 0.22 : 0.1}
                  stroke={b.color}
                  strokeOpacity={isHover ? 0.9 : 0.45}
                  strokeWidth={isHover ? 1.5 : 1}
                  style={{ transition: 'fill-opacity .25s, stroke-opacity .25s' }}
                />
                {/* núcleo */}
                <circle r={Math.max(b.r * 0.06, 2)} fill={b.color} fillOpacity={0.9} />
                {/* callout editorial: hairline + label + cantidad */}
                <line
                  x1={dirX * b.r * 0.72} y1={-b.r * 0.72}
                  x2={dirX * (b.r * 0.72 + lineLen)} y2={-b.r * 0.72 - lineLen * 0.55}
                  stroke={b.color} strokeOpacity={0.5} strokeWidth={0.75}
                />
                <text
                  x={dirX * (b.r * 0.72 + lineLen + 5)} y={-b.r * 0.72 - lineLen * 0.55 - 2}
                  textAnchor={dirX > 0 ? 'start' : 'end'}
                  style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13 }}
                  fill="#E8ECF4"
                >
                  {label}
                </text>
                <text
                  x={dirX * (b.r * 0.72 + lineLen + 5)} y={-b.r * 0.72 - lineLen * 0.55 + 12}
                  textAnchor={dirX > 0 ? 'start' : 'end'}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}
                  fill="#636E85"
                >
                  {b.cantidad.toLocaleString('es-AR')} normas
                </text>
              </g>
            );
          })}
        </svg>
        <p className="absolute bottom-2 left-0 text-[10px] text-text-tertiary font-mono">
          {nivel.tipo
            ? 'click en un sector para abrir el lector'
            : '533 mil normas · tamaño = volumen · datos en vivo'}
        </p>
      </div>
    </div>
  );
}
