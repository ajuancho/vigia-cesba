'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Newspaper, BarChart3, Search, Bell, FileBarChart, Landmark, Scale, X } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/feed', label: 'Boletín del día', icon: Newspaper },
  { to: '/legislatura', label: 'Legislatura', icon: Landmark },
  { to: '/tribunal', label: 'Tribunal Superior', icon: Scale },
  { to: '/search', label: 'Buscador', icon: Search },
  { to: '/alerts', label: 'Alertas', icon: Bell },
  { to: '/dashboard', label: 'Estadísticas', icon: BarChart3 },
  { to: '/reportes', label: 'Reportes', icon: FileBarChart },
];

export default function Sidebar({ open, onClose }) {
  const pathname = usePathname();
  return (
    <>
      {open && <div className="fixed inset-0 bg-navy-950/30 z-40 lg:hidden" onClick={onClose} />}

      <aside
        className={`bg-marca print:hidden fixed top-0 left-0 h-full w-60 text-white z-50 flex flex-col overflow-hidden transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="relative px-5 py-5 border-b border-white/25">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex flex-col gap-1.5">
              <img src="/brand/nuevosbaires-logo-blanco.svg" alt="nuevosBAires" width={160} height={34} className="h-[30px] w-auto" />
              <span className="text-[11px] font-medium tracking-[0.14em] text-white/85">MONITOR NORMATIVO</span>
            </Link>
            <button onClick={onClose} aria-label="Cerrar menú" className="lg:hidden p-1 text-white/85 hover:text-white">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="relative flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const isActive = pathname === to || pathname.startsWith(to + '/');
            return (
              <Link
                key={to}
                href={to}
                onClick={onClose}
                aria-current={isActive ? 'page' : undefined}
                className={`flex items-center gap-3 px-3.5 min-h-11 rounded text-[12px] uppercase tracking-[0.06em] transition-colors ${
                  isActive
                    ? 'bg-lima text-carbon font-bold'
                    : 'text-white font-medium hover:bg-white/15'
                }`}
              >
                <Icon size={18} strokeWidth={1.75} className="shrink-0" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="relative px-5 py-4 border-t border-white/25 space-y-1">
          <a href="https://nuevosbaires.com.ar" target="_blank" rel="noopener noreferrer" className="block text-[11px] font-semibold text-white hover:underline">
            nuevosbaires.com.ar
          </a>
          <p className="text-[10px] text-white/85 leading-relaxed">
            Basado en{' '}
            <a href="https://github.com/colossus-lab/vigia" target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:text-white">Vigía</a>
            , de Colossus Lab · MIT
          </p>
        </div>
      </aside>
    </>
  );
}
