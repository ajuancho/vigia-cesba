'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { authedFetch, AUTH_ENABLED } from '@/lib/authClient';

/**
 * Paywall del free trial: a los 30 días de la creación del workspace, si el
 * plan sigue siendo "free", cubre toda la plataforma con un cartel inamovible
 * (sin botón de cierre). La membresía se gestiona por email a devops.
 *
 * La session guarda trialEndsAt fijo al momento del login, así que el
 * vencimiento se evalúa client-side aunque la session sea vieja. Si devops ya
 * otorgó la membresía (plan != free en la API) pero la session quedó stale,
 * el refetch de /workspaces/me levanta el cartel sin pedir re-login.
 */
export default function TrialGate() {
  const { data: session } = useSession();
  const [lifted, setLifted] = useState(false);

  const ws = session?.workspace;
  const expired =
    AUTH_ENABLED &&
    ws &&
    ws.plan === 'free' &&
    ws.trialEndsAt &&
    Date.now() > new Date(ws.trialEndsAt).getTime();

  useEffect(() => {
    if (!expired || !session?.apiJwt) return;
    let cancelled = false;
    authedFetch(session.apiJwt, '/workspaces/me')
      .then((me) => {
        if (!cancelled && me && me.plan !== 'free') setLifted(true);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [expired, session?.apiJwt]);

  if (!expired || lifted) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-6"
      style={{ background: 'rgba(6, 9, 15, 0.96)', backdropFilter: 'blur(6px)' }}
      role="dialog"
      aria-modal="true"
      aria-label="Free trial finalizado"
    >
      <div className="card max-w-lg w-full p-8 md:p-10 text-center">
        <div className="flag-stripe h-1 w-16 mx-auto mb-6 rounded-full" />
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-tertiary mb-3">
          Free trial finalizado
        </p>
        <h2 className="font-display text-2xl md:text-3xl font-semibold text-text-primary leading-snug mb-4">
          Tu período de prueba <em className="text-sol italic">terminó</em>
        </h2>
        <p className="text-[14px] text-text-secondary leading-relaxed">
          Si querés seguir disfrutando de los beneficios de Vigía, contactate con{' '}
          <a href="mailto:devops@colossuslab.org" className="textlink text-celeste">
            devops@colossuslab.org
          </a>{' '}
          para obtener la membresía.
        </p>
      </div>
    </div>
  );
}
