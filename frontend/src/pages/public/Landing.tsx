import { Fragment } from "react";
import { Link, useParams } from "react-router-dom";
import Icon from "../../components/Icon";
import SavingsCalculator from "../../components/SavingsCalculator";
import { CtaBand, Faq, FeatureGrid, Reveal, SectionHead } from "../../components/Site";
import { content } from "../../content";
import { useI18n } from "../../i18n";
import { site, visibleProjects } from "../../siteContent";
import { ProjectCard } from "./Projects";

// Kept for the About page.
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

const BENEFIT_ICONS = ["rupee", "meter", "wrench", "chart", "leaf", "battery"];

export default function Landing() {
  const { slug } = useParams();
  const { lang } = useI18n();
  const s = site[lang];
  const h = s.home;
  const old = content[lang].home;
  const projects = visibleProjects(s.projects.items).slice(0, 3);
  const base = `/s/${slug}`;

  return (
    <>
      <section className="home-hero" style={{ backgroundImage: "url(/img/residential.jpg)" }}>
        <div className="home-hero-inner">
          <span className="badge-pill">{h.badge}</span>
          <h1>{h.title} <span className="hi">{h.titleHi}</span></h1>
          <p className="lead">{h.lead}</p>
          <div className="hero-actions">
            <Link className="btn btn-sun btn-lg" to={`${base}/request`}><Icon name="clipboard" size={18} /> {s.common.freeSurvey}</Link>
            <Link className="btn btn-outline-light btn-lg" to={`${base}/how-it-works`}>{h.ctaHow} <Icon name="arrow" size={18} /></Link>
          </div>
          <ul className="trust">
            {h.trust.map((t) => (
              <li key={t.title}><Icon name={t.icon} size={26} /><span>{t.title}</span></li>
            ))}
          </ul>
        </div>
      </section>

      <section className="sec">
        <SectionHead eyebrow={h.solEyebrow} title={h.solTitle} lead={h.solLead} />
        <div className="sol-grid">
          {h.solutions.map((x, i) => (
            <Reveal key={x.key} delay={i * 80}>
              <Link className="sol-card" to={`${base}/${x.key}`}>
                <div className="sol-img" style={{ backgroundImage: `url(${x.image})` }} />
                <div className="sol-body">
                  <span className="sol-icon"><Icon name={x.icon} size={28} /></span>
                  <div>
                    <h3>{x.title}</h3>
                    <p>{x.text}</p>
                    <span className="more">{s.common.explore} <Icon name="arrow" size={16} /></span>
                  </div>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="sec">
        <SavingsCalculator compact />
      </section>

      <section className="sec">
        <SectionHead eyebrow={h.stepsEyebrow} title={h.stepsTitle} />
        <div className="steps-row">
          {s.how.steps.map((st, i) => (
            <Fragment key={st.title}>
              {i > 0 && <span className="steps-arrow" aria-hidden="true"><Icon name="arrow" /></span>}
              <Reveal delay={i * 90} className="step-mini">
                <span className={`step-circle${i === s.how.steps.length - 1 ? " last" : ""}`}><Icon name={st.icon} size={28} /></span>
                <h3>{i + 1}. {st.title}</h3>
                <p>{st.text}</p>
              </Reveal>
            </Fragment>
          ))}
        </div>
      </section>

      <section className="sec sec-tint">
        <SectionHead eyebrow={h.whyEyebrow} title={h.whyTitle} lead={old.benefitsLead} />
        <FeatureGrid items={old.benefits.map((b, i) => ({ icon: BENEFIT_ICONS[i] ?? "sun", title: b.title, text: b.text }))} />
      </section>

      {projects.length > 0 && (
        <section className="sec">
          <div className="sec-head-row">
            <SectionHead center={false} title={h.projectsTitle} lead={h.projectsLead} />
            <Link className="link-more" to={`${base}/projects`}>{s.common.viewAll} <Icon name="arrow" size={16} /></Link>
          </div>
          <div className="proj-grid">
            {projects.map((p) => <ProjectCard key={p.title + p.capacity} p={p} />)}
          </div>
        </section>
      )}

      <Faq title={old.faqTitle} items={old.faq} />
      <CtaBand />
    </>
  );
}
