import { Link, useParams } from "react-router-dom";
import { useI18n } from "../../i18n";
import { useInstaller } from "./PublicLayout";

export default function Landing() {
  const { slug } = useParams();
  const { t } = useI18n();
  const info = useInstaller();
  return (
    <>
      <section className="hero">
        <div className="small" style={{ opacity: 0.85 }}>{t("brand_tag")}</div>
        <h1>{t("hero_title")}</h1>
        <p>{t("hero_text")}</p>
        <Link className="btn" to={`/s/${slug}/request`}>{t("get_quote")}</Link>
      </section>
      <section className="card">
        <h2>{t("how_it_works")}</h2>
        <ol className="steps">
          <li>{t("step1")}</li>
          <li>{t("step2")}</li>
          <li>{t("step3")}</li>
          <li>{t("step4")}</li>
        </ol>
      </section>
      <section className="card">
        <h2>{info?.name}</h2>
        <p className="muted">{info?.address}</p>
        <p>{info?.phone && <a href={`tel:${info.phone.replace(/\s/g, "")}`}>{info.phone}</a>}</p>
        <Link to={`/s/${slug}/login`}>{t("check_status")}</Link>
      </section>
    </>
  );
}
