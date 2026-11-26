// Residential / Commercial / Industrial solar pages.
import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import Icon from "../../components/Icon";
import SavingsCalculator from "../../components/SavingsCalculator";
import { CtaBand, Faq, FeatureGrid, PageHero, Reveal, SectionHead, Ticks } from "../../components/Site";
import { useI18n } from "../../i18n";
import { site, type SolutionKey } from "../../siteContent";

const CALC_TYPE = { residential: "home", commercial: "commercial", industrial: "industry" } as const;

export default function SolutionPage({ kind }: { kind: SolutionKey }) {
  const { slug } = useParams();
  const { lang } = useI18n();
  const s = site[lang];
  const p = s.solutions[kind];

  useEffect(() => {
    const prev = document.title;
    document.title = p.title;
    return () => { document.title = prev; };
  }, [p.title]);

  return (
    <>
      <PageHero eyebrow={p.eyebrow} title={p.title} lead={p.lead} image={p.image}>
        <Link className="btn btn-sun btn-lg" to={`/s/${slug}/request`}><Icon name="clipboard" size={18} /> {s.common.freeSurvey}</Link>
        <a className="btn btn-outline-light btn-lg" href="#calc">{s.nav.calculator}</a>
      </PageHero>

      <section className="sec">
        <div className="ideal">
          <h2>{p.idealTitle}</h2>
          <ul className="chip-list">
            {p.ideal.map((x) => <li key={x}><Icon name="check" size={16} /> {x}</li>)}
          </ul>
        </div>
      </section>

      <section className="sec">
        <SectionHead title={p.benefitsTitle} />
        <FeatureGrid items={p.benefits} />
      </section>

      <section className="sec two-up">
        <Reveal className="panel-card">
          <h2>{p.sizesTitle}</h2>
          <p className="muted">{p.sizesLead}</p>
          <table className="size-table">
            <tbody>
              {p.sizes.map((r) => (
                <tr key={r.label}><td>{r.label}</td><td className="num"><strong>{r.value}</strong></td></tr>
              ))}
            </tbody>
          </table>
        </Reveal>
        <Reveal className="panel-card" delay={100}>
          <h2>{p.pointsTitle}</h2>
          <Ticks items={p.points} />
          <div className="note small">{s.common.noPrice}</div>
        </Reveal>
      </section>

      <section className="sec" id="calc">
        <SectionHead title={p.calcTitle} />
        <SavingsCalculator key={kind} defaultType={CALC_TYPE[kind]} />
      </section>

      <Faq title={s.common.faqTitle} items={p.faq} />
      <CtaBand />
    </>
  );
}
