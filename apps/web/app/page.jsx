import Link from 'next/link';
import { Newspaper, Search, Bell, ArrowRight, BarChart3, FileBarChart } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

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
    icon: Newspaper, title: 'Boletín del día', href: '/feed',
    desc: 'El Boletín Oficial CABA como un diario: lo importante arriba, el trámite colapsado, filtrable por organismo y cada norma con su resumen IA.',
  },
  {
    icon: Search, title: 'Buscador', href: '/search',
    desc: 'Búsqueda de texto completo en español sobre toda la normativa porteña, con ranking por relevancia y fragmentos en contexto.',
  },
  {
    icon: Bell, title: 'Alertas', href: '/alerts',
    desc: 'Suscribite por palabra clave y sector. Cuando una norma coincide, recibís un resumen por correo con el vínculo al texto oficial.',
  },
  {
    icon: BarChart3, title: 'Estadísticas', href: '/dashboard',
    desc: 'El pulso normativo porteño en números: actividad por tipo y sector, organismos más activos, tendencias históricas.',
  },
  {
    icon: FileBarChart, title: 'Reportes', href: '/reportes',
    desc: 'Pedí un reporte con tus palabras o armalo con filtros: por ejemplo, las licitaciones de obra pública del último año. Con gráficos, CSV y envío programado por correo. Requiere iniciar sesión.',
  },
];

