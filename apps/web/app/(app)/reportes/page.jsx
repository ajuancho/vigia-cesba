'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSession, signIn } from 'next-auth/react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import {
  FileBarChart, Play, Save, Download, Printer, Sparkles, Trash2, Plus, X, ExternalLink, Lock,
} from 'lucide-react';
import { authedFetch, authedFetchBlob, AUTH_ENABLED } from '@/lib/authClient';
import FadeIn from '@/components/FadeIn';

const PAGE = 100;
const fmt = (n) => (n ?? 0).toLocaleString('es-AR');
const iso = (d) => d.toISOString().slice(0, 10);
const haceDias = (n) => iso(new Date(Date.now() - n * 86400000));
const fmtFecha = (s) => (s ? s.split('-').reverse().join('/') : '—');

const PERIODOS = [
  { label: '30 días', dias: 30 },
  { label: '6 meses', dias: 182 },
  { label: '1 año', dias: 365 },
  { label: 'Todo', dias: null },
];

// Puntos de partida frecuentes; el usuario los ajusta después.
const PLANTILLAS = [
  {
    nombre: 'Licitaciones de obra pública · último año',
    config: () => ({
      filtros: { secciones: ['Licitaciones'], tipos: ['Licitación Obra Pública'], desde: haceDias(365) },
      formato: 'analisis', orden: 'fecha_desc',
    }),
  },
  {
    nombre: 'Adjudicaciones · últimos 6 meses',
    config: () => ({
      filtros: { secciones: ['Licitaciones'], etapas: ['Adjudicación'], desde: haceDias(182) },
      formato: 'analisis', orden: 'organismo',
    }),
  },
  {
    nombre: 'Contrataciones directas · último año',
    config: () => ({
      filtros: { secciones: ['Licitaciones'], tipos: ['Contratación Directa'], desde: haceDias(365) },
      formato: 'listado', orden: 'fecha_desc',
    }),
  },
];

const CONFIG_VACIA = {
  filtros: { secciones: ['Licitaciones'], tipos: [], etapas: [], organismos: [], desde: haceDias(365), hasta: null, texto: '' },
  formato: 'analisis',
  orden: 'fecha_desc',
};

function normalizar(config) {
  const f = config.filtros || {};
  return {
    formato: config.formato || 'analisis',
    orden: config.orden || 'fecha_desc',
    filtros: {
      secciones: f.secciones || [], tipos: f.tipos || [], etapas: f.etapas || [],
      organismos: f.organismos || [], desde: f.desde || null, hasta: f.hasta || null, texto: f.texto || '',
    },
  };
}

function Chips({ opciones, seleccion, onToggle, max = 14 }) {
  const [todas, setTodas] = useState(false);
  const visibles = todas ? opciones : opciones.slice(0, max);
  return (
    <div className="flex flex-wrap gap-1.5">
      {visibles.map((o) => {
        const on = seleccion.includes(o.valor);
        return (
          <button
            key={o.valor}
            type="button"
            onClick={() => onToggle(o.valor)}
            aria-pressed={on}
            className={`text-[12px] px-2.5 min-h-8 rounded border transition-colors ${
              on ? 'bg-petroleo text-white border-petroleo' : 'bg-white text-text-secondary border-border-medium hover:border-cian'
            }`}
          >
            {o.valor} <span className={on ? 'text-white/80' : 'text-text-tertiary'}>· {fmt(o.cantidad)}</span>
          </button>
        );
      })}
      {opciones.length > max && (
        <button type="button" onClick={() => setTodas((v) => !v)} className="text-[12px] text-celeste font-semibold px-2 min-h-8">
          {todas ? 'ver menos' : `ver ${opciones.length - max} más`}
        </button>
      )}
    </div>
  );
}

function Campo({ label, ayuda, children }) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[11px] font-semibold tracking-[0.14em] uppercase text-petroleo">
        {label} {ayuda && <span className="normal-case tracking-normal font-normal text-text-tertiary">— {ayuda}</span>}
      </span>
      {children}
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-border-medium rounded px-3 py-2 shadow-[0_4px_14px_rgba(21,59,112,0.10)]">
      <p className="text-[11px] text-text-tertiary mb-0.5">{label}</p>
      <p className="text-[13px] font-bold text-petroleo">{fmt(payload[0].value)}</p>
    </div>
  );
}

