'use client';

import { Suspense } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import { Eye, LogIn } from 'lucide-react';
import { AUTH_ENABLED } from '@/lib/authClient';

function SignInInner() {
  const params = useSearchParams();
  const callbackUrl = params.get('callbackUrl') || '/feed';

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="flag-stripe fixed top-0 inset-x-0 z-[60]" />
      <div className="card p-8 max-w-sm w-full text-center">
        <div className="w-12 h-12 rounded-lg bg-celeste/10 border border-celeste/30 flex items-center justify-center mx-auto mb-4">
          <Eye size={24} className="text-celeste" />
        </div>
        <h1 className="text-lg font-bold text-text-primary mb-1">VIGÍA</h1>
        <p className="text-[12px] text-text-tertiary mb-6">Inteligencia Legislativa y Regulatoria</p>

        {AUTH_ENABLED ? (
          <button
            onClick={() => signIn('google', { callbackUrl })}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 btn-celeste rounded-full text-[13px] font-bold"
          >
            <LogIn size={15} /> Continuar con Google
          </button>
        ) : (
          <p className="text-[12px] text-text-secondary bg-bg-secondary border border-border-light rounded p-3">
            La autenticación no está configurada en este entorno (modo demo).
            Definí <code className="font-mono">AUTH_GOOGLE_ID</code>, <code className="font-mono">AUTH_GOOGLE_SECRET</code> y <code className="font-mono">AUTH_SECRET</code> para activarla.
          </p>
        )}

        <a href="/feed" className="block mt-4 text-[12px] text-inst-accent hover:underline">Entrar al demo →</a>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={null}>
      <SignInInner />
    </Suspense>
  );
}
