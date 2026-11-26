// Small original line icons for the public site (24x24, currentColor stroke).
import type { CSSProperties } from "react";

const P: Record<string, string> = {
  sun: "M12 4V2M12 22v-2M4 12H2M22 12h-2M5.6 5.6 4.2 4.2M19.8 19.8l-1.4-1.4M5.6 18.4l-1.4 1.4M19.8 4.2l-1.4 1.4M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  home: "M3 11 12 4l9 7M5 10v10h5v-6h4v6h5V10",
  building: "M4 21V5l8-3v19M12 8l8 3v10M7 8h2M7 12h2M7 16h2M15 13h2M15 17h2M2 21h20",
  factory: "M2 21V10l6 4v-4l6 4V6h3l1-3h2l1 3v15zM6 17h2M11 17h2M16 17h2",
  battery: "M7 6h10a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM10 3h4v3h-4zM13 10l-3 4h4l-3 4",
  panel: "M4 5h16l-2 10H2zM3 10h16M8 5 7 15M14 5l-1 10M9 15v4M6 19h7",
  inverter: "M5 3h14v18H5zM8 7h8v5H8zM9 16h1M14 16h1M8 9.5c1-1.5 2-1.5 3 0s2 1.5 3 0",
  meter: "M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18zM12 12l4-3M8 16h8",
  shield: "M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10zM8.5 12l2.5 2.5 4.5-5",
  wrench: "M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.4-.6-.6-2.4z",
  clipboard: "M9 3h6v3H9zM7 5H5v16h14V5h-2M8 11h8M8 15h6",
  ruler: "M3 17 17 3l4 4L7 21zM7 13l2 2M10 10l2 2M13 7l2 2",
  check: "M20 6 9 17l-5-5",
  phone: "M5 3h4l2 5-3 2a12 12 0 0 0 6 6l2-3 5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z",
  chart: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  leaf: "M5 21c0-9 5-15 16-16-1 11-7 16-16 16zM5 21l8-8",
  bolt: "M13 2 4 14h7l-1 8 9-12h-7z",
  rupee: "M6 4h12M6 9h12M9 4c6 0 6 10 0 10H6l8 7",
  plug: "M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5",
  doc: "M6 2h9l5 5v15H6zM14 2v6h6M9 13h8M9 17h6",
  camera: "M4 7h4l2-3h4l2 3h4v13H4zM12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  calc: "M5 2h14v20H5zM8 5h8v4H8zM8 13h1M12 13h1M16 13h0M8 17h1M12 17h1M15 13v5",
  wifi: "M2 9a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M12 20h0",
  grid: "M12 2 7 22M12 2l5 20M8 8h8M6.5 14h11M3 22h18M12 2v4",
  arrow: "M5 12h14M13 6l6 6-6 6",
  chevron: "M6 9l6 6 6-6",
  menu: "M3 6h18M3 12h18M3 18h18",
  close: "M6 6l12 12M18 6 6 18",
  pin: "M12 22s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  users: "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M16 3.5a4 4 0 0 1 0 7.5M22 21a7 7 0 0 0-4.5-6.5",
  clock: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2",
  spark: "M12 2v6M12 16v6M2 12h6M16 12h6",
};

export type IconName = keyof typeof P;

export default function Icon({ name, size = 24, style, className }: { name: string; size?: number; style?: CSSProperties; className?: string }) {
  const d = P[name] ?? P.sun;
  return (
    <svg className={className} style={style} width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