function BarrasHorizontales({ titulo, datos }) {
  if (!datos?.length) return null;
  const max = Math.max(...datos.map((d) => d.cantidad));
  return (
    <div className="card card-accent p-5 break-inside-avoid">
      <h3 className="text-[13px] font-bold tracking-[0.06em] uppercase text-petroleo mb-4">{titulo}</h3>
      <ul className="space-y-2.5">
        {datos.map((d) => (
          <li key={d.valor} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1 items-center">
            <span className="text-[12px] text-text-secondary truncate" title={d.valor}>{d.valor}</span>
            <span className="text-[12px] font-bold text-petroleo tabular-nums">{fmt(d.cantidad)}</span>
            <span className="col-span-2 h-2 bg-humo rounded-sm overflow-hidden">
              <span className="block h-full bg-cian rounded-sm" style={{ width: `${(d.cantidad / max) * 100}%` }} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SinSesion() {
  return (
    <FadeIn>
      <div className="card card-accent max-w-xl p-8 flex flex-col gap-4">
        <Lock size={28} strokeWidth={1.75} className="text-petroleo" />
        <h3 className="text-[17px] font-bold tracking-[0.06em] uppercase text-petroleo">Disponible con sesión iniciada</h3>
        <p className="text-[14px] text-text-secondary leading-relaxed">
          Los reportes permiten compilar y analizar la información del Boletín Oficial —por ejemplo, todas las
          licitaciones de obra pública del último año— y están disponibles solo para usuarios con sesión iniciada.
        </p>
        {AUTH_ENABLED ? (
          <button onClick={() => signIn('google', { callbackUrl: '/reportes' })} className="btn-celeste w-fit min-h-11 px-5 text-[12px] font-bold">
            Iniciar sesión
          </button>
        ) : (
          <p className="text-[12px] text-text-tertiary">El inicio de sesión se activa configurando Google OAuth en el deploy.</p>
        )}
      </div>
    </FadeIn>
  );
}

export default function ReportesView() {
  const { data: session, status } = useSession();
  const jwt = session?.apiJwt;
  const connected = AUTH_ENABLED && Boolean(jwt);

  const [config, setConfig] = useState(CONFIG_VACIA);
  const [opciones, setOpciones] = useState(null);
  const [guardados, setGuardados] = useState([]);
  const [actual, setActual] = useState(null); // reporte guardado abierto {id, nombre}
  const [resultado, setResultado] = useState(null);
  const [items, setItems] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [analisis, setAnalisis] = useState('');
  const [analizando, setAnalizando] = useState(false);
  const [orgDraft, setOrgDraft] = useState('');
  const [err, setErr] = useState('');

  const f = config.filtros;
  const setFiltro = (k, v) => setConfig((c) => ({ ...c, filtros: { ...c.filtros, [k]: v } }));
  const toggle = (k) => (v) => setFiltro(k, f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v]);

  const run = useCallback(async (fn) => {
    setErr('');
    try { return await fn(); } catch (e) { setErr(String(e.message || e)); return null; }
  }, []);

  const cargarGuardados = useCallback(async () => {
    if (!connected) return;
    const r = await run(() => authedFetch(jwt, '/reportes'));
    if (r) setGuardados(r);
  }, [connected, jwt, run]);

  useEffect(() => { cargarGuardados(); }, [cargarGuardados]);

  const seccionesKey = f.secciones.join('|');
  useEffect(() => {
    if (!connected) return;
    const qs = new URLSearchParams();
    f.secciones.forEach((s) => qs.append('secciones', s));
    run(() => authedFetch(jwt, `/reportes/opciones?${qs}`)).then((o) => o && setOpciones(o));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected, jwt, seccionesKey, run]);

  const body = useMemo(() => ({
    ...config,
    filtros: { ...f, texto: f.texto?.trim() || null, desde: f.desde || null, hasta: f.hasta || null },
  }), [config, f]);

  const generar = async (cfg = body) => {
    setCargando(true);
    setAnalisis('');
    const r = await run(() => authedFetch(jwt, '/reportes/ejecutar', {
      method: 'POST', body: JSON.stringify({ config: cfg, limit: PAGE, offset: 0 }),
    }));
    if (r) { setResultado(r); setItems(r.items); }
    setCargando(false);
  };

  const cargarMas = async () => {
    const r = await run(() => authedFetch(jwt, '/reportes/ejecutar', {
      method: 'POST', body: JSON.stringify({ config: body, limit: PAGE, offset: items.length }),
    }));
    if (r) setItems((prev) => [...prev, ...r.items]);
  };

  const pedirAnalisis = async () => {
    setAnalizando(true);
    const r = await run(() => authedFetch(jwt, '/reportes/analisis', { method: 'POST', body: JSON.stringify(body) }));
    if (r) setAnalisis(r.texto);
    setAnalizando(false);
  };

  const exportar = async () => {
    const blob = await run(() => authedFetchBlob(jwt, '/reportes/csv', { method: 'POST', body: JSON.stringify(body) }));
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(actual?.nombre || 'reporte').replace(/[^\w\-áéíóúñ ]+/gi, '').trim() || 'reporte'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const guardar = async () => {
    const nombre = window.prompt('Nombre del reporte', actual?.nombre || '');
    if (!nombre?.trim()) return;
    const payload = JSON.stringify({ nombre: nombre.trim(), config: body });
    const r = await run(() => (actual && nombre.trim() === actual.nombre
      ? authedFetch(jwt, `/reportes/${actual.id}`, { method: 'PUT', body: payload })
      : authedFetch(jwt, '/reportes', { method: 'POST', body: payload })));
    if (r) { setActual({ id: r.id, nombre: r.nombre }); cargarGuardados(); }
  };

  const abrir = (cfg, meta = null) => {
    const c = normalizar(cfg);
    setConfig(c);
    setActual(meta);
    generar({ ...c, filtros: { ...c.filtros, texto: c.filtros.texto || null } });
  };

  const borrar = async (g) => {
    if (!window.confirm(`¿Borrar el reporte "${g.nombre}"?`)) return;
    await run(() => authedFetch(jwt, `/reportes/${g.id}`, { method: 'DELETE' }));
    if (actual?.id === g.id) setActual(null);
    cargarGuardados();
  };

  const addOrganismo = (v) => {
    const o = v.trim();
    if (o && !f.organismos.includes(o)) setFiltro('organismos', [...f.organismos, o]);
    setOrgDraft('');
  };

  const periodoActivo = PERIODOS.find((p) => (p.dias === null ? !f.desde : f.desde === haceDias(p.dias)) && !f.hasta);
  const ag = resultado?.agregados;
  const porMes = (ag?.por_mes || []).map((m) => ({ mes: m.valor.split('-').reverse().join('/'), cantidad: m.cantidad }));

  return (
    <div className="max-w-6xl mx-auto">
      <FadeIn>
        <div className="mb-8 pt-2 print:mb-4">
          <p className="eyebrow mb-1 print:hidden"><span className="eyebrow-num">BOCBA / REPORTES</span><span className="ml-2">Compilación y análisis</span></p>
          <div className="title-rule flex flex-col gap-1">
            <h2 className="display-section text-text-primary">{actual?.nombre || <>Reportes <em>a medida</em></>}</h2>
            <p className="text-[15px] text-text-tertiary">compilá, ordená y analizá lo publicado en el boletín oficial de la ciudad</p>
          </div>
        </div>
      </FadeIn>

      {status === 'loading' ? null : !connected ? <SinSesion /> : (
        <>
          {/* Plantillas y guardados */}
          <FadeIn delay={60}>
            <div className="flex flex-col gap-3 mb-6 print:hidden">
              <div className="flex flex-wrap items-center gap-2">
                <span className="eyebrow mr-1">Empezar desde</span>
                {PLANTILLAS.map((p) => (
                  <button key={p.nombre} type="button" onClick={() => abrir(p.config())}
                    className="text-[12px] px-3 min-h-9 rounded border border-border-medium bg-white text-petroleo font-medium hover:border-cian transition-colors">
                    {p.nombre}
                  </button>
                ))}
                <button type="button" onClick={() => { setConfig(CONFIG_VACIA); setActual(null); setResultado(null); setItems([]); setAnalisis(''); }}
                  className="text-[12px] px-3 min-h-9 rounded text-celeste font-semibold inline-flex items-center gap-1.5">
                  <Plus size={14} /> Nuevo
                </button>
              </div>
              {guardados.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="eyebrow mr-1">Guardados</span>
                  {guardados.map((g) => (
                    <span key={g.id} className={`inline-flex items-center rounded border text-[12px] ${actual?.id === g.id ? 'border-petroleo bg-petroleo text-white' : 'border-border-medium bg-white text-text-secondary'}`}>
                      <button type="button" onClick={() => abrir(g.config, { id: g.id, nombre: g.nombre })} className="px-3 min-h-9">{g.nombre}</button>
                      <button type="button" onClick={() => borrar(g)} aria-label={`Borrar ${g.nombre}`} className="px-2 min-h-9 opacity-70 hover:opacity-100">
                        <Trash2 size={13} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </FadeIn>

          {/* Constructor */}
          <FadeIn delay={100}>
            <section className="card card-accent p-5 md:p-6 mb-8 flex flex-col gap-6 print:hidden" aria-label="Configuración del reporte">
              <Campo label="Sección del boletín">
                <Chips opciones={opciones?.secciones || []} seleccion={f.secciones} onToggle={toggle('secciones')} />
              </Campo>
              <Campo label="Tipo" ayuda="procedimiento o tipo de norma; vacío = todos">
                <Chips opciones={opciones?.tipos || []} seleccion={f.tipos} onToggle={toggle('tipos')} />
              </Campo>
              {(opciones?.etapas?.length ?? 0) > 0 && (
                <Campo label="Etapa" ayuda="llamado, preadjudicación, adjudicación…">
                  <Chips opciones={opciones.etapas} seleccion={f.etapas} onToggle={toggle('etapas')} />
                </Campo>
              )}
              <Campo label="Organismos" ayuda="vacío = todos">
                <div className="flex flex-wrap items-center gap-1.5">
                  {f.organismos.map((o) => (
                    <span key={o} className="inline-flex items-center gap-1 text-[12px] px-2.5 min-h-8 rounded bg-petroleo text-white">
                      {o}
                      <button type="button" onClick={() => setFiltro('organismos', f.organismos.filter((x) => x !== o))} aria-label={`Quitar ${o}`}><X size={12} /></button>
                    </span>
                  ))}
                  <label className="flex-1 min-w-[220px]">
                    <span className="sr-only">Agregar organismo</span>
                    <input list="reportes-organismos" value={orgDraft} onChange={(e) => setOrgDraft(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addOrganismo(orgDraft); } }}
                      onBlur={() => orgDraft && addOrganismo(orgDraft)}
                      placeholder="Escribí y elegí un organismo"
                      className="w-full h-10 px-3 rounded border border-border-medium bg-white text-[13px] focus:outline-none focus:border-cian" />
                    <datalist id="reportes-organismos">
                      {(opciones?.organismos || []).map((o) => <option key={o.valor} value={o.valor}>{fmt(o.cantidad)}</option>)}
                    </datalist>
                  </label>
                </div>
              </Campo>
              <div className="grid grid-cols-1 xl:grid-cols-[3fr_2fr] gap-6">
                <Campo label="Período">
                  <div className="flex flex-wrap items-center gap-2">
                    {PERIODOS.map((p) => (
                      <button key={p.label} type="button" onClick={() => setConfig((c) => ({ ...c, filtros: { ...c.filtros, desde: p.dias ? haceDias(p.dias) : null, hasta: null } }))}
                        aria-pressed={periodoActivo === p}
                        className={`text-[12px] px-3 min-h-9 rounded border ${periodoActivo === p ? 'bg-petroleo text-white border-petroleo' : 'bg-white border-border-medium text-text-secondary hover:border-cian'}`}>
                        {p.label}
                      </button>
                    ))}
                    <label className="flex items-center gap-1.5 text-[12px] text-text-tertiary">desde
                      <input type="date" value={f.desde || ''} onChange={(e) => setFiltro('desde', e.target.value || null)} className="h-9 px-2 rounded border border-border-medium bg-white text-[12px] text-text-secondary" />
                    </label>
                    <label className="flex items-center gap-1.5 text-[12px] text-text-tertiary">hasta
                      <input type="date" value={f.hasta || ''} onChange={(e) => setFiltro('hasta', e.target.value || null)} className="h-9 px-2 rounded border border-border-medium bg-white text-[12px] text-text-secondary" />
                    </label>
                  </div>
                </Campo>
                <Campo label="Texto" ayuda="palabras en el título u objeto">
                  <input value={f.texto} onChange={(e) => setFiltro('texto', e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') generar(); }}
                    placeholder='p. ej. "hospital" o pavimentación -bacheo'
                    className="h-10 px-3 rounded border border-border-medium bg-white text-[13px] focus:outline-none focus:border-cian" />
                </Campo>
              </div>
              <div className="flex flex-wrap items-end justify-between gap-4 pt-4 border-t border-border-light">
                <div className="flex flex-wrap gap-6">
                  <Campo label="Formato">
                    <div className="flex rounded border border-border-medium overflow-hidden w-fit" role="group">
                      {[['analisis', 'Análisis con gráficos'], ['listado', 'Listado']].map(([v, l]) => (
                        <button key={v} type="button" onClick={() => setConfig((c) => ({ ...c, formato: v }))} aria-pressed={config.formato === v}
                          className={`text-[12px] px-3 min-h-9 ${config.formato === v ? 'bg-petroleo text-white' : 'bg-white text-text-secondary'}`}>{l}</button>
                      ))}
                    </div>
                  </Campo>
                  <Campo label="Orden">
                    <select value={config.orden} onChange={(e) => setConfig((c) => ({ ...c, orden: e.target.value }))}
                      className="h-9 px-2 rounded border border-border-medium bg-white text-[12px] text-text-secondary">
                      <option value="fecha_desc">Más recientes primero</option>
                      <option value="fecha_asc">Más antiguas primero</option>
                      <option value="organismo">Por organismo</option>
                      <option value="tipo">Por tipo</option>
                    </select>
                  </Campo>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => generar()} disabled={cargando}
                    className="btn-celeste inline-flex items-center gap-2 min-h-11 px-5 text-[12px] font-bold disabled:opacity-50">
                    <Play size={15} /> {cargando ? 'Generando…' : 'Generar reporte'}
                  </button>
                  <button type="button" onClick={guardar}
                    className="inline-flex items-center gap-2 min-h-11 px-4 rounded border border-petroleo text-petroleo text-[12px] font-semibold uppercase tracking-[0.06em] hover:bg-humo">
                    <Save size={15} /> Guardar
                  </button>
                </div>
              </div>
            </section>
          </FadeIn>

          {err && <p className="text-[13px] text-status-red mb-4">{err}</p>}

          {/* Resultado */}
          {resultado && (
            <section className="flex flex-col gap-6" aria-label="Resultado del reporte">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
                  <div><p className="text-[38px] font-bold leading-none text-petroleo tabular-nums">{fmt(resultado.total)}</p><p className="eyebrow mt-1.5">publicaciones</p></div>
                  <div><p className="text-[38px] font-bold leading-none text-petroleo tabular-nums">{fmt(ag.organismos_distintos)}</p><p className="eyebrow mt-1.5">organismos</p></div>
                  <div><p className="text-[17px] font-bold text-petroleo mt-3">{fmtFecha(ag.desde)} — {fmtFecha(ag.hasta)}</p><p className="eyebrow mt-1.5">período con datos</p></div>
                </div>
                <div className="flex flex-wrap gap-2 print:hidden">
                  <button type="button" onClick={exportar} className="inline-flex items-center gap-2 min-h-10 px-3 rounded border border-border-medium bg-white text-[12px] text-petroleo font-semibold hover:border-cian">
                    <Download size={15} /> CSV
                  </button>
                  <button type="button" onClick={() => window.print()} className="inline-flex items-center gap-2 min-h-10 px-3 rounded border border-border-medium bg-white text-[12px] text-petroleo font-semibold hover:border-cian">
                    <Printer size={15} /> Imprimir / PDF
                  </button>
                </div>
              </div>

              {resultado.total === 0 && <p className="text-[14px] text-text-tertiary">No hay publicaciones con estos filtros.</p>}

              {config.formato === 'analisis' && resultado.total > 0 && (
                <>
                  <div className="card card-accent p-5 break-inside-avoid">
                    <h3 className="text-[13px] font-bold tracking-[0.06em] uppercase text-petroleo mb-4">Publicaciones por mes</h3>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={porMes} margin={{ top: 4, right: 8, bottom: 0, left: -12 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E4EBED" vertical={false} />
                        <XAxis dataKey="mes" tick={{ fill: '#5B6267', fontSize: 11 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                        <YAxis tick={{ fill: '#5B6267', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(24, 166, 194, 0.08)' }} />
                        <Bar dataKey="cantidad" fill="#18A6C2" radius={[2, 2, 0, 0]} isAnimationActive={false} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <BarrasHorizontales titulo="Organismos con más publicaciones" datos={ag.por_organismo} />
                    <div className="flex flex-col gap-6">
                      <BarrasHorizontales titulo="Por tipo" datos={ag.por_tipo.slice(0, 8)} />
                      <BarrasHorizontales titulo="Por etapa" datos={ag.por_etapa} />
                    </div>
                  </div>

                  <div className="card p-5 md:p-6 break-inside-avoid">
                    <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                      <h3 className="text-[13px] font-bold tracking-[0.06em] uppercase text-petroleo inline-flex items-center gap-2">
                        <Sparkles size={16} strokeWidth={1.75} /> Análisis
                      </h3>
                      <button type="button" onClick={pedirAnalisis} disabled={analizando}
                        className="print:hidden inline-flex items-center gap-2 min-h-10 px-3 rounded border border-petroleo text-petroleo text-[12px] font-semibold disabled:opacity-50 hover:bg-humo">
                        {analizando ? 'Analizando…' : analisis ? 'Regenerar' : 'Generar análisis con IA'}
                      </button>
                    </div>
                    {analisis ? (
                      <div className="space-y-3 text-[14px] leading-relaxed text-text-secondary max-w-3xl">
                        {analisis.split(/\n+/).filter(Boolean).map((p, i) => <p key={i}>{p}</p>)}
                        <p className="text-[11px] text-text-tertiary pt-1">Texto generado con IA a partir de las cifras del reporte. Verificá los datos antes de citarlos.</p>
                      </div>
                    ) : (
                      <p className="text-[13px] text-text-tertiary">Un resumen escrito de las cifras del reporte: volumen, evolución, organismos y temas recurrentes.</p>
                    )}
                  </div>
                </>
              )}

              {resultado.total > 0 && (
                <div className="card overflow-hidden">
                  <div className="px-5 py-3 border-b border-border-light flex items-center justify-between">
                    <h3 className="text-[13px] font-bold tracking-[0.06em] uppercase text-petroleo inline-flex items-center gap-2">
                      <FileBarChart size={16} strokeWidth={1.75} /> Listado
                    </h3>
                    <span className="text-[12px] text-text-tertiary">{fmt(items.length)} de {fmt(resultado.total)}</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[13px]">
                      <thead className="bg-humo text-[11px] uppercase tracking-[0.06em] text-petroleo">
                        <tr>
                          <th scope="col" className="px-4 py-2.5 font-semibold whitespace-nowrap">Fecha</th>
                          <th scope="col" className="px-4 py-2.5 font-semibold">Tipo · etapa</th>
                          <th scope="col" className="px-4 py-2.5 font-semibold">Objeto</th>
                          <th scope="col" className="px-4 py-2.5 font-semibold">Organismo</th>
                          <th scope="col" className="px-4 py-2.5 font-semibold print:hidden"><span className="sr-only">Fuente</span></th>
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((it) => (
                          <tr key={it.id} className="border-t border-border-light align-top break-inside-avoid">
                            <td className="px-4 py-3 whitespace-nowrap tabular-nums text-text-tertiary">{fmtFecha(it.fecha)}</td>
                            <td className="px-4 py-3 min-w-[160px]">
                              <span className="block text-text-secondary">{it.tipo}</span>
                              {it.etapa && <span className="block text-[12px] text-text-tertiary">{it.etapa}{it.numero ? ` · N° ${it.numero}` : ''}</span>}
                            </td>
                            <td className="px-4 py-3 min-w-[260px] text-petroleo font-medium">{it.objeto || it.titulo}</td>
                            <td className="px-4 py-3 min-w-[180px] text-text-secondary">{it.organismo}</td>
                            <td className="px-4 py-3 print:hidden">
                              {it.url && (
                                <a href={it.url} target="_blank" rel="noopener noreferrer" aria-label="Ver publicación oficial" className="text-celeste hover:text-petroleo">
                                  <ExternalLink size={15} />
                                </a>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {items.length < resultado.total && (
                    <div className="px-5 py-3 border-t border-border-light print:hidden">
                      <button type="button" onClick={cargarMas} className="text-[12px] font-semibold uppercase tracking-[0.06em] text-celeste hover:text-petroleo min-h-9">
                        Cargar {fmt(Math.min(PAGE, resultado.total - items.length))} más
                      </button>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