export default async function Landing() {
  const stats = await getStats();
  const total = stats?.total_normas ?? 0;
  const sectores = stats?.por_sector?.length ?? 9;
  const fmt = (n) => n.toLocaleString('es-AR');

  const CIFRAS = [
    { num: total > 0 ? fmt(total) : '—', label: 'Normas indexadas', detail: 'decretos, resoluciones, disposiciones, edictos y avisos' },
    { num: '1', label: 'Fuente oficial', detail: 'api del boletín oficial de la ciudad, sin intermediarios' },
    { num: String(sectores), label: 'Sectores detectados', detail: 'salud, educación, ambiente, transporte y más' },
    { num: '24/7', label: 'Monitoreo continuo', detail: 'ingesta diaria a las 9:00 hs con reintento a las 13:00 hs' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* ── Hero: gradiente institucional + trama ── */}
      <header className="grad-institucional relative overflow-hidden text-white">
        <div className="trama" />
        <div className="blob w-[520px] h-[520px] -right-32 -top-40 bg-[rgba(0,250,185,0.28)]" />
        <div className="blob w-[420px] h-[420px] right-64 -bottom-56 bg-[rgba(78,131,251,0.35)]" />

        <nav className="relative max-w-6xl mx-auto px-5 md:px-10 pt-6 flex items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-3.5 text-white">
            <img src="/brand/cesba-logo-blanco.png" alt="CESBA — Consejo Económico y Social de la Ciudad de Buenos Aires" width={64} height={64} className="w-14 h-14 md:w-16 md:h-16" />
            <span className="flex flex-col gap-0.5 border-l border-white/30 pl-3.5">
              <span className="text-[14px] md:text-[15px] font-bold tracking-[0.06em]">MONITOR BOCBA</span>
              <span className="hidden sm:block text-[12px] text-white/85">boletín oficial de la ciudad</span>
            </span>
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/auth/signin" className="btn-ghost-invert hidden sm:inline-flex items-center min-h-11 px-4 text-[12px] font-semibold">
              Iniciar sesión
            </Link>
            <Link href="/feed" className="btn-celeste inline-flex items-center gap-2 min-h-11 px-5 text-[12px] font-bold">
              Entrar <ArrowRight size={16} />
            </Link>
          </div>
        </nav>

        <div className="relative max-w-6xl mx-auto px-5 md:px-10 pt-20 pb-24 md:pt-28 md:pb-28 flex flex-col gap-7">
          <FadeIn>
            <p className="text-[11px] md:text-[12px] font-medium tracking-[0.14em] text-white/85">
              CONSEJO ECONÓMICO Y SOCIAL DE LA CIUDAD DE BUENOS AIRES
            </p>
          </FadeIn>
          <FadeIn delay={80}>
            <div className="title-rule-vital flex flex-col gap-4">
              <h1 className="display-hero max-w-4xl">La normativa porteña, al día</h1>
              <p className="text-[19px] md:text-[23px] font-light leading-snug">
                monitor interno del boletín oficial de la ciudad de buenos aires
              </p>
            </div>
          </FadeIn>
          <FadeIn delay={160}>
            <p className="max-w-xl text-[16px] md:text-[17px] leading-relaxed text-white/85">
              Cada norma indexada, resumida con IA en lenguaje claro y con alertas por correo
              cuando se publica algo que te importa. Datos oficiales, actualizados cada mañana.
            </p>
          </FadeIn>
          <FadeIn delay={240}>
            <div className="flex flex-wrap gap-3">
              <Link href="/feed" className="btn-celeste inline-flex items-center gap-2.5 min-h-12 px-6 text-[13px] font-bold">
                Ver el boletín de hoy <ArrowRight size={18} />
              </Link>
              <Link href="#plataforma" className="btn-ghost-invert inline-flex items-center min-h-12 px-6 text-[13px] font-semibold">
                Conocé la plataforma
              </Link>
            </div>
          </FadeIn>
        </div>
      </header>

      {/* ── Cifras ── */}
      <section className="bg-humo border-b border-nube">
        <div className="max-w-6xl mx-auto px-5 md:px-10 py-12 md:py-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {CIFRAS.map((c, i) => (
            <FadeIn key={c.label} delay={i * 70}>
              <div className="flex flex-col gap-2">
                <span className="text-[44px] md:text-[52px] font-bold leading-none text-petroleo tabular-nums">{c.num}</span>
                <span className="text-[12px] font-semibold tracking-[0.14em] uppercase text-petroleo">{c.label}</span>
                <span className="text-[14px] leading-snug text-text-tertiary">{c.detail}</span>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* ── Módulos ── */}
      <section id="plataforma" className="relative overflow-hidden scroll-mt-16">
        <div className="trama-clara" />
        <div className="relative max-w-6xl mx-auto px-5 md:px-10 py-16 md:py-24 flex flex-col gap-10 md:gap-12">
          <FadeIn>
            <div className="title-rule flex flex-col gap-2">
              <h2 className="display-section text-petroleo">La plataforma</h2>
              <p className="text-[17px] md:text-[19px] text-text-tertiary">cinco módulos, un solo radar normativo</p>
            </div>
          </FadeIn>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
            {MODULES.map(({ icon: Icon, title, desc, href }, i) => (
              <FadeIn key={title} delay={i * 70} className="h-full">
                <Link href={href} className="card card-accent group h-full flex flex-col gap-3.5 px-6 py-7 shadow-[0_4px_14px_rgba(21,59,112,0.10)] hover:shadow-[0_18px_48px_rgba(21,59,112,0.16)] transition-shadow">
                  <Icon size={28} strokeWidth={1.75} className="text-petroleo" />
                  <h3 className="text-[16px] font-bold tracking-[0.06em] uppercase text-petroleo">{title}</h3>
                  <p className="text-[14px] leading-relaxed text-text-secondary flex-1">{desc}</p>
                  <span className="text-[12px] font-semibold tracking-[0.06em] uppercase text-celeste inline-flex items-center gap-1.5">
                    Abrir <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </Link>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ── Acceso ── */}
      <section className="bg-humo border-t border-nube">
        <div className="max-w-6xl mx-auto px-5 md:px-10 py-16 md:py-22 flex flex-wrap gap-8 items-center justify-between">
          <FadeIn>
            <div className="flex flex-col gap-2 max-w-2xl">
              <h2 className="text-[24px] md:text-[29px] font-bold tracking-[0.04em] uppercase text-petroleo leading-tight">
                La Ciudad publica. Vos te enterás.
              </h2>
              <p className="text-[16px] md:text-[17px] text-text-tertiary">herramienta interna del cesba · acceso con cuenta institucional</p>
            </div>
          </FadeIn>
          <Link href="/auth/signin" className="btn-celeste inline-flex items-center min-h-12 px-6 text-[13px] font-bold">
            Iniciar sesión
          </Link>
        </div>
      </section>

      {/* ── Footer institucional ── */}
      <footer className="bg-azul-profundo text-white mt-auto">
        <div className="max-w-6xl mx-auto px-5 md:px-10 pt-10 flex flex-wrap gap-8 justify-between items-start">
          <img src="/brand/cesba-logo-blanco.png" alt="CESBA" width={72} height={72} className="w-[72px] h-[72px]" />
          <div className="flex flex-wrap gap-12 text-[13px] leading-[1.9]">
            <div className="flex flex-col">
              <span className="text-[12px] font-semibold tracking-[0.14em] text-white/70 mb-1">PLATAFORMA</span>
              <Link href="/feed" className="hover:underline">Boletín del día</Link>
              <Link href="/search" className="hover:underline">Buscador</Link>
              <Link href="/alerts" className="hover:underline">Alertas</Link>
              <Link href="/dashboard" className="hover:underline">Estadísticas</Link>
            </div>
            <div className="flex flex-col">
              <span className="text-[12px] font-semibold tracking-[0.14em] text-white/70 mb-1">FUENTE</span>
              <span>Boletín Oficial CABA</span>
              <span>api-restboletinoficial.buenosaires.gob.ar</span>
              <span>Actualización diaria automática</span>
            </div>
          </div>
        </div>
        <p className="max-w-6xl mx-auto px-5 md:px-10 pt-8 text-[11px] text-white/70">
          Basado en{' '}
          <a href="https://github.com/colossus-lab/vigia" target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:text-white">Vigía</a>
          , de Colossus Lab · Licencia MIT
        </p>
        <div className="mt-5 border-t border-white/30">
          <div className="max-w-6xl mx-auto px-5 md:px-10 min-h-11 py-2 flex flex-wrap gap-2 items-center justify-between text-[12px] tracking-[0.06em]">
            <a href="https://www.cesba.gob.ar" target="_blank" rel="noopener noreferrer" className="font-semibold hover:underline">www.cesba.gob.ar</a>
            <span className="text-white/85">CONSEJO ECONÓMICO Y SOCIAL DE LA CIUDAD DE BUENOS AIRES</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
