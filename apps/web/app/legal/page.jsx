import Link from 'next/link';
import { Eye, ArrowLeft } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

export const metadata = {
  title: 'Términos y privacidad — Vigía',
  description: 'Qué datos guarda Vigía, para qué los usa y cuáles son tus derechos.',
};

const SECCIONES = [
  {
    num: 'I.',
    titulo: 'El servicio',
    cuerpo: [
      <>Vigía es una plataforma de inteligencia legislativa y regulatoria argentina, desarrollada por <strong className="text-text-primary">Colossus Lab</strong> (familia OpenArg). Monitorea fuentes oficiales públicas — Boletín Oficial, InfoLEG, Congreso, BCRA y consultas públicas —, las indexa y te avisa cuando aparece normativa que te interesa.</>,
      <>El corpus normativo que mostramos es <strong className="text-text-primary">información pública</strong>: proviene de fuentes oficiales del Estado argentino y cada norma linkea a su fuente original verificable.</>,
    ],
  },
  {
    num: 'II.',
    titulo: 'Qué datos guardamos',
    cuerpo: [
      <>Si creás una cuenta, guardamos lo que tu cuenta de Google nos da al iniciar sesión: <strong className="text-text-primary">email, nombre y foto de perfil</strong>. Nada más — no accedemos a tu correo, contactos ni archivos.</>,
      <>Además guardamos lo que vos creás dentro de la plataforma: tu workspace, sus miembros, las alertas que configurás (keywords y sectores) y los emails de las personas que invitás.</>,
    ],
  },
  {
    num: 'III.',
    titulo: 'Para qué los usamos',
    cuerpo: [
      <>Para que el servicio funcione: autenticarte, mantener tu workspace y mandarte los emails que pediste — el digest de tus alertas y las invitaciones que enviás. Son emails operativos, no de marketing.</>,
    ],
  },
  {
    num: 'IV.',
    titulo: 'Lo que no hacemos',
    cuerpo: [
      <>No vendemos ni compartimos tus datos con terceros. No mostramos publicidad. No usamos trackers de terceros ni perfiles de comportamiento. Tu monitoreo — qué keywords vigilás, qué buscás — es tuyo.</>,
    ],
  },
  {
    num: 'V.',
    titulo: 'Servicios de terceros',
    cuerpo: [
      <>Para operar usamos: <strong className="text-text-primary">Google</strong> (inicio de sesión), <strong className="text-text-primary">Resend</strong> (envío de emails), <strong className="text-text-primary">Amazon Web Services</strong> (infraestructura y base de datos) y <strong className="text-text-primary">Vercel</strong> (hosting del sitio). Cada uno recibe solo lo mínimo necesario para su función.</>,
    ],
  },
  {
    num: 'VI.',
    titulo: 'Cookies',
    cuerpo: [
      <>Usamos únicamente la cookie de sesión necesaria para mantenerte logueado. Sin cookies de publicidad ni de analytics de terceros.</>,
    ],
  },
  {
    num: 'VII.',
    titulo: 'Tus datos, tus derechos',
    cuerpo: [
      <>Podés pedir acceso, corrección o <strong className="text-text-primary">borrado completo de tu cuenta y tus datos</strong> escribiendo a <a href="mailto:devops@colossuslab.org" className="textlink">devops@colossuslab.org</a>. Lo procesamos a la brevedad y sin vueltas.</>,
    ],
  },
  {
    num: 'VIII.',
    titulo: 'Términos de uso',
    cuerpo: [
      <>Vigía está en <strong className="text-text-primary">beta</strong> y se ofrece "tal cual". Hacemos lo posible por la frescura y fidelidad de los datos (monitoreamos cada fuente con SLOs), pero las fuentes oficiales pueden contener errores, demoras u omisiones — y nuestro procesamiento también puede fallar.</>,
      <>Vigía <strong className="text-text-primary">no es asesoramiento legal</strong>. Los resúmenes — incluidos los generados automáticamente con IA — son orientativos: ante cualquier decisión, verificá siempre el texto completo en la fuente oficial (cada norma incluye el link).</>,
      <>Cada workspace incluye un período de prueba gratuito de 30 días; al vencer, las funciones de cuenta (workspaces y alertas) requieren membresía. Los datos normativos públicos siguen siendo de libre acceso.</>,
    ],
  },
  {
    num: 'IX.',
    titulo: 'Cambios',
    cuerpo: [
      <>Si esta página cambia, actualizamos la fecha de abajo. Si el cambio es relevante para tus datos, te avisamos por email.</>,
    ],
  },
];

export default function LegalPage() {
  return (
    <div className="min-h-screen">
      <div className="flag-stripe fixed top-0 inset-x-0 z-[60]" />

      <header className="sticky top-0 z-50 bg-bg-secondary/80 backdrop-blur border-b border-border-light">
        <div className="max-w-3xl mx-auto px-5 md:px-10 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 rounded-lg bg-celeste/10 border border-celeste/30 flex items-center justify-center">
              <Eye size={14} className="text-celeste" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-text-primary leading-none" style={{ fontFamily: 'var(--font-display)' }}>VIGÍA</p>
              <p className="text-[8px] text-text-tertiary uppercase tracking-[0.18em] font-mono mt-0.5">por OpenArg</p>
            </div>
          </Link>
          <Link href="/" className="flex items-center gap-1.5 text-[12px] text-text-tertiary hover:text-text-primary transition-colors">
            <ArrowLeft size={12} /> Volver al inicio
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-5 md:px-10 pb-16">
        <section className="pt-12 md:pt-16 pb-10">
          <FadeIn>
            <p className="eyebrow mb-4">
              <span className="eyebrow-num">LEGAL</span>
              <span className="mx-2 text-text-tertiary">·</span>
              Claro y en una sola página
            </p>
          </FadeIn>
          <FadeIn delay={80}>
            <h1 className="display-section text-text-primary mb-4">
              Términos y <em>privacidad.</em>
            </h1>
          </FadeIn>
          <FadeIn delay={140}>
            <p className="text-[14px] text-text-secondary leading-relaxed max-w-xl">
              La versión corta: guardamos lo mínimo para que el servicio funcione,
              no vendemos tus datos, y podés irte — con todo borrado — cuando quieras.
              La versión completa, abajo.
            </p>
          </FadeIn>
        </section>

        <div className="border-t-2 border-text-primary/70">
          {SECCIONES.map(({ num, titulo, cuerpo }, i) => (
            <FadeIn key={num} delay={i * 50}>
              <section className="grid grid-cols-1 md:grid-cols-[180px_1fr] gap-2 md:gap-8 py-7 border-b border-border-light">
                <p className="eyebrow">
                  <span className="eyebrow-num">{num}</span>
                  <span className="ml-2">{titulo}</span>
                </p>
                <div className="space-y-3">
                  {cuerpo.map((parrafo, j) => (
                    <p key={j} className="text-[13px] text-text-secondary leading-relaxed">{parrafo}</p>
                  ))}
                </div>
              </section>
            </FadeIn>
          ))}
        </div>

        <FadeIn>
          <p className="text-[10px] text-text-tertiary font-mono pt-6">
            Última actualización: 12 de junio de 2026 · Colossus Lab · Buenos Aires
          </p>
        </FadeIn>
      </main>
    </div>
  );
}
