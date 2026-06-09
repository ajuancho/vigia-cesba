'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { LogIn, LogOut, Settings } from 'lucide-react';
import { AUTH_ENABLED } from '@/lib/authClient';

export default function AuthButton() {
  const router = useRouter();
  const { data: session, status } = useSession();

  // Modo demo (sin credenciales OAuth): avatar estático, sin login.
  if (!AUTH_ENABLED) {
    return (
      <div className="w-7 h-7 rounded bg-navy-800 flex items-center justify-center text-white text-[10px] font-bold" title="Modo demo">
        CL
      </div>
    );
  }

  if (status === 'loading') {
    return <div className="w-7 h-7 rounded bg-bg-tertiary animate-pulse" />;
  }

  if (!session) {
    return (
      <button onClick={() => signIn('google')} className="flex items-center gap-1.5 px-3 py-1.5 bg-navy-800 text-white rounded text-[11px] font-medium hover:bg-navy-700 transition-colors">
        <LogIn size={13} /> Iniciar sesión
      </button>
    );
  }

  const initials = (session.workspace?.name || session.user?.name || '?').slice(0, 2).toUpperCase();
  return (
    <div className="flex items-center gap-2">
      <button onClick={() => router.push('/settings/workspace')} className="p-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors" title="Workspace">
        <Settings size={16} />
      </button>
      <button onClick={() => signOut()} className="p-1.5 rounded text-text-secondary hover:text-status-red hover:bg-red-50 transition-colors" title="Cerrar sesión">
        <LogOut size={16} />
      </button>
      <div className="w-7 h-7 rounded bg-navy-800 flex items-center justify-center text-white text-[10px] font-bold" title={session.user?.email}>
        {initials}
      </div>
    </div>
  );
}
