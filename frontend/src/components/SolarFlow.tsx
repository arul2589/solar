// Simple original illustrations for the "how solar works" flow.
const line = { stroke: "#0f5132", strokeWidth: 2.5, strokeLinecap: "round", strokeLinejoin: "round" } as const;
const stroke = { fill: "none", ...line } as const;

function Sun() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="11" fill="#f2a900" stroke="#c98a00" strokeWidth="2" />
      {Array.from({ length: 8 }).map((_, i) => {
        const a = (i * Math.PI) / 4;
        return <line key={i} x1={32 + Math.cos(a) * 17} y1={32 + Math.sin(a) * 17} x2={32 + Math.cos(a) * 25} y2={32 + Math.sin(a) * 25} stroke="#c98a00" strokeWidth="3" strokeLinecap="round" />;
      })}
    </svg>
  );
}
function Panel() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M14 14h40l-8 30H6z" fill="#175cd3" stroke="#0f5132" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M12 24h40M9 34h40M24 14l-6 30M38 14l-4 30" stroke="#dbeafe" strokeWidth="1.5" />
      <path d="M26 44v10M18 54h16" {...stroke} />
    </svg>
  );
}
function Inverter() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <rect x="12" y="8" width="40" height="48" rx="6" fill="#ecfdf3" {...line} />
      <path d="M20 26c3-6 6-6 8 0s5 6 8 0" {...stroke} />
      <path d="M20 40h24M20 47h14" {...stroke} />
    </svg>
  );
}
function House() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M8 30 32 10l24 20" {...stroke} />
      <path d="M14 27v26h36V27" fill="#ecfdf3" {...line} />
      <rect x="27" y="38" width="10" height="15" fill="#f2a900" stroke="#0f5132" strokeWidth="2" />
      <path d="M22 18l10-8 10 8" stroke="#175cd3" strokeWidth="3" strokeLinecap="round" fill="none" />
    </svg>
  );
}
function Grid() {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true">
      <path d="M32 6v52M20 58h24M22 18h20M18 28h28M24 38h16" {...stroke} />
      <path d="M32 6 20 28M32 6l12 22M20 28l12 10 12-10" {...stroke} />
      <rect x="6" y="40" width="14" height="14" rx="2" fill="#fff" stroke="#0f5132" strokeWidth="2" />
      <path d="M9 47h8M13 43v8" stroke="#f2a900" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

const icons = [Sun, Panel, Inverter, House, Grid];

export default function SolarFlow({ steps }: { steps: { title: string; text: string }[] }) {
  return (
    <ol className="flow">
      {steps.map((s, i) => {
        const Icon = icons[i] ?? Sun;
        return (
          <li key={i}>
            <div className="flow-icon"><Icon /></div>
            <div className="flow-title">{s.title}</div>
            <div className="flow-text">{s.text}</div>
          </li>
        );
      })}
    </ol>
  );
}
