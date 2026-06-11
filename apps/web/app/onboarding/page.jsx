'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { Eye, Check } from 'lucide-react';
import { SECTORES } from '@/lib/constants';
import { authedFetch } from '@/lib/authClient';

export default function OnboardingPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [name, setName] = useState('');
  const [selected, setSelected] = useState([]);
  const [saving, setSaving] = useState(false);

  const toggle = (s) => setSelected((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));

  const submit = async () => {
    setSaving(true);
    try {
      await authedFetch(session?.apiJwt, '/workspaces/me/onboarding', {
        method: 'POST',
        body: JSON.stringify({ name: name || undefined, sectores_interes: selected }),
      });
      router.push('/feed');
    } catch {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="flag-stripe fixed top-0 inset-x-0 z-[60]" />
      <div className="card p-8 max-w-lg w-full">
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-9 h-9 rounded-lg bg-celeste/10 border border-celeste/30 flex items-center justify-center">
            <Eye size={18} className="text-celeste" />
          </div>
          <div>
            <h1 className="text-base font-bold text-text-primary">ConfigurÃ¡ tu workspace</h1>
            <p className="text-[12px] text-text-tertiary">PersonalizÃ¡ VigÃ­a para tu organizaciÃ³n</p>
          </div>
        </div>

        <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Nombre del workspace</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={session?.workspace?.name || 'Mi organizaciÃ³n'}
          className="w-full bg-bg-primary border border-border-light rounded-lg px-3 py-2 text-[13px] mb-5 focus:outline-none focus:border-inst-accent"
        />

        <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-2 block">Sectores de interÃ©s</label>
        <div className="flex flex-wrap gap-2 mb-6">
          {SECTORES.map((s) => (
            <button
              key={s}
              onClick={() => toggle(s)}
              className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors flex items-center gap-1 ${
                selected.includes(s)
                  ? 'bg-celeste/10 text-celeste-bright border-celeste/40'
                  : 'bg-bg-primary text-text-secondary border-border-light hover:bg-bg-tertiary'
              }`}
            >
              {selected.includes(s) && <Check size={11} />} {s}
            </button>
          ))}
        </div>

        <button
          onClick={submit}
          disabled={saving}
          className="w-full px-4 py-2.5 btn-celeste rounded-full text-[13px] font-bold disabled:opacity-50"
        >
          {saving ? 'Guardandoâ€¦' : 'Continuar'}
        </button>
      </div>
    </div>
  );
}
