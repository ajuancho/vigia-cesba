// Template se re-monta en cada navegación → transición suave entre páginas.
export default function Template({ children }) {
  return <div className="page-transition">{children}</div>;
}
