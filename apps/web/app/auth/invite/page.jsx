'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSession, signIn } from 'next-auth/react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Eye } from 'lucide-react';
import { authedFetch, AUTH_ENABLED } from '@/lib/authClient';

function InviteInner() {
  const { data: session, status } = useSession();
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get('token');
  const [state, setState] = useState('idle'); // idle | accepting | ok | error
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!AUTH_ENABLED || !token) return;
    if (status === 'authenticated' && session?.apiJwt && state === 'idle') {
      setState('accepting');
      authedFetch(session.apiJwt, `/invitations/${token}/accept`, { method: 'POST' })
        .then(() => { setState('ok'); setTimeout(() => router.push('/feed'), 1200); })
        .catch((e) => { setState('error'); setMsg(String(e.message || e)); });
    }
  }, [status, session, token, state, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-900 p-4">
      <div className="card p-8 max-w-sm w-full text-center">
        <div className="w-12 h-12 rounded-lg bg-navy-800 flex items-center justify-center mx-auto mb-4"><Eye size={24} className="text-white" /></div>
        <h1 className="text-lg font-bold text-text-primary mb-3">Invitación a Vigía</h1>
        {!token && <p className="text-[13px] text-status-red">Falta el token de invitación.</p>}
        {token && !AUTH_ENABLED && <p className="text-[13px] text-text-secondary">Auth deshabilitada en este entorno.</p>}
        {token && AUTH_ENABLED && status === 'unauthenticated' && (
          <button onClick={() => signIn('google')} className="w-full px-4 py-2.5 bg-navy-800 text-white rounded text-[13px] font-medium hover:bg-navy-700">Iniciá sesión para aceptar</button>
        )}
        {state === 'accepting' && <p className="text-[13px] text-text-secondary">Aceptando…</p>}
        {state === 'ok' && <p className="text-[13px] text-status-green">¡Listo! Redirigiendo…</p>}
        {state === 'error' && <p className="text-[13px] text-status-red">{msg}</p>}
      </div>
    </div>
  );
}

export default function InvitePage() {
  return (
    <Suspense fallback={null}>
      <InviteInner />
    </Suspense>
  );
}
