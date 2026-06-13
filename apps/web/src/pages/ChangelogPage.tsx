import { PageHeader } from "../components/PageHeader";
import { CHANGELOG_RELEASES, GCR_VERSION } from "../constants/changelog";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";
import { useParams } from "react-router-dom";

export function ChangelogPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);

  return (
    <div>
      <PageHeader
        title="Changelog"
        subtitle={`Growth Control Room · versione corrente ${GCR_VERSION}`}
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          {
            label: project?.name ?? id ?? "",
            href: id ? APP_ROUTES.project(id) : undefined,
          },
          { label: "Changelog" },
        ]}
      />

      <p className="gcr-card__description" style={{ marginBottom: "1.5rem" }}>
        Il progetto è in fase Alpha. Vedi{" "}
        <code>docs/changelog-policy.md</code> per le regole di versioning.
      </p>

      <div className="changelog-list">
        {CHANGELOG_RELEASES.map((release) => (
          <article key={release.version} className="gcr-card changelog-release">
            <header className="changelog-release__header">
              <h2 className="gcr-card__title">[{release.version}]</h2>
              <span className="changelog-release__meta">
                {release.date} · {release.type}
              </span>
            </header>
            <ul className="changelog-release__items">
              {release.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </div>
  );
}
