'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { SECTORES } from '@/lib/constants';
import { authedFetch, AUTH_ENABLED } from '@/lib/authClient';
import { Bell, Plus, Trash2, Power, PowerOff, Tag, Hash, Calendar, Info } from 'lucide-react';

export default function AlertsView() {
  const { data: session } = useSession();
  const jwt = session?.apiJwt;
  // Modo conectado: auth activa + sesión con JWT. Si no, demo client-side.
  const connected = AUTH_ENABLED && Boolean(jwt);

  const [alertas, setAlertas] = useState([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [newSector, setNewSector] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    if (!connected) return;
    try {
      const data = await authedFetch(jwt, '/alerts');
      setAlertas(data);
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

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Alertas</h2>
          <p className="text-sm text-text-tertiary">Monitoreo por keywords y sectores</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1.5 px-3 py-2 btn-celeste rounded-full text-[11px] font-bold">
          <Plus size={13} /> Nueva alerta
        </button>
      </div>

      {!connected && (
        <div className="card p-3 mb-5 border-l-4 border-l-inst-accent flex items-start gap-2">
          <Info size={14} className="text-inst-accent shrink-0 mt-0.5" />
          <p className="text-[12px] text-text-secondary leading-relaxed">
            {AUTH_ENABLED
              ? 'Iniciá sesión para que tus alertas se guarden y te lleguen por email.'
              : 'Vista previa: las alertas se persisten y notifican por email cuando la autenticación está activa. Por ahora viven solo en esta sesión.'}
          </p>
        </div>
      )}

      {err && <div className="card p-3 mb-4 border-l-4 border-l-status-red text-[12px] text-status-red">{err}</div>}

      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="card p-4 text-center">
          <p className="text-xl font-bold text-text-primary">{alertas.length}</p>
          <p className="text-[10px] text-text-tertiary uppercase tracking-wide font-medium">Total</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-xl font-bold text-status-green">{activas}</p>
          <p className="text-[10px] text-text-tertiary uppercase tracking-wide font-medium">Activas</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-xl font-bold text-inst-blue">{totalMatches}</p>
          <p className="text-[10px] text-text-tertiary uppercase tracking-wide font-medium">Matches</p>
        </div>
      </div>

      {showForm && (
        <div className="card p-5 mb-5 animate-slide-up">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Crear nueva alerta</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Keyword</label>
              <input type="text" value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} placeholder="ej: litio, ciberseguridad, energia..." className="w-full bg-bg-primary border border-border-light rounded-lg px-3 py-2 text-[13px] text-text-primary placeholder-text-tertiary focus:outline-none focus:border-inst-accent" />
            </div>
            <div>
              <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Sector</label>
              <select value={newSector} onChange={(e) => setNewSector(e.target.value)} className="w-full bg-bg-primary border border-border-light rounded-lg px-3 py-2 text-[13px] text-text-secondary focus:outline-none focus:border-inst-accent">
                <option value="">Todos</option>
                {SECTORES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addAlerta} className="px-3 py-1.5 btn-celeste rounded-full text-[11px] font-bold">Crear</button>
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-text-secondary text-[11px] font-medium hover:text-text-primary transition-colors">Cancelar</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {alertas.map((alerta) => (
          <div key={alerta.id} className={`card p-4 transition-all ${!alerta.activa ? 'opacity-50' : ''}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell size={16} className={alerta.activa ? 'text-inst-blue' : 'text-text-tertiary'} />
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <h4 className="text-[13px] font-semibold text-text-primary">&quot;{alerta.keyword}&quot;</h4>
                    {alerta.activa && <span className="text-[9px] font-medium tint-green px-1.5 py-0.5 rounded-full border">Activa</span>}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-text-tertiary">
                    <span className="flex items-center gap-1"><Tag size={9} /> {alerta.sector || 'Todos'}</span>
                    <span className="flex items-center gap-1"><Hash size={9} /> {alerta.matches || 0} matches</span>
                    {alerta.last_match_at && <span className="flex items-center gap-1"><Calendar size={9} /> {alerta.last_match_at.slice(0, 10)}</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => toggleAlerta(alerta)} className={`p-1.5 rounded transition-colors ${alerta.activa ? 'text-status-green hover:bg-status-green/10' : 'text-text-tertiary hover:bg-bg-tertiary'}`}>
                  {alerta.activa ? <Power size={14} /> : <PowerOff size={14} />}
                </button>
                <button onClick={() => deleteAlerta(alerta)} className="p-1.5 rounded text-text-tertiary hover:text-status-red hover:bg-status-red/10 transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {alertas.length === 0 && (
        <div className="text-center py-16">
          <Bell size={32} className="text-border-medium mx-auto mb-2" />
          <p className="text-text-tertiary text-sm">No hay alertas configuradas</p>
        </div>
      )}
    </div>
  );
}
