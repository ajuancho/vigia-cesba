'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { TIPOS_NORMA } from '@/lib/constants';
import {
  ArrowLeft, Clock, Building2, MapPin, Tag, FileText,
  Users, ExternalLink, BookOpen,
} from 'lucide-react';

const TIPO_BADGE = {
  DNU: 'tint-red',
  DECRETO: 'tint-amber',
  LEY: 'tint-green',
  RESOLUCION: 'tint-blue',
  DISPOSICION: 'tint-purple',
  PROYECTO: 'tint-cyan',
  OTRA: 'tint-gray',
};

export default function NormDetailView() {
  const { id } = useParams();
  const router = useRouter();
  const [norma, setNorma] = useState(undefined); // undefined=loading, null=not found

  useEffect(() => {
    api.getNorma(id).then(setNorma).catch(() => setNorma(null));
  }, [id]);

  if (norma === undefined) {
    return <div className="max-w-3xl mx-auto text-center py-20 text-text-tertiary">Cargando…</div>;
  }

  if (norma === null) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <p className="text-text-tertiary">Norma no encontrada</p>
        <button onClick={() => router.push('/feed')} className="text-inst-accent text-sm mt-3 hover:underline">Volver al feed</button>
      </div>
    );
  }

  const tipoMeta = TIPOS_NORMA[norma.tipo] || TIPOS_NORMA.OTRA;
  const estado = norma.estado || '';
  const estadoStyle = estado.includes('Vigente') || estado.includes('Publicada')
    ? 'tint-green'
    : estado.includes('comisión')
      ? 'tint-amber'
      : 'tint-blue';

  return (
    <div className="max-w-3xl mx-auto animate-fade-in">
      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-text-tertiary hover:text-text-primary text-[13px] mb-5 transition-colors">
        <ArrowLeft size={14} /> Volver
      </button>

      <div className="card p-6 mb-4">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className={`px-2.5 py-1 rounded text-[10px] font-semibold uppercase tracking-wide border ${TIPO_BADGE[norma.tipo] || TIPO_BADGE.OTRA}`}>
            {tipoMeta.label} {norma.numero || ''}
          </span>
          {estado && <span className={`px-2.5 py-1 rounded text-[10px] font-medium border ${estadoStyle}`}>{estado}</span>}
        </div>

        <h1 className="text-lg font-bold text-text-primary leading-snug mb-5">{norma.titulo}</h1>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border-light">
          {[
            { icon: Clock, label: 'Publicación', value: norma.fecha_publicacion },
            { icon: Building2, label: 'Organismo', value: norma.organismo },
            { icon: MapPin, label: 'Jurisdicción', value: norma.jurisdiccion },
            { icon: Tag, label: 'Sector', value: norma.sector },
          ].filter((f) => f.value).map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-start gap-2">
              <Icon size={13} className="text-text-tertiary mt-0.5 shrink-0" />
              <div>
                <p className="text-[9px] text-text-tertiary uppercase tracking-wide">{label}</p>
                <p className="text-[12px] font-medium text-text-primary">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Análisis automático — solo cuando hay IA (Fase 5) */}
      {norma.resumen_ia && (
        <div className="card p-6 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <FileText size={14} className="text-inst-blue" />
            <h3 className="text-sm font-semibold text-text-primary">Análisis automático</h3>
            <span className="text-[9px] font-medium tint-blue px-2 py-0.5 rounded-full border ml-auto">Vigía AI</span>
          </div>
          <div className="bg-bg-secondary border border-border-light rounded p-4">
            <p className="text-[13px] text-text-secondary leading-relaxed">{norma.resumen_ia}</p>
          </div>
        </div>
      )}

      {norma.resumen && (
        <div className="card p-6 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <BookOpen size={14} className="text-text-tertiary" />
            <h3 className="text-sm font-semibold text-text-primary">Texto resumido</h3>
          </div>
          <p className="text-[13px] text-text-secondary leading-relaxed">{norma.resumen}</p>
          {(norma.url || norma.bora_seccion) && (
            <div className="mt-3 pt-3 border-t border-border-light">
              <a href={norma.url || '#'} target={norma.url ? '_blank' : undefined} rel="noreferrer" className="flex items-center gap-1.5 text-[12px] text-inst-accent hover:underline">
                <ExternalLink size={11} /> Ver texto completo{norma.bora_seccion ? ` en el Boletín Oficial — ${norma.bora_seccion}` : ' en InfoLEG'}
              </a>
            </div>
          )}
        </div>
      )}

      {/* Entidades (NER) — solo cuando hay (Fase 5) */}
      {norma.entidades && norma.entidades.length > 0 && (
        <div className="card p-6 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Users size={14} className="text-text-tertiary" />
            <h3 className="text-sm font-semibold text-text-primary">Entidades identificadas</h3>
            <span className="text-[9px] font-medium tint-green px-2 py-0.5 rounded-full border ml-auto">NER</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {norma.entidades.map((ent) => (
              <span key={ent} className="px-3 py-1.5 bg-bg-secondary border border-border-light rounded text-[12px] text-text-secondary font-medium">{ent}</span>
            ))}
          </div>
        </div>
      )}

      {norma.tags && norma.tags.length > 0 && (
        <div className="card p-5 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Tag size={13} className="text-text-tertiary" />
            <h3 className="text-sm font-semibold text-text-primary">Tags</h3>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {norma.tags.map((tag) => (
              <span key={tag} className="px-2.5 py-1 bg-celeste/10 text-celeste-bright border border-celeste/30 rounded-full text-[10px] font-medium">#{tag}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
