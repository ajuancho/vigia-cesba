'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { SECTORES } from '@/lib/constants';
import { authedFetch, AUTH_ENABLED } from '@/lib/authClient';
import { Bell, Plus, Trash2, Power, PowerOff, Tag, Hash, Calendar, Info } from 'lucide-react';
import FadeIn from '@/components/FadeIn';
import CountUp from '@/components/CountUp';

const INPUT_CLS = 'w-full bg-transparent border-b border-border-light px-1 py-2 text-[13px] text-text-primary placeholder-text-tertiary focus:outline-none focus:border-celeste transition-colors';

export default function AlertsView() {
  const { data: session } = useSession();
  const jwt = session?.apiJwt;
  const connected = AUTH_ENABLED && Boolean(jwt);

  const [alertas, setAlertas] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [newSector, setNewSector] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    if (!connected) return;
    try {
      setAlertas(await authedFetch(jwt, '/alerts'));
    } catch (e) { setErr(String(e.message || e)); }
  }, [connected, jwt]);

  useEffect(() => { load(); }, [load]);

  const addAlerta = async () => {
    if (!newKeyword.trim()) return;
    if (connected) {
      try {
        await authedFetch(jwt, '/alerts', {
          method: 'POST',
          body: JSON.stringify({ keyword: newKeyword.trim(), sector: newSector || null }),
        });
        await load();
      } catch (e) { setErr(String(e.message || e)); }
    } else {
      setAlertas((prev) => [
        { id: `local-${Date.now()}`, keyword: newKeyword.trim(), sector: newSector || null, activa: true, matches: 0, last_match_at: null },
        ...prev,
      ]);
    }
    setNewKeyword(''); setNewSector(''); setShowForm(false);
  };

  const toggleAlerta = async (a) => {
    if (connected) {
      await authedFetch(jwt, `/alerts/${a.id}`, { method: 'PATCH', body: JSON.stringify({ activa: !a.activa }) });
      load();
    } else {
      setAlertas((prev) => prev.map((x) => (x.id === a.id ? { ...x, activa: !x.activa } : x)));
    }
  };

  const deleteAlerta = async (a) => {
    if (connected) {
      await authedFetch(jwt, `/alerts/${a.id}`, { method: 'DELETE' });
      load();
    } else {
      setAlertas((prev) => prev.filter((x) => x.id !== a.id));
    }
  };

  const activas = alertas.filter((a) => a.activa).length;
  const totalMatches = alertas.reduce((s, a) => s + (a.matches || 0), 0);

  const KPIS = [
    { label: 'Alertas', value: alertas.length, color: 'text-text-primary' },
    { label: 'Activas', value: activas, color: 'text-status-green' },
    { label: 'Matches', value: totalMatches, color: 'text-celeste' },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      <FadeIn>
        <div className="flex items-end justify-between gap-4 mb-7 pt-2">
          <div>
            <p className="eyebrow mb-1"><span className="eyebrow-num">VIGÍA / ALERTAS</span><span className="ml-2">Monitoreo automático</span></p>
            <h2 className="display-section text-text-primary mb-1">Que la norma <em>te encuentre.</em></h2>
            <p className="text-[13px] text-text-tertiary font-mono">keyword + sector · matching horario · digest por email</p>
          </div>
          <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1.5 px-4 py-2 btn-celeste rounded-full text-[11px] font-bold shrink-0">
            <Plus size={13} /> Nueva
          </button>
        </div>
      </FadeIn>

      {!connected && (
        <FadeIn delay={60}>
          <div className="flex items-start gap-2 border-l-2 border-celeste pl-4 py-1 mb-8">
            <Info size={13} className="text-celeste shrink-0 mt-0.5" />
            <p className="text-[12px] text-text-secondary leading-relaxed">
              {AUTH_ENABLED ? 'Iniciá sesión para que tus alertas se guarden y lleguen por email.' : 'Vista demo: las alertas viven solo en esta sesión.'}
            </p>
          </div>
        </FadeIn>
      )}

      {err && <p className="text-[12px] text-status-red mb-4 font-mono">{err}</p>}

      {/* KPIs flotantes */}
      <div className="grid grid-cols-3 border-t-2 border-text-primary/70 mb-10">
        {KPIS.map(({ label, value, color }, i) => (
          <FadeIn key={label} delay={i * 80}>
            <div className="pt-4 pb-5 lg:border-r border-border-light lg:px-5 first:pl-0 transition-colors duration-300 hover:bg-celeste/[0.03]">
              <p className={`font-mono font-bold text-3xl leading-none mb-1.5 ${color}`}><CountUp value={value} /></p>
              <p className="eyebrow text-[9px]">{label}</p>
            </div>
          </FadeIn>
        ))}
      </div>

      {/* Form flotante */}
      {showForm && (
        <div className="mb-10 animate-slide-up border-l-2 border-celeste pl-5 py-1">
          <p className="eyebrow mb-4"><span className="eyebrow-num">+</span><span className="ml-2">Nueva alerta</span></p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-4">
            <div>
              <label className="eyebrow text-[9px] block mb-1">Keyword</label>
              <input type="text" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} placeholder="litio, ciberseguridad, SMVM…" className={INPUT_CLS} autoFocus />
            </div>
            <div>
              <label className="eyebrow text-[9px] block mb-1">Sector (opcional)</label>
              <select value={newSector} onChange={(e) => setNewSector(e.target.value)} className={INPUT_CLS}>
                <option value="">Todos</option>
                {SECTORES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={addAlerta} className="px-4 py-1.5 btn-celeste rounded-full text-[11px] font-bold">Crear</button>
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-text-secondary text-[11px] font-medium hover:text-text-primary transition-colors">Cancelar</button>
          </div>
        </div>
      )}

      {/* Lista editorial */}
      <div className="border-t border-border-light">
        {alertas.map((alerta, i) => (
          <FadeIn key={alerta.id} delay={Math.min(i * 50, 300)}>
            <div className={`group flex items-center justify-between gap-3 border-b border-border-light py-4 transition-all duration-300 hover:bg-celeste/[0.03] hover:pl-2 ${!alerta.activa ? 'opacity-40' : ''}`}>
              <div className="flex items-center gap-3 min-w-0">
                <Bell size={15} className={alerta.activa ? 'text-celeste' : 'text-text-tertiary'} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-[14px] font-semibold text-text-primary truncate" style={{ fontFamily: 'var(--font-display)' }}>
                      “{alerta.keyword}”
                    </h4>
                    {alerta.activa && <span className="text-[9px] font-medium tint-green border px-1.5 py-0.5 rounded-full shrink-0">activa</span>}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-text-tertiary font-mono">
                    <span className="flex items-center gap-1"><Tag size={9} /> {alerta.sector || 'todos'}</span>
                    <span className="flex items-center gap-1"><Hash size={9} /> {(alerta.matches || 0).toLocaleString('es-AR')} matches</span>
                    {alerta.last_match_at && <span className="flex items-center gap-1"><Calendar size={9} /> {alerta.last_match_at.slice(0, 10)}</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button onClick={() => toggleAlerta(alerta)} className={`p-1.5 rounded-lg transition-colors ${alerta.activa ? 'text-status-green hover:bg-status-green/10' : 'text-text-tertiary hover:bg-bg-tertiary'}`}>
                  {alerta.activa ? <Power size={14} /> : <PowerOff size={14} />}
                </button>
                <button onClick={() => deleteAlerta(alerta)} className="p-1.5 rounded-lg text-text-tertiary hover:text-status-red hover:bg-status-red/10 transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </FadeIn>
        ))}
      </div>

      {alertas.length === 0 && (
        <div className="text-center py-16">
          <Bell size={28} className="text-text-tertiary/40 mx-auto mb-3" />
          <p className="text-text-tertiary text-sm">Sin alertas todavía — creá la primera.</p>
        </div>
      )}
    </div>
  );
}
