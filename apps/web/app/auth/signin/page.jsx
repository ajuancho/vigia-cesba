'use client';

import { Suspense, useState } from 'react';
import Link from 'next/link';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import { Bell, Users, History, ArrowLeft } from 'lucide-react';
import { AUTH_ENABLED } from '@/lib/authClient';
import FadeIn from '@/components/FadeIn';

const BENEFITS = [
  { icon: Bell, text: 'Alertas por keyword y sector, con digest por email' },
  { icon: Users, text: 'Seguí la normativa porteña que te importa' },
  { icon: History, text: 'Monitoreo persistente: nada se pierde entre sesiones' },
];

function GoogleMark() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.27-4.74 3.27-8.1z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.1A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.44.34-2.1V7.06H2.18a11 11 0 0 0 0 9.88l3.66-2.84z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15A11 11 0 0 0 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

function SignInInner() {
  const params = useSearchParams();
  const callbackUrl = params.get('callbackUrl') || '/feed';
  const [accepted, setAccepted] = useState(false);

  return (
    <div className="min-h-screen flex flex-wrap bg-white">
      {/* Marca: gradiente institucional + trama */}
      <section className="grad-institucional relative overflow-hidden text-white flex-[1_1_480px] min-h-[380px] p-8 md:p-12 flex flex-col justify-between gap-12">
        <div className="trama" />
        <div className="blob w-[460px] h-[460px] -left-36 -bottom-44 bg-[rgba(0,250,185,0.26)]" />
        <Link href="/" className="relative w-fit">
          <img src="/brand/cesba-logo-blanco.png" alt="CESBA — Consejo Económico y Social de la Ciudad de Buenos Aires" width={96} height={96} className="w-20 h-20 md:w-24 md:h-24" />
        </Link>
        <div className="relative title-rule-vital flex flex-col gap-3">
          <p className="display-hero !text-[clamp(2rem,4vw,3.25rem)]">Monitor BOCBA</p>
          <p className="text-[17px] md:text-[19px] font-light text-white/85">la normativa porteña, al día</p>
        </div>
        <p className="relative text-[11px] md:text-[12px] tracking-[0.06em] text-white/85">
          CONSEJO ECONÓMICO Y SOCIAL DE LA CIUDAD DE BUENOS AIRES
        </p>
      </section>

      {/* Acceso */}
      <section className="flex-[1_1_480px] px-6 py-12 md:py-16 flex items-center justify-center">
        <FadeIn className="w-full max-w-sm">
          <div className="flex flex-col gap-7">
            <div className="flex flex-col gap-2">
              <p className="eyebrow"><span className="eyebrow-num">ACCESO</span></p>
              <h1 className="display-section text-petroleo">Entrá al monitor</h1>
              <p className="text-[15px] text-text-tertiary">usá tu correo institucional para ingresar</p>
            </div>

            <ul className="space-y-3">
              {BENEFITS.map(({ icon: Icon, text }) => (
                <li key={text} className="flex items-start gap-3 text-[14px] text-text-secondary leading-relaxed">
                  <Icon size={18} strokeWidth={1.75} className="text-petroleo shrink-0 mt-0.5" />
                  {text}
                </li>
              ))}
            </ul>

            {AUTH_ENABLED ? (
              <div className="flex flex-col gap-4">
                <label className="flex items-start gap-2.5 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={accepted}
                    onChange={(e) => setAccepted(e.target.checked)}
                    className="mt-0.5 w-4 h-4 shrink-0 accent-cian cursor-pointer"
                  />
                  <span className="text-[12px] text-text-tertiary leading-relaxed">
                    Leí y acepto los{' '}
                    <Link href="/legal" className="text-celeste font-semibold hover:text-petroleo transition-colors">términos y la política de privacidad</Link>, y presto mi consentimiento al tratamiento de mis datos personales conforme a la Ley N° 25.326.
                  </span>
                </label>
                <button
                  onClick={() => signIn('google', { callbackUrl })}
                  disabled={!accepted}
                  className="btn-celeste w-full flex items-center justify-center gap-3 min-h-12 px-4 text-[13px] font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span className="w-6 h-6 rounded-sm bg-white flex items-center justify-center"><GoogleMark /></span>
                  Continuar con Google
                </button>
              </div>
            ) : (
              <div className="text-[13px] text-text-secondary bg-humo border border-border-light rounded p-3 leading-relaxed">
                <span className="tint-amber border rounded-full px-2 py-0.5 text-[10px] font-semibold mr-1.5">demo</span>
                El login se activa configurando Google OAuth
                (<code className="text-[12px]">AUTH_GOOGLE_ID/SECRET</code> + <code className="text-[12px]">AUTH_SECRET</code>).
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-2 pt-5 border-t border-border-light text-[12px]">
              <a href="https://www.cesba.gob.ar" target="_blank" rel="noopener noreferrer" className="font-semibold tracking-[0.06em] text-petroleo hover:underline">www.cesba.gob.ar</a>
              <Link href="/" className="flex items-center gap-1 text-text-tertiary hover:text-petroleo transition-colors">
                <ArrowLeft size={12} /> Volver al inicio
              </Link>
            </div>
          </div>
        </FadeIn>
      </section>
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
