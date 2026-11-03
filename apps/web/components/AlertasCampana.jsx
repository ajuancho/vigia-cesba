'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Bell } from 'lucide-react';
import { authedFetch, AUTH_ENABLED } from '@/lib/authClient';

// "Visto hasta": última visita a /alerts en este navegador.
const KEY = 'vigia.alertas.vistas_hasta';
const REFRESCO_MS = 5 * 60 * 1000;

function leerVisto() {
  try { return window.localStorage.getItem(KEY); } catch { return null; }
}

function marcarVisto() {
  try { window.localStorage.setItem(KEY, new Date().toISOString()); } catch { /* storage bloqueado */ }
}

/**
 * Campana del header: lleva a Alertas y muestra cuántas normas nuevas
 * coincidieron con las alertas del workspace desde la última visita.
 */
export default function AlertasCampana() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const jwt = session?.apiJwt;
  const connected = AUTH_ENABLED && Boolean(jwt);
  const [nuevas, setNuevas] = useState(0);
  const enAlertas = pathname === '/alerts' || pathname.startsWith('/alerts/');

  useEffect(() => {
    if (!connected) return undefined;
    if (enAlertas) {
      marcarVisto();
      setNuevas(0);
      return undefined;
    }
    let vivo = true;
    const consultar = async () => {
      const visto = leerVisto();
      const qs = visto ? `?desde=${encodeURIComponent(visto)}` : '';
      try {
        const r = await authedFetch(jwt, `/alerts/novedades${qs}`);
        if (vivo) setNuevas(r.nuevas || 0);
      } catch { /* la campana no muestra errores: queda sin contador */ }
    };
    consultar();
    const t = setInterval(consultar, REFRESCO_MS);
    return () => { vivo = false; clearInterval(t); };
  }, [connected, jwt, enAlertas]);

  const etiqueta = nuevas > 0
    ? `Alertas: ${nuevas} ${nuevas === 1 ? 'norma nueva' : 'normas nuevas'}`
    : 'Alertas';

  return (
    <Link
      href="/alerts"
      aria-label={etiqueta}
      title={etiqueta}
      className="relative p-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
    >
      <Bell size={16} />
      {nuevas > 0 && (
        <span className="absolute -top-0.5 -right-0.5 min-w-4 h-4 px-1 rounded-full bg-status-red text-white text-[10px] font-bold leading-4 text-center tabular-nums">
          {nuevas > 9 ? '9+' : nuevas}
        </span>
      )}
    </Link>
  );
}
