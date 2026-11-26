import { Link, useParams } from "react-router-dom";
import Icon from "../../components/Icon";
import { CtaBand, FeatureGrid, PageHero, Reveal, SectionHead } from "../../components/Site";
import { useI18n } from "../../i18n";
import { site } from "../../siteContent";

export default function Products() {
  const { slug } = useParams();
  const { lang } = useI18n();
  const s = site[lang];
  const p = s.products;

  return (
    <>
      <PageHero eyebrow={p.eyebrow} title={p.title} lead={p.lead} image="/img/hybrid-battery.jpg">
        <Link className="btn btn-sun btn-lg" to={`/s/${slug}/request`}><Icon name="clipboard" size={18} /> {s.common.freeSurvey}</Link>
      </PageHero>

      <section className="sec">
        <SectionHead title={p.typesTitle} />
        <div className="type-grid">
          {p.types.map((t, i) => (
            <Reveal key={t.title} delay={i * 80}>
              <div className="type-card">
                <span className="feat-icon big"><Icon name={t.icon} size={30} /></span>
                <h3>{t.title}</h3>
                <p>{t.text}</p>
                <ul className="tick-list compact">
                  {t.points.map((x) => <li key={x}><Icon name="check" size={16} /> <span>{x}</span></li>)}
                </ul>
                <div className="best"><span>{p.bestFor}</span> {t.best}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="sec sec-tint">
        <SectionHead title={p.partsTitle} lead={p.partsLead} />
        <FeatureGrid items={p.parts} />
      </section>

      <section className="sec">
        <SectionHead title={p.compareTitle} />
        <div className="table-wrap compare">
          <table>
            <thead><tr>{p.compareHead.map((h, i) => <th key={i}>{h}</th>)}</tr></thead>
            <tbody>
              {p.compareRows.map((r) => (
                <tr key={r[0]}>{r.map((c, i) => (i === 0 ? <th key={i} scope="row">{c}</th> : <td key={i}>{c}</td>))}</tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="note">{p.note}</div>
      </section>

      <CtaBand />
    </>
  );
}
