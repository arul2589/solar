import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { content } from "../../content";
import { useI18n } from "../../i18n";
import { IconCards } from "./Landing";
import { useInstaller } from "./PublicLayout";

export default function About() {
  const { slug } = useParams();
  const { lang, t } = useI18n();
  const info = useInstaller();
  const c = content[lang].about;
  const nav = content[lang].nav;
  const name = info?.name ?? "";

  useEffect(() => {
    const prev = document.title;
    document.title = c.title.replace("{name}", name);
    return () => { document.title = prev; };
  }, [c.title, name]);

  return (
    <>
      <section className="hero">
        <h1>{c.title.replace("{name}", name)}</h1>
        <p>{c.lead.replace("{name}", name)}</p>
        <div className="hero-actions">
          <Link className="btn" to={`/s/${slug}/request`}>{t("get_quote")}</Link>
        </div>
      </section>

      <section className="block">
        <h2>{c.whatTitle}</h2>
        <IconCards items={c.what} />
      </section>

      <section className="block">
        <h2>{c.whyTitle}</h2>
        <IconCards items={c.why} />
      </section>

      <section className="block card">
        <h2>{c.processTitle}</h2>
        <ol className="steps">
          {c.process.map((p) => <li key={p}>{p}</li>)}
        </ol>
      </section>

      <section className="block card savings">
        <h2>{c.safetyTitle}</h2>
        <ul className="ticks">
          {c.safety.map((p) => <li key={p}>{p}</li>)}
        </ul>
      </section>

      <section className="cta-band">
        <h2>{c.contactTitle}</h2>
        <p>{c.contactText}</p>
        <dl className="contact-list">
          {info?.address && (<><dt>{c.address}</dt><dd>{info.address}</dd></>)}
          {info?.phone && (<><dt>{c.phone}</dt><dd><a href={`tel:${info.phone.replace(/\s/g, "")}`}>{info.phone}</a></dd></>)}
          {info?.email && (<><dt>{c.email}</dt><dd><a href={`mailto:${info.email}`}>{info.email}</a></dd></>)}
        </dl>
        <div className="hero-actions" style={{ justifyContent: "center" }}>
          <Link className="btn" to={`/s/${slug}/request`}>{nav.quote}</Link>
        </div>
      </section>
    </>
  );
}
