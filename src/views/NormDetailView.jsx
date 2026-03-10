import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { NORMAS_FEED, TIPOS_NORMA } from '../data/mockData';
import {
    ArrowLeft, Clock, Building2, MapPin, Tag, FileText,
    Users, ExternalLink, BookOpen, CheckCircle, Timer, AlertTriangle
} from 'lucide-react';

const TIPO_BADGE = {
    DNU: 'bg-red-50 text-red-800 border-red-200',
    DECRETO: 'bg-amber-50 text-amber-800 border-amber-200',
    LEY: 'bg-green-50 text-green-800 border-green-200',
    RESOLUCION: 'bg-blue-50 text-blue-800 border-blue-200',
    DISPOSICION: 'bg-purple-50 text-purple-800 border-purple-200',
    PROYECTO: 'bg-cyan-50 text-cyan-800 border-cyan-200',
};

const NormDetailView = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const norma = NORMAS_FEED.find(n => n.id === id);

    if (!norma) {
        return (
            <div className="max-w-3xl mx-auto text-center py-20">
                <p className="text-text-tertiary">Norma no encontrada</p>
                <button onClick={() => navigate('/feed')} className="text-inst-accent text-sm mt-3 hover:underline">Volver al feed</button>
            </div>
        );
    }

    const estadoStyle = norma.estado.includes('Vigente')
        ? 'bg-green-50 text-green-800 border-green-200'
        : norma.estado.includes('comisión')
            ? 'bg-amber-50 text-amber-800 border-amber-200'
            : 'bg-blue-50 text-blue-800 border-blue-200';

    return (
        <div className="max-w-3xl mx-auto animate-fade-in">
            <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-text-tertiary hover:text-text-primary text-[13px] mb-5 transition-colors">
                <ArrowLeft size={14} /> Volver
            </button>

            {/* Header Card */}
            <div className="card p-6 mb-4">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                    <span className={`px-2.5 py-1 rounded text-[10px] font-semibold uppercase tracking-wide border ${TIPO_BADGE[norma.tipo]}`}>
                        {TIPOS_NORMA[norma.tipo].label} {norma.numero}
                    </span>
                    <span className={`px-2.5 py-1 rounded text-[10px] font-medium border ${estadoStyle}`}>
                        {norma.estado}
                    </span>
                </div>

                <h1 className="text-lg font-bold text-text-primary leading-snug mb-5">{norma.titulo}</h1>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-border-light">
                    {[
                        { icon: Clock, label: 'Publicación', value: norma.fecha },
                        { icon: Building2, label: 'Organismo', value: norma.organismo },
                        { icon: MapPin, label: 'Jurisdicción', value: norma.jurisdiccion },
                        { icon: Tag, label: 'Sector', value: norma.sector },
                    ].map(({ icon: Icon, label, value }) => (
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

            {/* AI Analysis */}
            <div className="card p-6 mb-4">
                <div className="flex items-center gap-2 mb-3">
                    <FileText size={14} className="text-inst-blue" />
                    <h3 className="text-sm font-semibold text-text-primary">Análisis automático</h3>
                    <span className="text-[9px] font-medium text-inst-blue bg-blue-50 px-2 py-0.5 rounded border border-blue-200 ml-auto">Vigía AI</span>
                </div>
                <div className="bg-bg-secondary border border-border-light rounded p-4">
                    <p className="text-[13px] text-text-secondary leading-relaxed">{norma.resumenIA}</p>
                </div>
            </div>

            {/* Full Text */}
            <div className="card p-6 mb-4">
                <div className="flex items-center gap-2 mb-3">
                    <BookOpen size={14} className="text-text-tertiary" />
                    <h3 className="text-sm font-semibold text-text-primary">Texto resumido</h3>
                </div>
                <p className="text-[13px] text-text-secondary leading-relaxed">{norma.resumen}</p>
                {norma.boraSeccion && (
                    <div className="mt-3 pt-3 border-t border-border-light">
                        <a href="#" className="flex items-center gap-1.5 text-[12px] text-inst-accent hover:underline">
                            <ExternalLink size={11} /> Ver texto completo en el Boletín Oficial — {norma.boraSeccion}
                        </a>
                    </div>
                )}
            </div>

            {/* Entities */}
            <div className="card p-6 mb-4">
                <div className="flex items-center gap-2 mb-3">
                    <Users size={14} className="text-text-tertiary" />
                    <h3 className="text-sm font-semibold text-text-primary">Entidades identificadas</h3>
                    <span className="text-[9px] font-medium text-status-green bg-green-50 px-2 py-0.5 rounded border border-green-200 ml-auto">NER</span>
                </div>
                <div className="flex flex-wrap gap-2">
                    {norma.entidades.map(ent => (
                        <span key={ent} className="px-3 py-1.5 bg-bg-secondary border border-border-light rounded text-[12px] text-text-secondary font-medium">{ent}</span>
                    ))}
                </div>
            </div>

            {/* Tags */}
            <div className="card p-5 mb-4">
                <div className="flex items-center gap-2 mb-3">
                    <Tag size={13} className="text-text-tertiary" />
                    <h3 className="text-sm font-semibold text-text-primary">Tags</h3>
                </div>
                <div className="flex flex-wrap gap-1.5">
                    {norma.tags.map(tag => (
                        <span key={tag} className="px-2.5 py-1 bg-navy-800 text-white rounded text-[10px] font-medium">#{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default NormDetailView;
