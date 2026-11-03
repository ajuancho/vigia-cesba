'use client';

import { useState } from 'react';
import { CalendarClock, Send, Pencil, Trash2 } from 'lucide-react';
import { authedFetch } from '@/lib/authClient';

const DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
const HORAS = Array.from({ length: 24 }, (_, h) => h);
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const fmtFechaHora = (iso) => (iso
  ? new Date(iso).toLocaleString('es-AR', {
    timeZone: 'America/Argentina/Buenos_Aires', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }) + ' hs'
  : '—');

export function describirProgramacion(p) {
  const hora = `${String(p.hora).padStart(2, '0')}:00 hs`;
  const cuando = p.frecuencia === 'diaria'
    ? `todos los días a las ${hora}`
    : p.frecuencia === 'mensual'
      ? `el día ${p.dia_mes} de cada mes a las ${hora}`
      : `los ${DIAS[p.dia_semana]} a las ${hora}`;
  const que = p.periodo === 'ventana' ? `lo publicado en los últimos ${p.dias} días` : 'solo lo nuevo desde el envío anterior';
  return `${cuando} · ${que}`;
}

const SELECT_CLS = 'h-9 px-2 rounded border border-border-medium bg-white text-[12px] text-text-secondary';

function Formulario({ inicial, onGuardar, onCancelar, guardando }) {
  const [p, setP] = useState(inicial);
  const [destDraft, setDestDraft] = useState(inicial.destinatarios.join(', '));
  const set = (k, v) => setP((x) => ({ ...x, [k]: v }));
  const destinatarios = destDraft.split(/[\s,;]+/).map((s) => s.trim()).filter(Boolean);
  const invalidos = destinatarios.filter((d) => !EMAIL_RE.test(d));
  const valido = destinatarios.length > 0 && destinatarios.length <= 10 && invalidos.length === 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">Frecuencia</span>
          <div className="flex rounded border border-border-medium overflow-hidden w-fit" role="group">
            {[['diaria', 'Diaria'], ['semanal', 'Semanal'], ['mensual', 'Mensual']].map(([v, l]) => (
              <button key={v} type="button" onClick={() => set('frecuencia', v)} aria-pressed={p.frecuencia === v}
                className={`text-[12px] px-3 min-h-9 ${p.frecuencia === v ? 'bg-petroleo text-white' : 'bg-white text-text-secondary'}`}>{l}</button>
            ))}
          </div>
        </div>
        {p.frecuencia === 'semanal' && (
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">Día</span>
            <select value={p.dia_semana} onChange={(e) => set('dia_semana', Number(e.target.value))} className={SELECT_CLS}>
              {DIAS.map((d, i) => <option key={d} value={i}>{d}</option>)}
            </select>
          </label>
        )}
        {p.frecuencia === 'mensual' && (
          <label className="flex flex-col gap-1.5">
            <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">Día del mes</span>
            <select value={p.dia_mes} onChange={(e) => set('dia_mes', Number(e.target.value))} className={SELECT_CLS}>
              {Array.from({ length: 28 }, (_, i) => i + 1).map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>
        )}
        <label className="flex flex-col gap-1.5">
          <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">Hora</span>
          <select value={p.hora} onChange={(e) => set('hora', Number(e.target.value))} className={SELECT_CLS}>
            {HORAS.map((h) => <option key={h} value={h}>{String(h).padStart(2, '0')}:00</option>)}
          </select>
        </label>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo mb-1.5">Qué incluye cada envío</legend>
        <label className="flex items-center gap-2 text-[13px] text-text-secondary">
          <input type="radio" name="periodo" checked={p.periodo === 'nuevo'} onChange={() => set('periodo', 'nuevo')} className="accent-cian" />
          Solo lo nuevo desde el envío anterior
        </label>
        <label className="flex flex-wrap items-center gap-2 text-[13px] text-text-secondary">
          <input type="radio" name="periodo" checked={p.periodo === 'ventana'} onChange={() => set('periodo', 'ventana')} className="accent-cian" />
          Lo publicado en los últimos
          <input type="number" min={1} max={366} value={p.dias} disabled={p.periodo !== 'ventana'}
            onChange={(e) => set('dias', Math.max(1, Math.min(366, Number(e.target.value) || 1)))}
            aria-label="Cantidad de días" className="w-20 h-9 px-2 rounded border border-border-medium bg-white text-[12px] disabled:opacity-50" />
          días
        </label>
        <p className="text-[12px] text-text-tertiary">Los demás filtros del reporte (sección, tipo, etapa, organismos, palabras clave) se mantienen.</p>
      </fieldset>

      <label className="flex flex-col gap-1.5">
        <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">
          Destinatarios <span className="normal-case tracking-normal font-normal text-text-tertiary">— hasta 10, separados por coma</span>
        </span>
        <input value={destDraft} onChange={(e) => setDestDraft(e.target.value)}
          placeholder="nombre@cesba.gob.ar, otra@cesba.gob.ar"
          className="h-10 px-3 rounded border border-border-medium bg-white text-[13px] focus:outline-none focus:border-cian" />
        {invalidos.length > 0 && <span className="text-[12px] text-status-red">No parecen correos válidos: {invalidos.join(', ')}</span>}
        {destinatarios.length > 10 && <span className="text-[12px] text-status-red">Máximo 10 destinatarios.</span>}
      </label>

      <div className="flex flex-col gap-2">
        <label className="flex items-center gap-2 text-[13px] text-text-secondary">
          <input type="checkbox" checked={p.solo_si_hay} onChange={(e) => set('solo_si_hay', e.target.checked)} className="accent-cian w-4 h-4" />
          No enviar si no hay publicaciones
        </label>
        <label className="flex items-center gap-2 text-[13px] text-text-secondary">
          <input type="checkbox" checked={p.incluir_ia} onChange={(e) => set('incluir_ia', e.target.checked)} className="accent-cian w-4 h-4" />
          Incluir análisis escrito con IA
        </label>
        <label className="flex items-center gap-2 text-[13px] text-text-secondary">
          <input type="checkbox" checked={p.activa} onChange={(e) => set('activa', e.target.checked)} className="accent-cian w-4 h-4" />
          Programación activa
        </label>
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={!valido || guardando} onClick={() => onGuardar({ ...p, destinatarios })}
          className="btn-celeste inline-flex items-center gap-2 min-h-10 px-4 text-[12px] font-bold disabled:opacity-50">
          <CalendarClock size={15} /> {guardando ? 'Guardando…' : 'Guardar programación'}
        </button>
        <button type="button" onClick={onCancelar} className="min-h-10 px-3 text-[12px] text-text-secondary hover:text-petroleo">Cancelar</button>
      </div>
    </div>
  );
}

