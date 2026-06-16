import Link from 'next/link';
import { Eye, Newspaper, Search, Bell, Shield, ArrowRight, Building2, BarChart3 } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import TypingDemo from '@/components/TypingDemo';

export const revalidate = 300;

const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getStats() {
  try {
    const res = await fetch(`${API}/stats/dashboard`, { next: { revalidate: 300 } });
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    return null;
  }
}

const MODULES = [
  {
    num: '01', icon: Newspaper, title: 'Feed Normativo', href: '/feed',
    desc: 'El Boletín del día como un diario: lo importante arriba, el trámite colapsado, filtrable por organismo emisor, y cada norma nueva con su resumen IA — qué resuelve y a quién afecta.',
  },
  {
    num: '02', icon: Search, title: 'Buscador', href: '/search',
    desc: 'Full-text search en español sobre todo el corpus normativo. Lenguaje natural, ranking y snippets.',
  },
  {
    num: '03', icon: Bell, title: 'Alertas', href: '/alerts',
    desc: 'Suscribite por keyword y sector. Cuando una norma, comunicación o edicto matchea, te llega un digest por email.',
  },
  {
    num: '04', icon: Shield, title: 'Tracker DNU', href: '/dnu',
    desc: 'Cada DNU con su estado bicameral real: dictaminados, pendientes y sin tratamiento, desde los datos del Congreso.',
  },
  {
    num: '05', icon: Building2, title: 'Radar societario', href: '/avisos',
    desc: 'La 2ª sección del Boletín, buscable: constituciones, asambleas y edictos. Vigilá una empresa por razón social.',
  },
  {
    num: '06', icon: BarChart3, title: 'Estadísticas', href: '/dashboard',
    desc: 'El pulso normativo en números: actividad por tipo y sector, organismos más activos, tendencias.',
  },
];

const PIPELINE = [
  { num: '01', label: 'Ingesta', desc: 'Nueve fuentes oficiales — BORA, InfoLEG, ambas cámaras del Congreso, BCRA — con workers diarios', color: 'text-celeste' },
  { num: '02', label: 'Normalización', desc: 'Tipo, sector, estado de tramitación y organismo emisor canónico (ARCA, CNV, BCRA…) detectados', color: 'text-sol' },
  { num: '03', label: 'Síntesis IA', desc: 'Cada norma nueva del Boletín, resumida en lenguaje claro: qué resuelve y a quién afecta', color: 'text-sol-bright' },
  { num: '04', label: 'Alertas', desc: 'Índice full-text en español + matching por keyword y digest por email', color: 'text-text-primary' },
];

