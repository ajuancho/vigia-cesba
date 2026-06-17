'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { Sparkles, X } from 'lucide-react';
import { AUTH_ENABLED } from '@/lib/authClient';

/**
 * Prompt opcional para completar el onboarding (nombre del workspace + sectores
 * de interés). El flujo de signin manda directo al feed, así que sin esto nadie
 * pasa por /onboarding. Es descartable y no bloquea: se oculta al onboardear o
 * al cerrarlo (persistido en localStorage para no insistir).
 *
 * El flag `onboarded` viaja en el JWT y se refresca recién en el próximo sync;
 * por eso /onboarding marca el localStorage al terminar, evitando que el banner
 * reaparezca con la sesión stale.
 */
const KEY = 'vigia_onboarding_dismissed';

export default function OnboardingBanner() {
  const { data: session } = useSession();
  const [hidden, setHidden] = useState(true); // oculto hasta leer localStorage (evita flash)

  useEffect(() => {
    try {
      setHidden(localStorage.getItem(KEY) === '1');
    } catch {
      setHidden(false);
    }
  }, []);

  const ws = session?.workspace;
  if (!AUTH_ENABLED || !ws || ws.onboarded || hidden) return null;

  const dismiss = () => {
    try {
      localStorage.setItem(KEY, '1');
    } catch {
      /* noop */
    }
    setHidden(true);
  };

  return (
    <div className="mb-5 card border-l-4 border-l-celeste p-4 flex items-start gap-3">
      <Sparkles size={16} className="text-celeste shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-semibold text-text-primary">Personalizá tu Vigía</p>
        <p className="text-[12px] text-text-secondary leading-relaxed">
          Elegí tus sectores de interés para afinar el feed y las alertas. Toma 30 segundos.
        </p>
      </div>
      <Link
        href="/onboarding"
        className="shrink-0 px-3 py-1.5 btn-celeste rounded-full text-[12px] font-bold whitespace-nowrap"
      >
        Completar perfil
      </Link>
      <button
        onClick={dismiss}
        aria-label="Descartar"
        className="shrink-0 p-1 text-text-tertiary hover:text-text-primary transition-colors"
      >
        <X size={15} />
      </button>
    </div>
  );
}