/**
 * Programación de envío por email de un reporte guardado. `reporte` es el
 * objeto de GET /reportes (con programacion, proximo_envio, ultimo_*).
 */
export default function ProgramacionReporte({ reporte, jwt, emailDefault, onCambio, mensajeError }) {
  const [editando, setEditando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [err, setErr] = useState('');
  const [aviso, setAviso] = useState('');
  const prog = reporte.programacion;

  const llamar = async (fn, okMsg = '') => {
    setGuardando(true);
    setErr('');
    setAviso('');
    try {
      const r = await fn();
      onCambio(r);
      setEditando(false);
      setAviso(okMsg);
    } catch (e) {
      setErr(mensajeError(e));
    }
    setGuardando(false);
  };

  const guardar = (p) => llamar(() => authedFetch(jwt, `/reportes/${reporte.id}/programacion`, { method: 'PUT', body: JSON.stringify(p) }));
  const quitar = () => {
    if (!window.confirm('¿Quitar el envío programado de este reporte?')) return;
    llamar(() => authedFetch(jwt, `/reportes/${reporte.id}/programacion`, { method: 'DELETE' }));
  };
  const enviarAhora = () => llamar(
    () => authedFetch(jwt, `/reportes/${reporte.id}/enviar-ahora`, { method: 'POST' }),
    'Listo: se envía en los próximos 15 minutos.',
  );

  const inicial = prog || {
    activa: true, frecuencia: 'semanal', hora: 8, dia_semana: 0, dia_mes: 1,
    periodo: 'nuevo', dias: 7, destinatarios: emailDefault ? [emailDefault] : [], solo_si_hay: true, incluir_ia: false,
  };

  return (
    <div className="border-t border-border-light pt-4 flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="inline-flex items-center gap-2 text-[12px] font-bold tracking-[0.06em] uppercase text-petroleo">
          <CalendarClock size={16} strokeWidth={1.75} /> Envío programado por email
        </h3>
        {!editando && (
          <div className="flex flex-wrap gap-2">
            {prog && (
              <button type="button" onClick={enviarAhora} disabled={guardando}
                className="inline-flex items-center gap-1.5 min-h-9 px-3 rounded border border-border-medium bg-white text-[12px] text-petroleo font-semibold hover:border-cian disabled:opacity-50">
                <Send size={14} /> Enviar ahora
              </button>
            )}
            <button type="button" onClick={() => setEditando(true)}
              className="inline-flex items-center gap-1.5 min-h-9 px-3 rounded border border-petroleo text-[12px] text-petroleo font-semibold hover:bg-humo">
              <Pencil size={14} /> {prog ? 'Editar' : 'Programar'}
            </button>
            {prog && (
              <button type="button" onClick={quitar} disabled={guardando} aria-label="Quitar programación"
                className="inline-flex items-center min-h-9 px-2 text-text-tertiary hover:text-status-red disabled:opacity-50">
                <Trash2 size={15} />
              </button>
            )}
          </div>
        )}
      </div>

      {editando ? (
        <Formulario inicial={inicial} guardando={guardando} onGuardar={guardar} onCancelar={() => setEditando(false)} />
      ) : prog ? (
        <div className="text-[13px] text-text-secondary flex flex-col gap-1">
          <p>
            {!prog.activa && <span className="tint-gray border rounded px-1.5 py-0.5 text-[11px] font-semibold mr-2">pausado</span>}
            Se envía {describirProgramacion(prog)} a {prog.destinatarios.join(', ')}.
          </p>
          <p className="text-[12px] text-text-tertiary">
            Próximo envío: {prog.activa ? fmtFechaHora(reporte.proximo_envio) : '—'}
            {reporte.ultimo_envio && <> · Último: {fmtFechaHora(reporte.ultimo_envio)} ({reporte.ultimo_estado})</>}
          </p>
        </div>
      ) : (
        <p className="text-[13px] text-text-tertiary">Recibí este reporte por email con la frecuencia que elijas: resumen, primeras filas y el CSV adjunto.</p>
      )}
      {aviso && <p role="status" className="text-[12px] text-petroleo">{aviso}</p>}
      {err && <p role="alert" className="text-[13px] text-status-red">{err}</p>}
    </div>
  );
}
