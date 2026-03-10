import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { NORMAS_FEED, TIPOS_NORMA } from '../data/mockData';
import { Clock, ArrowRight, Filter, Tag, Building2, MapPin } from 'lucide-react';

const IMPACTO_STYLES = {
    alto: 'bg-red-50 text-status-red border-red-200',
    medio: 'bg-amber-50 text-status-amber border-amber-200',
    bajo: 'bg-gray-50 text-text-tertiary border-gray-200',
};

const TIPO_STYLES = {
    DNU: 'bg-red-50 text-red-800 border-red-200',
    DECRETO: 'bg-amber-50 text-amber-800 border-amber-200',
    LEY: 'bg-green-50 text-green-800 border-green-200',
    RESOLUCION: 'bg-blue-50 text-blue-800 border-blue-200',
    DISPOSICION: 'bg-purple-50 text-purple-800 border-purple-200',
    PROYECTO: 'bg-cyan-50 text-cyan-800 border-cyan-200',
};

const NormCard = ({ norma, onClick }) => (
    <div
        onClick={onClick}
        className="card card-hover p-5 cursor-pointer transition-all group animate-fade-in"
    >
        {/* Top row: type + impact + date */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide border ${TIPO_STYLES[norma.tipo]}`}>
                {TIPOS_NORMA[norma.tipo].label}
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${IMPACTO_STYLES[norma.impacto]}`}>
                {norma.impacto === 'alto' ? 'Alto impacto' : norma.impacto === 'medio' ? 'Impacto medio' : 'Bajo'}
            </span>
            <span className="text-[11px] text-text-tertiary ml-auto flex items-center gap-1 font-mono">
                <Clock size={10} /> {norma.fecha}
            </span>
        </div>

        {/* Title */}
        <h3 className="text-[15px] font-semibold text-text-primary mb-2 group-hover:text-inst-accent transition-colors leading-snug">
            {norma.tipo !== 'PROYECTO' && `${TIPOS_NORMA[norma.tipo].label} ${norma.numero} — `}
            {norma.titulo}
        </h3>

        {/* Summary */}
        <p className="text-[13px] text-text-secondary leading-relaxed mb-3 line-clamp-2">{norma.resumen}</p>

        {/* AI summary */}
        <div className="bg-bg-secondary border border-border-light rounded p-3 mb-3">
            <p className="text-[10px] font-semibold text-inst-blue uppercase tracking-wide mb-1">Análisis automático</p>
            <p className="text-[12px] text-text-secondary leading-relaxed line-clamp-2">{norma.resumenIA}</p>
        </div>

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-4 text-[11px] text-text-tertiary">
            <span className="flex items-center gap-1"><Building2 size={11} /> {norma.organismo}</span>
            <span className="flex items-center gap-1"><MapPin size={11} /> {norma.jurisdiccion}</span>
            <span className="flex items-center gap-1"><Tag size={11} /> {norma.sector}</span>
            <span className="ml-auto flex items-center gap-1 text-inst-accent font-medium group-hover:gap-2 transition-all">
                Ver detalle <ArrowRight size={11} />
            </span>
        </div>
    </div>
);

const FeedView = () => {
    const navigate = useNavigate();
    const [filterTipo, setFilterTipo] = useState('TODOS');
    const [filterImpacto, setFilterImpacto] = useState('todos');

    const filtered = NORMAS_FEED.filter(n => {
        if (filterTipo !== 'TODOS' && n.tipo !== filterTipo) return false;
        if (filterImpacto !== 'todos' && n.impacto !== filterImpacto) return false;
        return true;
    });

    return (
        <div className="max-w-4xl mx-auto animate-fade-in">
            <div className="mb-6">
                <h2 className="text-xl font-bold text-text-primary tracking-tight mb-0.5">Feed Normativo</h2>
                <p className="text-sm text-text-tertiary">Últimas publicaciones del Boletín Oficial y actividad del Congreso</p>
            </div>

            {/* Filters */}
            <div className="card p-3 mb-5 flex flex-wrap items-center gap-2">
                <Filter size={14} className="text-text-tertiary" />
                {['TODOS', ...Object.keys(TIPOS_NORMA)].map(tipo => (
                    <button
                        key={tipo}
                        onClick={() => setFilterTipo(tipo)}
                        className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors border ${filterTipo === tipo
                                ? 'bg-navy-800 text-white border-navy-800'
                                : 'bg-white text-text-secondary border-border-light hover:bg-bg-secondary'
                            }`}
                    >
                        {tipo === 'TODOS' ? 'Todos' : TIPOS_NORMA[tipo].label}
                    </button>
                ))}
                <select
                    value={filterImpacto}
                    onChange={e => setFilterImpacto(e.target.value)}
                    className="ml-auto bg-white border border-border-light rounded px-2.5 py-1 text-[11px] text-text-secondary focus:outline-none focus:border-inst-accent"
                >
                    <option value="todos">Todo impacto</option>
                    <option value="alto">Alto impacto</option>
                    <option value="medio">Medio</option>
                </select>
            </div>

            <p className="text-[11px] text-text-tertiary mb-3">
                <span className="font-semibold text-text-primary">{filtered.length}</span> de {NORMAS_FEED.length} normas
            </p>

            <div className="space-y-3">
                {filtered.map((norma, i) => (
                    <div key={norma.id} style={{ animationDelay: `${i * 40}ms` }}>
                        <NormCard norma={norma} onClick={() => navigate(`/norma/${norma.id}`)} />
                    </div>
                ))}
            </div>

            {filtered.length === 0 && (
                <div className="text-center py-16">
                    <p className="text-text-tertiary text-sm">No hay normas que coincidan con los filtros.</p>
                </div>
            )}
        </div>
    );
};

export default FeedView;
