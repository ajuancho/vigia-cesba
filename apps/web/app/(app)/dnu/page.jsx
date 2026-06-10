'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Shield, AlertTriangle, CheckCircle, Timer, Clock, ArrowRight, Scale, Building2 } from 'lucide-react';

export default function DNUTrackerView() {
  const router = useRouter();
  const [dnu, setDnu] = useState(null);
  const [normas, setNormas] = useState([]);

  useEffect(() => {
    api.dnuStats().then(setDnu).catch(() => setDnu(null));
    api.listNormas({ tipo: 'DNU', limit: 50 }).then((d) => setNormas(d.items || [])).catch(() => setNormas([]));
  }, []);

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Tracker de DNU</h2>
        <p className="text-sm text-text-tertiary">Seguimiento de Decretos de Necesidad y Urgencia — Comisión Bicameral</p>
      </div>

      <div className="card p-5 mb-5 border-l-4 border-l-sol">
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

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {[
          { icon: Shield, label: 'En seguimiento', value: dnu?.total ?? 0, sub: 'DNU monitoreados', color: 'text-text-primary' },
          { icon: Timer, label: 'Pendientes', value: dnu?.pendientes ?? 0, sub: 'Sin tratamiento', color: 'text-status-amber' },
          { icon: CheckCircle, label: 'Aprobados', value: dnu?.aprobados ?? 0, sub: 'Ratificados', color: 'text-status-green' },
          { icon: AlertTriangle, label: 'Rechazados', value: dnu?.rechazados ?? 0, sub: 'Por ambas cámaras', color: 'text-status-red' },
        ].map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="card p-4">
            <div className="flex items-center gap-2 mb-2">
              <Icon size={14} className="text-text-tertiary" />
              <span className="text-[9px] font-semibold text-text-tertiary uppercase tracking-wide">{label}</span>
            </div>
            <p className={`text-2xl font-bold font-mono ${color}`}>{value}</p>
            <p className="text-[10px] text-text-tertiary">{sub}</p>
          </div>
        ))}
      </div>

      <div className="mb-3">
        <h3 className="text-sm font-semibold text-text-primary mb-0.5">DNU recientes</h3>
        <p className="text-[11px] text-text-tertiary">Últimos decretos monitoreados</p>
      </div>

      <div className="space-y-2">
        {normas.map((d) => {
          const estado = d.estado || '';
          const pendiente = estado.includes('Pendiente') || estado.includes('comisión');
          return (
            <div key={d.id} onClick={() => router.push(`/norma/${d.id}`)} className="card card-hover p-4 cursor-pointer group transition-all">
              <div className="flex items-start gap-3">
                <div className="w-1 h-10 rounded-full bg-status-red shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-semibold text-status-red uppercase">DNU {d.numero || ''}</span>
                    <span className={`text-[9px] font-medium px-2 py-0.5 rounded-full border ${pendiente ? 'tint-amber' : 'tint-green'}`}>
                      {pendiente ? 'Pendiente Bicameral' : 'Vigente'}
                    </span>
                  </div>
                  <h4 className="text-[13px] font-semibold text-text-primary group-hover:text-inst-accent transition-colors mb-0.5">{d.titulo}</h4>
                  {d.resumen && <p className="text-[12px] text-text-tertiary line-clamp-1">{d.resumen}</p>}
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-text-tertiary">
                    {d.fecha_publicacion && <span className="flex items-center gap-1"><Clock size={9} /> {d.fecha_publicacion}</span>}
                    {d.organismo && <span className="flex items-center gap-1"><Building2 size={9} /> {d.organismo}</span>}
                  </div>
                </div>
                <ArrowRight size={12} className="text-text-tertiary group-hover:text-inst-accent shrink-0 mt-2 transition-colors" />
              </div>
            </div>
          );
        })}
      </div>

      {normas.length === 0 && (
        <div className="text-center py-12 text-text-tertiary text-sm">
          No hay DNU en el corpus actual. La ingesta del corpus completo de InfoLEG los incorporará.
        </div>
      )}
    </div>
  );
}
