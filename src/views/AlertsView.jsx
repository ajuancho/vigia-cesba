import React, { useState } from 'react';
import { ALERTAS_EJEMPLO, SECTORES } from '../data/mockData';
import { Bell, Plus, Trash2, Power, PowerOff, Tag, Calendar, Hash } from 'lucide-react';

const AlertsView = () => {
    const [alertas, setAlertas] = useState(ALERTAS_EJEMPLO);
    const [newKeyword, setNewKeyword] = useState('');
    const [newSector, setNewSector] = useState('');
    const [showForm, setShowForm] = useState(false);

    const toggleAlerta = (id) => {
        setAlertas(prev => prev.map(a => a.id === id ? { ...a, activa: !a.activa } : a));
    };

    const deleteAlerta = (id) => {
        setAlertas(prev => prev.filter(a => a.id !== id));
    };

    const addAlerta = () => {
        if (!newKeyword.trim()) return;
        setAlertas(prev => [{
            id: `a${Date.now()}`, keyword: newKeyword.trim(), sector: newSector || 'Todos',
            activa: true, matches: 0, ultimaAlerta: 'Nueva',
        }, ...prev]);
        setNewKeyword('');
        setNewSector('');
        setShowForm(false);
    };

    const activas = alertas.filter(a => a.activa).length;

    return (
        <div className="max-w-3xl mx-auto animate-fade-in">
            <div className="flex items-start justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Alertas</h2>
                    <p className="text-sm text-text-tertiary">Monitoreo por keywords y sectores</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="flex items-center gap-1.5 px-3 py-2 bg-navy-800 text-white rounded text-[11px] font-medium hover:bg-navy-700 transition-colors"
                >
                    <Plus size={13} /> Nueva alerta
                </button>
            </div>

            {/* Stats */}
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
                    <p className="text-xl font-bold text-inst-blue">{alertas.reduce((sum, a) => sum + a.matches, 0)}</p>
                    <p className="text-[10px] text-text-tertiary uppercase tracking-wide font-medium">Matches</p>
                </div>
            </div>

            {/* New Alert Form */}
            {showForm && (
                <div className="card p-5 mb-5 animate-slide-up">
                    <h3 className="text-sm font-semibold text-text-primary mb-3">Crear nueva alerta</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <div>
                            <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Keyword</label>
                            <input
                                type="text" value={newKeyword} onChange={e => setNewKeyword(e.target.value)}
                                placeholder="ej: PYME, litio, ciberseguridad..."
                                className="w-full bg-white border border-border-light rounded px-3 py-2 text-[13px] text-text-primary placeholder-text-tertiary focus:outline-none focus:border-inst-accent"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wide mb-1 block">Sector</label>
                            <select value={newSector} onChange={e => setNewSector(e.target.value)} className="w-full bg-white border border-border-light rounded px-3 py-2 text-[13px] text-text-secondary focus:outline-none focus:border-inst-accent">
                                <option value="">Todos</option>
                                {SECTORES.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={addAlerta} className="px-3 py-1.5 bg-navy-800 text-white rounded text-[11px] font-medium hover:bg-navy-700 transition-colors">Crear</button>
                        <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-text-secondary text-[11px] font-medium hover:text-text-primary transition-colors">Cancelar</button>
                    </div>
                </div>
            )}

            {/* Alert List */}
            <div className="space-y-2">
                {alertas.map(alerta => (
                    <div key={alerta.id} className={`card p-4 transition-all ${!alerta.activa ? 'opacity-50' : ''}`}>
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Bell size={16} className={alerta.activa ? 'text-inst-blue' : 'text-text-tertiary'} />
                                <div>
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <h4 className="text-[13px] font-semibold text-text-primary">"{alerta.keyword}"</h4>
                                        {alerta.activa && (
                                            <span className="text-[9px] font-medium text-status-green bg-green-50 px-1.5 py-0.5 rounded border border-green-200">Activa</span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-3 text-[10px] text-text-tertiary">
                                        <span className="flex items-center gap-1"><Tag size={9} /> {alerta.sector}</span>
                                        <span className="flex items-center gap-1"><Hash size={9} /> {alerta.matches} matches</span>
                                        <span className="flex items-center gap-1"><Calendar size={9} /> {alerta.ultimaAlerta}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-1">
                                <button onClick={() => toggleAlerta(alerta.id)} className={`p-1.5 rounded transition-colors ${alerta.activa ? 'text-status-green hover:bg-green-50' : 'text-text-tertiary hover:bg-bg-tertiary'}`}>
                                    {alerta.activa ? <Power size={14} /> : <PowerOff size={14} />}
                                </button>
                                <button onClick={() => deleteAlerta(alerta.id)} className="p-1.5 rounded text-text-tertiary hover:text-status-red hover:bg-red-50 transition-colors">
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
};

export default AlertsView;
