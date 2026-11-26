import { useState } from "react";
import Icon from "../../components/Icon";
import { CtaBand, PageHero, Reveal } from "../../components/Site";
import { useI18n } from "../../i18n";
import { site, visibleProjects, type Project } from "../../siteContent";

export function ProjectCard({ p }: { p: Project }) {
  const { lang } = useI18n();
  const c = site[lang].projects;
  return (
    <article className="proj-card">
      <div className="proj-img" style={{ backgroundImage: `url(${p.image})` }}>
        <span className={`proj-type t-${p.type}`}>{c.filters[p.type]}</span>
        {p.sample && <span className="proj-sample">{c.sampleTag}</span>}
      </div>
      <div className="proj-body">
        <h3>{p.title}</h3>
        <div className="proj-loc"><Icon name="pin" size={16} /> {p.location}{p.year ? ` · ${p.year}` : ""}</div>
        <dl className="proj-facts">
          <div><dt>{c.capacity}</dt><dd>{p.capacity}</dd></div>
          <div><dt>{c.system}</dt><dd>{p.system}</dd></div>
        </dl>
        {p.result && <div className="proj-result"><Icon name="chart" size={16} /> <span><strong>{c.result}:</strong> {p.result}</span></div>}
      </div>
    </article>
  );
}

export default function Projects() {
  const { lang } = useI18n();
  const c = site[lang].projects;
  const [filter, setFilter] = useState<Project["type"] | "all">("all");
  const all = visibleProjects(c.items);
  const shown = filter === "all" ? all : all.filter((p) => p.type === filter);
  const types = (Object.keys(c.filters) as Project["type"][]).filter((t) => all.some((p) => p.type === t));

  return (
    <>
      <PageHero eyebrow={c.eyebrow} title={c.title} lead={c.lead} image="/img/industrial.jpg" />
      <section className="sec">
        {all.length === 0 ? (
          <div className="panel-card empty"><Icon name="camera" size={34} /><p>{c.empty}</p></div>
        ) : (
          <>
            <div className="filter-row" role="tablist">
              <button className={filter === "all" ? "on" : ""} onClick={() => setFilter("all")}>{c.all} ({all.length})</button>
              {types.map((t) => (
                <button key={t} className={filter === t ? "on" : ""} onClick={() => setFilter(t)}>
                  {c.filters[t]} ({all.filter((p) => p.type === t).length})
                </button>
              ))}
            </div>
            <div className="proj-grid">
              {shown.map((p, i) => (
                <Reveal key={p.title + p.capacity + i} delay={i * 60}><ProjectCard p={p} /></Reveal>
              ))}
            </div>
          </>
        )}
      </section>
      <CtaBand />
    </>
  );
}
