// Shared building blocks for the public marketing pages.
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { useInstaller } from "../pages/public/PublicLayout";
import { useI18n } from "../i18n";
import { site, type Card, type QA } from "../siteContent";
import Icon from "./Icon";

/** Fades children in when they scroll into view (respects reduced motion via CSS). */
export function Reveal({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") { setOn(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setOn(true); io.disconnect(); } }, { threshold: 0.12 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <div ref={ref} className={`reveal${on ? " in" : ""} ${className}`} style={{ transitionDelay: `${delay}ms` }}>{children}</div>;
}

export function SectionHead({ eyebrow, title, lead, center = true }: { eyebrow?: string; title: string; lead?: string; center?: boolean }) {
  return (
    <div className={`sec-head${center ? " center" : ""}`}>
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      <h2>{title}</h2>
      {lead && <p>{lead}</p>}
    </div>
  );
}

export function PageHero({ eyebrow, title, lead, image, children }: { eyebrow: string; title: string; lead: string; image?: string; children?: ReactNode }) {
  return (
    <section className={`page-hero${image ? " with-img" : ""}`} style={image ? { backgroundImage: `url(${image})` } : undefined}>
      <div className="page-hero-inner">
        <div className="eyebrow light">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{lead}</p>
        {children && <div className="hero-actions">{children}</div>}
      </div>
    </section>
  );
}

export function FeatureGrid({ items, cols = 3 }: { items: Card[]; cols?: 2 | 3 }) {
  return (
    <div className={`feat-grid cols-${cols}`}>
      {items.map((b, i) => (
        <Reveal key={b.title} delay={i * 60}>
          <div className="feat">
            <span className="feat-icon"><Icon name={b.icon} /></span>
            <h3>{b.title}</h3>
            <p>{b.text}</p>
          </div>
        </Reveal>
      ))}
    </div>
  );
}

export function Faq({ items, title }: { items: QA[]; title: string }) {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section className="sec">
      <SectionHead title={title} />
      <div className="faq">
        {items.map((f, i) => (
          <div className={`faq-item ${open === i ? "open" : ""}`} key={f.q}>
            <button className="faq-q" aria-expanded={open === i} onClick={() => setOpen(open === i ? null : i)}>
              <span>{f.q}</span>
              <span aria-hidden="true">{open === i ? "−" : "+"}</span>
            </button>
            {open === i && <div className="faq-a">{f.a}</div>}
          </div>
        ))}
      </div>
    </section>
  );
}

export function Ticks({ items }: { items: string[] }) {
  return (
    <ul className="tick-list">
      {items.map((p) => <li key={p}><Icon name="check" size={18} /> <span>{p}</span></li>)}
    </ul>
  );
}

export function CtaBand() {
  const { slug } = useParams();
  const { lang } = useI18n();
  const info = useInstaller();
  const c = site[lang].common;
  return (
    <section className="cta-strip">
      <div>
        <h2>{c.readyTitle}</h2>
        <p>{c.readyText}</p>
      </div>
      <div className="cta-strip-actions">
        <Link className="btn btn-sun" to={`/s/${slug}/request`}><Icon name="clipboard" size={18} /> {c.freeSurvey}</Link>
        {info?.phone && (
          <a className="btn btn-outline-light" href={`tel:${info.phone.replace(/\s/g, "")}`}><Icon name="phone" size={18} /> {info.phone}</a>
        )}
      </div>
    </section>
  );
}
