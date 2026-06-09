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
    <div className="min-h-screen flex items-center justify-center bg-navy-900 p-4">
      <div className="card p-8 max-w-sm w-full text-center">
        <div className="w-12 h-12 rounded-lg bg-navy-800 flex items-center justify-center mx-auto mb-4">
          <Eye size={24} className="text-white" />
        </div>
        <h1 className="text-lg font-bold text-text-primary mb-1">VIGÍA</h1>
        <p className="text-[12px] text-text-tertiary mb-6">Inteligencia Legislativa y Regulatoria</p>

        {AUTH_ENABLED ? (
          <button
            onClick={() => signIn('google', { callbackUrl })}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-navy-800 text-white rounded text-[13px] font-medium hover:bg-navy-700 transition-colors"
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
