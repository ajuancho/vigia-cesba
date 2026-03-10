import React from 'react';
import { STATS_DNU, NORMAS_FEED } from '../data/mockData';
import { useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle, CheckCircle, Timer, Clock, ArrowRight, Scale, Building2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white border border-border-light rounded-lg p-3 shadow-lg">
            <p className="text-xs font-semibold text-text-primary mb-1">{label}</p>
            <p className="text-[11px] text-text-secondary">DNU emitidos: <span className="font-semibold text-text-primary">{payload[0].value}</span></p>
        </div>
    );
};

const DNUTrackerView = () => {
    const navigate = useNavigate();
    const dnuNormas = NORMAS_FEED.filter(n => n.tipo === 'DNU');

    return (
        <div className="max-w-5xl mx-auto animate-fade-in">
            <div className="mb-6">
                <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Tracker de DNU</h2>
                <p className="text-sm text-text-tertiary">Seguimiento de Decretos de Necesidad y Urgencia — Comisión Bicameral</p>
            </div>

            {/* Context */}
            <div className="card p-5 mb-5 border-l-4 border-l-amber-400">
                <div className="flex items-start gap-3">
                    <Scale size={16} className="text-status-amber shrink-0 mt-0.5" />
                    <div>
                        <h3 className="text-sm font-semibold text-text-primary mb-1">¿Qué son los DNU?</h3>
                        <p className="text-[12px] text-text-secondary leading-relaxed">
                            Los <strong>Decretos de Necesidad y Urgencia</strong> son medidas legislativas dictadas por el Poder Ejecutivo en circunstancias excepcionales.
                            En Argentina, <strong className="text-status-amber">mantienen vigencia por aprobación tácita</strong>: solo pierden efecto si ambas cámaras del Congreso los rechazan.
                            La Comisión Bicameral Permanente tiene <strong>10 días</strong> para emitir dictamen.
                        </p>
                    </div>
                </div>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                {[
                    { icon: Shield, label: 'Total 2026', value: STATS_DNU.total2026, sub: 'DNU emitidos', color: 'text-text-primary' },
                    { icon: Timer, label: 'Pendientes', value: STATS_DNU.pendientes, sub: 'Sin tratamiento', color: 'text-status-amber' },
                    { icon: CheckCircle, label: 'Aprobados', value: STATS_DNU.aprobados, sub: 'Ratificados', color: 'text-status-green' },
                    { icon: AlertTriangle, label: 'Rechazados', value: STATS_DNU.rechazados, sub: 'Por ambas cámaras', color: 'text-status-red' },
                ].map(({ icon: Icon, label, value, sub, color }) => (
                    <div key={label} className="card p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Icon size={14} className="text-text-tertiary" />
                            <span className="text-[9px] font-semibold text-text-tertiary uppercase tracking-wide">{label}</span>
                        </div>
                        <p className={`text-2xl font-bold ${color}`}>{value}</p>
                        <p className="text-[10px] text-text-tertiary">{sub}</p>
                    </div>
                ))}
            </div>

            {/* Chart */}
            <div className="card p-5 mb-6">
                <h3 className="text-sm font-semibold text-text-primary mb-0.5">DNU emitidos por año</h3>
                <p className="text-[11px] text-text-tertiary mb-5">Evolución histórica 2020–2026</p>
                <ResponsiveContainer width="100%" height={230}>
                    <BarChart data={STATS_DNU.historico}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ebeef3" />
                        <XAxis dataKey="anio" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar dataKey="cantidad" name="DNU" fill="#1e3a5f" radius={[4, 4, 0, 0]} barSize={36} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* DNU List */}
            <div className="mb-3">
                <h3 className="text-sm font-semibold text-text-primary mb-0.5">DNU recientes</h3>
                <p className="text-[11px] text-text-tertiary">Últimos decretos monitoreados</p>
            </div>

            <div className="space-y-2">
                {dnuNormas.map(dnu => (
                    <div
                        key={dnu.id}
                        onClick={() => navigate(`/norma/${dnu.id}`)}
                        className="card card-hover p-4 cursor-pointer group transition-all"
                    >
                        <div className="flex items-start gap-3">
                            <div className="w-1 h-10 rounded-full bg-status-red shrink-0 mt-0.5" />
                            <div className="flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                                    <span className="text-[10px] font-semibold text-status-red uppercase">DNU {dnu.numero}</span>
                                    <span className={`text-[9px] font-medium px-2 py-0.5 rounded border ${dnu.estado.includes('Pendiente')
                                            ? 'bg-amber-50 text-status-amber border-amber-200'
                                            : 'bg-green-50 text-status-green border-green-200'
                                        }`}>
                                        {dnu.estado.includes('Pendiente') ? 'Pendiente Bicameral' : 'Vigente'}
                                    </span>
                                </div>
                                <h4 className="text-[13px] font-semibold text-text-primary group-hover:text-inst-accent transition-colors mb-0.5">{dnu.titulo}</h4>
                                <p className="text-[12px] text-text-tertiary line-clamp-1">{dnu.resumen}</p>
                                <div className="flex items-center gap-3 mt-1.5 text-[10px] text-text-tertiary">
                                    <span className="flex items-center gap-1"><Clock size={9} /> {dnu.fecha}</span>
                                    <span className="flex items-center gap-1"><Building2 size={9} /> {dnu.organismo}</span>
                                </div>
                            </div>
                            <ArrowRight size={12} className="text-text-tertiary group-hover:text-inst-accent shrink-0 mt-2 transition-colors" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DNUTrackerView;
