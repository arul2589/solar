import SavingsCalculator from "../../components/SavingsCalculator";
import { CtaBand, PageHero, Reveal, Ticks } from "../../components/Site";
import { useI18n } from "../../i18n";
import { site } from "../../siteContent";

export default function CalculatorPage() {
  const { lang } = useI18n();
  const s = site[lang];
  const c = s.calc;
  return (
    <>
      <PageHero eyebrow={c.eyebrow} title={c.title} lead={c.lead} />
      <section className="sec">
        <SavingsCalculator />
      </section>
      <section className="sec">
        <Reveal className="panel-card">
          <h2>{c.howTitle}</h2>
          <Ticks items={c.how} />
          <div className="note small">{s.common.noPrice}</div>
        </Reveal>
      </section>
      <CtaBand />
    </>
  );
}
