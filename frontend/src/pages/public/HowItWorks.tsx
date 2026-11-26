import { Link, useParams } from "react-router-dom";
import Icon from "../../components/Icon";
import SolarFlow from "../../components/SolarFlow";
import { CtaBand, FeatureGrid, PageHero, Reveal, SectionHead, Ticks } from "../../components/Site";
import { content } from "../../content";
import { useI18n } from "../../i18n";
import { site } from "../../siteContent";

export default function HowItWorks() {
  const { slug } = useParams();
  const { lang } = useI18n();
  const s = site[lang];
  const h = s.how;
  const old = content[lang].home;

  return (
    <>
      <PageHero eyebrow={h.eyebrow} title={h.title} lead={h.lead}>
        <Link className="btn btn-sun btn-lg" to={`/s/${slug}/request`}><Icon name="clipboard" size={18} /> {s.common.freeSurvey}</Link>
      </PageHero>

      <section className="sec">
        <ol className="roadmap">
          {h.steps.map((st, i) => (
            <li key={st.title} className={i % 2 ? "right" : "left"}>
              <span className="road-dot"><Icon name={st.icon} size={24} /></span>
              <Reveal className="road-card" delay={60}>
                <div className="road-time">{String(i + 1).padStart(2, "0")} · {st.time}</div>
                <h3>{st.title}</h3>
                <p>{st.text}</p>
                <ul className="tick-list compact">
                  {st.points.map((x) => <li key={x}><Icon name="check" size={16} /> <span>{x}</span></li>)}
                </ul>
              </Reveal>
            </li>
          ))}
        </ol>
      </section>

      <section className="sec sec-tint">
        <SectionHead title={h.flowTitle} lead={old.introText} />
        <SolarFlow steps={old.flow} />
      </section>

      <section className="sec two-up">
        <Reveal className="panel-card">
          <h2>{h.readyTitle}</h2>
          <Ticks items={h.ready} />
        </Reveal>
        <Reveal className="panel-card" delay={100}>
          <h2>{h.afterTitle}</h2>
          <FeatureGrid items={h.after} cols={2} />
        </Reveal>
      </section>

      <CtaBand />
    </>
  );
}
