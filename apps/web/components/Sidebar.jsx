'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Newspaper, BarChart3, Search, Bell, Shield, X, Eye, Landmark } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/feed', label: 'Feed Normativo', icon: Newspaper },
  { to: '/dashboard', label: 'Estadísticas', icon: BarChart3 },
  { to: '/search', label: 'Buscador', icon: Search },
  { to: '/alerts', label: 'Alertas', icon: Bell },
  { to: '/dnu', label: 'Tracker DNU', icon: Shield },
];

export default function Sidebar({ open, onClose }) {
  const pathname = usePathname();
  return (
    <>
      {open && <div className="fixed inset-0 bg-black/20 z-40 lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed top-0 left-0 h-full w-60 bg-navy-900 z-50 flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center">
                <Eye size={16} className="text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-white tracking-wide">VIGÍA</h1>
                <p className="text-[9px] text-white/40 uppercase tracking-[0.15em]">Inteligencia Legislativa</p>
              </div>
            </div>
            <button onClick={onClose} className="lg:hidden text-white/40 hover:text-white">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => {
            const isActive = pathname === to || pathname.startsWith(to + '/');
            return (
              <Link
                key={to}
                href={to}
                onClick={onClose}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded text-[13px] font-medium transition-colors ${
                  isActive ? 'bg-white/15 text-white' : 'text-white/50 hover:bg-white/5 hover:text-white/80'
                }`}
              >
                <Icon size={16} className="shrink-0" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-2">
            <Landmark size={12} className="text-white/30" />
            <p className="text-[10px] text-white/30">Colossus Lab</p>
          </div>
        </div>
      </aside>
    </>
  );
}
