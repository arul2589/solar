import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import SolarFlow from "../../components/SolarFlow";
import { content } from "../../content";
import { useI18n } from "../../i18n";
import { useInstaller } from "./PublicLayout";

export function IconCards({ items }: { items: { icon?: string; title: string; text: string }[] }) {
  return (
    <div className="cards">
      {items.map((b) => (
        <div className="icard" key={b.title}>
          {b.icon && <div className="icard-icon" aria-hidden="true">{b.icon}</div>}
          <h3>{b.title}</h3>
          <p>{b.text}</p>
        </div>
      ))}
    </div>
  );
}

export default function Landing() {
  const { slug } = useParams();
  const { t, lang } = useI18n();
  const info = useInstaller();
  const c = content[lang].home;
  const nav = content[lang].nav;
  const [open, setOpen] = useState<number | null>(0);

  return (
    <>
      <section className="hero hero-lg">
        <div className="small" style={{ opacity: 0.9 }}>{t("brand_tag")}</div>
        <h1>{t("hero_title")}</h1>
        <p>{t("hero_text")}</p>
        <div className="hero-actions">
          <Link className="btn" to={`/s/${slug}/request`}>{t("get_quote")}</Link>
          <Link className="btn ghost-light" to={`/s/${slug}/about`}>{c.ctaAbout}</Link>
        </div>
        <ul className="chips">
          {c.chips.map((x) => <li key={x}>{x}</li>)}
        </ul>
      </section>

      <section className="block">
        <div className="two-col">
          <div>
            <h2>{c.introTitle}</h2>
            <p className="lead">{c.introText}</p>
          </div>
          <div className="callout">
            <strong>{c.flowNote}</strong>
          </div>
        </div>
        <SolarFlow steps={c.flow} />
      </section>

      <section className="block">
        <h2>{c.benefitsTitle}</h2>
        <p className="muted">{c.benefitsLead}</p>
        <IconCards items={c.benefits} />
      </section>

      <section className="block">
        <h2>{c.systemsTitle}</h2>
        <p className="muted">{c.systemsLead}</p>
        <IconCards items={c.systems} />
      </section>

      <section className="block">
        <h2>{c.whoTitle}</h2>
        <IconCards items={c.who} />
      </section>

      <section className="block card savings">
        <h2>{c.savingsTitle}</h2>
        <ul className="ticks">
          {c.savingsPoints.map((p) => <li key={p}>{p}</li>)}
        </ul>
        <div className="note">{c.savingsNote}</div>
      </section>

      <section className="block card">
        <h2>{t("how_it_works")}</h2>
        <ol className="steps">
          <li>{t("step1")}</li>
          <li>{t("step2")}</li>
          <li>{t("step3")}</li>
          <li>{t("step4")}</li>
        </ol>
      </section>

      <section className="block">
        <h2>{c.faqTitle}</h2>
        <div className="faq">
          {c.faq.map((f, i) => (
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

      <section className="cta-band">
        <h2>{c.ctaTitle}</h2>
        <p>{c.ctaText}</p>
        <div className="hero-actions" style={{ justifyContent: "center" }}>
          <Link className="btn" to={`/s/${slug}/request`}>{nav.quote}</Link>
          <Link className="btn ghost-light" to={`/s/${slug}/login`}>{t("check_status")}</Link>
        </div>
      </section>

      <section className="card contact">
        <h2>{info?.name}</h2>
        <p className="muted">{info?.address}</p>
        <p>{info?.phone && <a href={`tel:${info.phone.replace(/\s/g, "")}`}>{info.phone}</a>}</p>
      </section>
    </>
  );
}