export default async function Landing() {
  const stats = await getStats();
  const total = stats?.total_normas ?? 990;
  const sectores = stats?.por_sector?.length ?? 9;
  const fmt = (n) => n.toLocaleString('es-AR');

  return (
    <div className="min-h-screen">
      <div className="flag-stripe fixed top-0 inset-x-0 z-[60]" />

      {/* ── Topbar ── */}
      <header className="sticky top-0 z-50 bg-bg-secondary/80 backdrop-blur border-b border-border-light">
        <div className="max-w-5xl mx-auto px-5 md:px-10 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-celeste/10 border border-celeste/30 flex items-center justify-center">
              <Eye size={14} className="text-celeste" />
            </div>
            <div>
              <p className="text-[13px] font-bold text-text-primary leading-none" style={{ fontFamily: 'var(--font-display)' }}>VIGÍA</p>
              <p className="text-[8px] text-text-tertiary uppercase tracking-[0.18em] font-mono mt-0.5">por OpenArg</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-[12px] font-mono text-text-secondary">
            <a href="#plataforma" className="hover:text-text-primary transition-colors">Plataforma</a>
            <a href="#como-funciona" className="hover:text-text-primary transition-colors">Cómo funciona</a>
          </nav>
          <div className="flex items-center gap-2">
            <Link href="/auth/signin" className="hidden sm:block text-[12px] text-text-secondary hover:text-text-primary px-3 py-1.5 transition-colors">
              Iniciar sesión
            </Link>
            <Link href="/feed" className="btn-celeste rounded-full px-4 py-1.5 text-[12px] font-bold">
              Entrar →
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 md:px-10">
        {/* ── Hero ── */}
        <section className="pt-16 pb-14 md:pt-24 md:pb-20 text-center">
          <FadeIn>
            <p className="eyebrow mb-5">
              <span className="eyebrow-num">N.º 01 / MMXXVI</span>
              <span className="mx-2 text-text-tertiary">·</span>
              Inteligencia legislativa y regulatoria
            </p>
          </FadeIn>
          <FadeIn delay={80}>
            <h1 className="display-hero text-text-primary mb-6">
              La normativa argentina,
              <br />
              <em>vigilada.</em>
            </h1>
          </FadeIn>
          <FadeIn delay={160}>
            <p className="text-[15px] md:text-base text-text-secondary max-w-xl mx-auto leading-relaxed mb-9">
              Vigía monitorea el <strong className="text-text-primary font-semibold">Boletín Oficial del día</strong>,
              ambas cámaras del Congreso, el BCRA y las consultas públicas; lo indexa, lo{' '}
              <strong className="text-text-primary font-semibold">resume con IA en lenguaje claro</strong> y
              te avisa cuando algo que te importa cambia. Datos públicos, frescos cada mañana,
              sin leer {fmt(total)} normas a mano.
            </p>
          </FadeIn>
          <FadeIn delay={240}>
            <TypingDemo />
          </FadeIn>
          <FadeIn delay={320}>
            <div className="flex items-center justify-center gap-6 mt-9 text-[13px] font-medium">
              <Link href="/feed" className="textlink">
                Entrar a la plataforma <span className="arrow">→</span>
              </Link>
              <Link href="/auth/signin" className="textlink">
                Crear cuenta <span className="arrow">→</span>
              </Link>
            </div>
          </FadeIn>
        </section>

        {/* ── Escala (stats editoriales) ── */}
        <section className="border-t border-border-light py-12 md:py-16">
          <FadeIn>
            <p className="eyebrow mb-8"><span className="eyebrow-num">I.</span> <span className="ml-2">Escala</span></p>
          </FadeIn>
          {[
            { num: `${fmt(total)}+`, color: 'text-celeste', label: 'Normas indexadas', detail: 'Leyes, decretos, DNU, resoluciones, proyectos parlamentarios, comunicaciones del BCRA y consultas públicas.' },
            { num: '9', color: 'text-sol', label: 'Fuentes oficiales', detail: 'Boletín Oficial (1ª y 2ª sección), InfoLEG, Diputados y Senado (proyectos, movimientos y dictámenes), BCRA y consultas públicas.' },
            { num: String(sectores), color: 'text-sol-bright', label: 'Sectores detectados', detail: 'Energía, minería, salud, trabajo, tecnología y más, etiquetados automáticamente.' },
            { num: '24/7', color: 'text-text-primary', label: 'Monitoreo continuo', detail: 'Ingesta diaria con SLOs de frescura por fuente: si un dato se atrasa, lo sabemos antes que vos.' },
          ].map((row, i) => (
            <FadeIn key={row.label} delay={i * 80}>
              <div className="grid grid-cols-1 md:grid-cols-[200px_220px_1fr] gap-2 md:gap-6 items-baseline py-6 border-b border-border-light">
                <span className={`font-mono font-bold text-4xl md:text-5xl tracking-tight ${row.color}`}>{row.num}</span>
                <span className="text-[15px] font-bold text-text-primary" style={{ fontFamily: 'var(--font-display)' }}>{row.label}</span>
                <span className="text-[13px] text-text-secondary leading-relaxed">{row.detail}</span>
              </div>
            </FadeIn>
          ))}
        </section>

        {/* ── Módulos ── */}
        <section id="plataforma" className="border-t border-border-light py-12 md:py-16 scroll-mt-16">
          <FadeIn>
            <p className="eyebrow mb-3"><span className="eyebrow-num">II.</span> <span className="ml-2">La plataforma</span></p>
            <h2 className="display-section text-text-primary mb-10">Seis módulos, <em>un solo radar.</em></h2>
          </FadeIn>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 border-t-2 border-text-primary/80">
            {MODULES.map(({ num, icon: Icon, title, desc, href }, i) => (
              <FadeIn key={num} delay={i * 70} className="h-full">
                <Link href={href} className="group flex flex-col gap-3 p-5 min-h-[190px] border-b sm:border-r border-border-light hover:bg-bg-primary transition-colors h-full">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] text-celeste">{num}</span>
                    <Icon size={15} className="text-text-tertiary group-hover:text-celeste transition-colors" />
                  </div>
                  <h3 className="text-[16px] font-bold text-text-primary" style={{ fontFamily: 'var(--font-display)' }}>{title}.</h3>
                  <p className="text-[12px] text-text-secondary leading-relaxed flex-1">{desc}</p>
                  <span className="text-[11px] font-semibold text-celeste opacity-0 group-hover:opacity-100 transition-opacity">
                    Abrir →
                  </span>
                </Link>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* ── Pipeline ── */}
        <section id="como-funciona" className="border-t border-border-light py-12 md:py-16 scroll-mt-16">
          <FadeIn>
            <p className="eyebrow mb-3"><span className="eyebrow-num">III.</span> <span className="ml-2">Cómo funciona</span></p>
            <h2 className="display-section text-text-primary mb-10">Del Boletín a tu inbox, <em>en cuatro pasos.</em></h2>
          </FadeIn>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border-t-2 border-text-primary/80">
            {PIPELINE.map(({ num, label, desc, color }, i) => (
              <FadeIn key={num} delay={i * 70} className="h-full">
                <div className="relative p-5 min-h-[140px] border-b sm:border-r border-border-light h-full">
                  {i < PIPELINE.length - 1 && (
                    <span className="hidden lg:block absolute top-5 right-3 text-sol text-lg">→</span>
                  )}
                  <p className={`font-mono font-bold text-3xl mb-2 ${color}`}>{num}</p>
                  <p className="text-[14px] font-bold text-text-primary mb-1" style={{ fontFamily: 'var(--font-display)' }}>{label}</p>
                  <p className="text-[12px] text-text-secondary leading-relaxed">{desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* ── CTA final ── */}
        <section className="border-t border-border-light py-14 md:py-20">
          <FadeIn>
            <div className="card max-w-2xl mx-auto p-8 md:p-10 text-center relative overflow-hidden">
              <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse 70% 90% at 50% -20%, rgba(116,172,223,0.10), transparent 60%)' }} />
              <p className="eyebrow mb-4"><span className="eyebrow-num">IV.</span> <span className="ml-2">Empezá a vigilar</span></p>
              <h2 className="display-section text-text-primary mb-4">
                Dejá de leer el Boletín. <em>Dejá que te avise.</em>
              </h2>
              <p className="text-[13px] text-text-secondary max-w-md mx-auto mb-7 leading-relaxed">
                Con tu cuenta gratuita accedés al feed, el buscador, las alertas por email
                y un workspace para tu equipo. Los datos son públicos; tu monitoreo es tuyo.
              </p>
              <div className="flex items-center justify-center gap-4 flex-wrap">
                <Link href="/feed" className="btn-celeste rounded-full px-6 py-2.5 text-[13px] font-bold inline-flex items-center gap-2">
                  Entrar a la plataforma <ArrowRight size={14} />
                </Link>
                <Link href="/auth/signin" className="textlink text-[13px] font-medium">
                  Iniciar sesión <span className="arrow">→</span>
                </Link>
              </div>
            </div>
          </FadeIn>
        </section>
      </main>

      {/* ── Colophon ── */}
      <footer className="border-t border-border-light">
        <div className="max-w-5xl mx-auto px-5 md:px-10 py-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
            <div>
              <p className="text-[13px] font-bold text-text-primary mb-1" style={{ fontFamily: 'var(--font-display)' }}>VIGÍA</p>
              <p className="text-[10px] text-text-tertiary font-mono uppercase tracking-[0.15em] mb-2">por OpenArg</p>
              <p className="text-[11px] text-text-secondary leading-relaxed">Inteligencia legislativa y regulatoria argentina.</p>
            </div>
            <div>
              <p className="eyebrow mb-3">Plataforma</p>
              <ul className="space-y-1.5 text-[12px] text-text-secondary">
                <li><Link href="/feed" className="hover:text-celeste transition-colors">Feed Normativo</Link></li>
                <li><Link href="/search" className="hover:text-celeste transition-colors">Buscador</Link></li>
                <li><Link href="/alerts" className="hover:text-celeste transition-colors">Alertas</Link></li>
                <li><Link href="/dnu" className="hover:text-celeste transition-colors">Tracker DNU</Link></li>
                <li><Link href="/avisos" className="hover:text-celeste transition-colors">Radar societario</Link></li>
              </ul>
            </div>
            <div>
              <p className="eyebrow mb-3">Fuentes</p>
              <ul className="space-y-1.5 text-[12px] text-text-secondary">
                <li>Boletín Oficial — 1ª y 2ª sección</li>
                <li>InfoLEG — Min. Justicia</li>
                <li>Congreso — Diputados y Senado (proyectos, movimientos, dictámenes)</li>
                <li>Comisión Bicameral DNU</li>
                <li>BCRA — Comunicaciones "A"</li>
                <li>Consultas públicas nacionales</li>
              </ul>
            </div>
            <div>
              <p className="eyebrow mb-3">Colossus Lab</p>
              <ul className="space-y-1.5 text-[12px] text-text-secondary">
                <li><a href="https://openarg.org" target="_blank" rel="noreferrer" className="hover:text-celeste transition-colors">OpenArg</a></li>
                <li><a href="https://github.com/colossus-lab/vigia" target="_blank" rel="noreferrer" className="hover:text-celeste transition-colors">Código abierto · MIT</a></li>
                <li><Link href="/legal" className="hover:text-celeste transition-colors">Términos y privacidad</Link></li>
              </ul>
            </div>
          </div>
          <div className="pt-5 border-t border-border-light flex flex-wrap items-center justify-between gap-2">
            <p className="text-[10px] text-text-tertiary font-mono">MMXXVI · Hecho en Buenos Aires por Colossus Lab</p>
            <p className="text-[10px] text-text-tertiary font-mono">Compuesto en Familjen Grotesk e Inter · Datos públicos verificables</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
