// Las cuatro barras del isotipo de nuevosBAires (lima, magenta, turquesa,
// lavanda), en ese orden y con alturas desiguales. Recurso gráfico de marca:
// decorativo, nunca reemplaza un gráfico con datos.
const ORDEN = ['bg-lima', 'bg-magenta', 'bg-turquesa', 'bg-lavanda'];
const ALTURAS = [1, 0.62, 0.8, 0.42];

export default function BarrasMarca({ alto = 48, ancho, gap, alturas = ALTURAS, className = '' }) {
  const w = ancho ?? Math.max(3, Math.round(alto / 6));
  const g = gap ?? Math.max(2, Math.round(w / 2.5));
  return (
    <span aria-hidden="true" className={`inline-flex items-end ${className}`} style={{ height: alto, gap: g }}>
      {ORDEN.map((c, i) => (
        <span key={c} className={`block ${c}`} style={{ width: w, height: Math.round(alto * alturas[i]) }} />
      ))}
    </span>
  );
}
