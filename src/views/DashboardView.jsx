import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, AreaChart, Area, CartesianGrid
} from 'recharts';
import { STATS_PRODUCCION, STATS_SECTORES, STATS_DNU, NORMAS_FEED } from '../data/mockData';
import { FileText, Shield, Scale, Gavel } from 'lucide-react';

const COLORS = ['#1e3a5f', '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#db2777', '#64748b'];

const StatCard = ({ title, value, subtitle, icon: Icon, trend }) => (
    <div className="card p-5">
        <div className="flex items-start justify-between mb-3">
            <div className="p-2 rounded bg-bg-secondary">
                <Icon size={16} className="text-inst-blue" />
            </div>
            {trend && (
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${trend > 0 ? 'bg-green-50 text-status-green' : 'bg-red-50 text-status-red'
                    }`}>
                    {trend > 0 ? '+' : ''}{trend}%
                </span>
            )}
        </div>
        <p className="text-2xl font-bold text-text-primary mb-0.5">{value}</p>
        <p className="text-[12px] font-medium text-text-primary">{title}</p>
        <p className="text-[11px] text-text-tertiary">{subtitle}</p>
    </div>
);

const ChartTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="bg-white border border-border-light rounded-lg p-3 shadow-lg">
            <p className="text-xs font-semibold text-text-primary mb-1">{label}</p>
            {payload.map((entry, i) => (
                <p key={i} className="text-[11px] text-text-secondary">
                    <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ backgroundColor: entry.color }} />
                    {entry.name}: <span className="font-semibold text-text-primary">{entry.value}</span>
                </p>
            ))}
        </div>
    );
};

const DashboardView = () => {
    const produccionData = STATS_PRODUCCION.labels.map((label, i) => ({
        mes: label,
        Leyes: STATS_PRODUCCION.leyes[i],
        Decretos: STATS_PRODUCCION.decretos[i],
        DNU: STATS_PRODUCCION.dnu[i],
    }));

    const sectorData = STATS_SECTORES.map(s => ({ name: s.sector, value: s.cantidad }));

    return (
        <div className="max-w-7xl mx-auto animate-fade-in">
            <div className="mb-6">
                <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Estadísticas</h2>
                <p className="text-sm text-text-tertiary">Producción legislativa y regulatoria — 2026</p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <StatCard title="Normas publicadas" value="390" subtitle="Último trimestre" icon={FileText} trend={12} />
                <StatCard title="DNU vigentes" value={STATS_DNU.total2026} subtitle={`${STATS_DNU.pendientes} pendientes bicameral`} icon={Shield} trend={-8} />
                <StatCard title="Leyes sancionadas" value="62" subtitle="Acumulado 2026" icon={Scale} trend={15} />
                <StatCard title="Proyectos activos" value="847" subtitle="En comisiones" icon={Gavel} />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
                <div className="lg:col-span-2 card p-5">
                    <h3 className="text-sm font-semibold text-text-primary mb-0.5">Producción normativa mensual</h3>
                    <p className="text-[11px] text-text-tertiary mb-5">Distribución por tipo — 2025</p>
                    <ResponsiveContainer width="100%" height={260}>
                        <AreaChart data={produccionData}>
                            <defs>
                                <linearGradient id="fillLeyes" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#059669" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="fillDecretos" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#d97706" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#d97706" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="fillDNU" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ebeef3" />
                            <XAxis dataKey="mes" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Area type="monotone" dataKey="Leyes" stroke="#059669" fillOpacity={1} fill="url(#fillLeyes)" strokeWidth={1.5} />
                            <Area type="monotone" dataKey="Decretos" stroke="#d97706" fillOpacity={1} fill="url(#fillDecretos)" strokeWidth={1.5} />
                            <Area type="monotone" dataKey="DNU" stroke="#dc2626" fillOpacity={1} fill="url(#fillDNU)" strokeWidth={1.5} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="card p-5">
                    <h3 className="text-sm font-semibold text-text-primary mb-0.5">Por sector</h3>
                    <p className="text-[11px] text-text-tertiary mb-4">Distribución sectorial</p>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={sectorData} cx="50%" cy="50%" innerRadius={45} outerRadius={72} paddingAngle={1} dataKey="value">
                                {sectorData.map((_, index) => (
                                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip content={<ChartTooltip />} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="grid grid-cols-2 gap-x-3 gap-y-1 mt-3">
                        {STATS_SECTORES.slice(0, 6).map((s, i) => (
                            <div key={s.sector} className="flex items-center gap-1.5">
                                <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLORS[i] }} />
                                <span className="text-[10px] text-text-secondary truncate">{s.sector} ({s.porcentaje}%)</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Bottom charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="card p-5">
                    <h3 className="text-sm font-semibold text-text-primary mb-0.5">DNU por año</h3>
                    <p className="text-[11px] text-text-tertiary mb-5">Evolución histórica</p>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={STATS_DNU.historico}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ebeef3" />
                            <XAxis dataKey="anio" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar dataKey="cantidad" name="DNU emitidos" fill="#1e3a5f" radius={[4, 4, 0, 0]} barSize={28} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                <div className="card p-5">
                    <h3 className="text-sm font-semibold text-text-primary mb-0.5">Estado de DNU 2026</h3>
                    <p className="text-[11px] text-text-tertiary mb-5">Seguimiento bicameral</p>
                    <div className="space-y-4">
                        {[
                            { label: 'Total emitidos', value: STATS_DNU.total2026, color: '#1e3a5f', pct: 100 },
                            { label: 'Pendientes', value: STATS_DNU.pendientes, color: '#d97706', pct: (STATS_DNU.pendientes / STATS_DNU.total2026) * 100 },
                            { label: 'Aprobados', value: STATS_DNU.aprobados, color: '#059669', pct: (STATS_DNU.aprobados / STATS_DNU.total2026) * 100 },
                            { label: 'Rechazados', value: STATS_DNU.rechazados, color: '#dc2626', pct: (STATS_DNU.rechazados / STATS_DNU.total2026) * 100 },
                        ].map(item => (
                            <div key={item.label}>
                                <div className="flex justify-between text-[12px] mb-1.5">
                                    <span className="text-text-secondary">{item.label}</span>
                                    <span className="font-semibold text-text-primary">{item.value}</span>
                                </div>
                                <div className="w-full bg-bg-tertiary rounded-full h-1.5">
                                    <div className="h-1.5 rounded-full transition-all duration-700" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="mt-5 p-3 bg-amber-50 border border-amber-200 rounded">
                        <p className="text-[11px] text-status-amber">
                            {STATS_DNU.pendientes} DNU sin tratamiento por la Comisión Bicameral. Mantienen vigencia por aprobación tácita (Art. 99 inc. 3 CN).
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardView;
