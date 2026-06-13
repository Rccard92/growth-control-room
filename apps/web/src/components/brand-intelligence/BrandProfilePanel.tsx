import { FormEvent, useEffect, useState } from "react";
import type {
  BrandProfile,
  BrandProfileEnrichResponse,
  BrandProfileProposal,
  BrandProfileSourceResult,
} from "@gcr/shared";
import {
  useApplyBrandProfileProposal,
  useBrandProfile,
  useEnrichBrandProfile,
  useUpdateBrandProfile,
} from "../../hooks/useBrandIntelligence";

interface BrandProfilePanelProps {
  projectId: string;
}

const EMPTY_SOURCES = {
  brandName: "",
  websiteUrl: "",
  instagramUrl: "",
  facebookUrl: "",
  tiktokUrl: "",
  youtubeUrl: "",
  linkedinUrl: "",
  trustpilotUrl: "",
  googleBusinessUrl: "",
  otherSourcesText: "",
};

type SourcesForm = typeof EMPTY_SOURCES;

function parseOtherSources(text: string): Array<{ label: string; url: string }> {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, url] = line.split("|").map((s) => s.trim());
      return { label: label || "other", url: url || label };
    });
}

export function BrandProfilePanel({ projectId }: BrandProfilePanelProps) {
  const { data: profile, isLoading } = useBrandProfile(projectId);
  const update = useUpdateBrandProfile(projectId);
  const enrich = useEnrichBrandProfile(projectId);
  const applyProposal = useApplyBrandProfileProposal(projectId);

  const [sourcesForm, setSourcesForm] = useState<SourcesForm>(EMPTY_SOURCES);
  const [enrichResult, setEnrichResult] = useState<BrandProfileEnrichResponse | null>(null);
  const [proposal, setProposal] = useState<BrandProfileProposal | null>(null);
  const [officialForm, setOfficialForm] = useState<Partial<BrandProfile>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!profile) return;
    setSourcesForm({
      brandName: profile.brandName ?? "",
      websiteUrl: profile.websiteUrl ?? "",
      instagramUrl: profile.instagramUrl ?? "",
      facebookUrl: profile.facebookUrl ?? "",
      tiktokUrl: profile.tiktokUrl ?? "",
      youtubeUrl: profile.youtubeUrl ?? "",
      linkedinUrl: profile.linkedinUrl ?? "",
      trustpilotUrl: profile.trustpilotUrl ?? "",
      googleBusinessUrl: profile.googleBusinessUrl ?? "",
      otherSourcesText: (profile.otherSources ?? [])
        .map((s) => `${s.label ?? "other"}|${s.url ?? ""}`)
        .join("\n"),
    });
  }, [profile]);

  const official = { ...profile, ...officialForm };

  function handleSaveSources(e: FormEvent) {
    e.preventDefault();
    setError(null);
    update.mutate({
      brandName: sourcesForm.brandName || undefined,
      websiteUrl: sourcesForm.websiteUrl || undefined,
      instagramUrl: sourcesForm.instagramUrl || undefined,
      facebookUrl: sourcesForm.facebookUrl || undefined,
      tiktokUrl: sourcesForm.tiktokUrl || undefined,
      youtubeUrl: sourcesForm.youtubeUrl || undefined,
      linkedinUrl: sourcesForm.linkedinUrl || undefined,
      trustpilotUrl: sourcesForm.trustpilotUrl || undefined,
      googleBusinessUrl: sourcesForm.googleBusinessUrl || undefined,
      otherSources: parseOtherSources(sourcesForm.otherSourcesText),
    });
  }

  function handleEnrich() {
    setError(null);
    enrich.mutate(
      {
        brandName: sourcesForm.brandName,
        websiteUrl: sourcesForm.websiteUrl || undefined,
        instagramUrl: sourcesForm.instagramUrl || undefined,
        facebookUrl: sourcesForm.facebookUrl || undefined,
        tiktokUrl: sourcesForm.tiktokUrl || undefined,
        youtubeUrl: sourcesForm.youtubeUrl || undefined,
        linkedinUrl: sourcesForm.linkedinUrl || undefined,
        trustpilotUrl: sourcesForm.trustpilotUrl || undefined,
        googleBusinessUrl: sourcesForm.googleBusinessUrl || undefined,
        otherSources: parseOtherSources(sourcesForm.otherSourcesText),
      },
      {
        onSuccess: (res) => {
          setEnrichResult(res);
          setProposal({ ...res.proposal });
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleApplyProposal() {
    if (!proposal) return;
    setError(null);
    applyProposal.mutate(
      {
        proposal,
        confidence: enrichResult?.confidence,
        warnings: enrichResult?.warnings,
      },
      {
        onSuccess: () => {
          setEnrichResult(null);
          setProposal(null);
          setOfficialForm({});
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleSaveOfficial(e: FormEvent) {
    e.preventDefault();
    setError(null);
    update.mutate({
      shortDescription: official.shortDescription ?? undefined,
      story: official.story ?? undefined,
      mission: official.mission ?? undefined,
      values: official.values ?? undefined,
      differentiators: official.differentiators ?? undefined,
      originNotes: official.originNotes ?? undefined,
      productionNotes: official.productionNotes ?? undefined,
      toneNotes: official.toneNotes ?? undefined,
      customerNotes: official.customerNotes ?? undefined,
      aiSummary: official.aiSummary ?? undefined,
    }, {
      onSuccess: () => setOfficialForm({}),
    });
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-profile-v1">
      {error && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Blocco 1 — Fonti</h3>
        <p className="bi-panel__subtitle">
          Inserisci nome brand, sito e social. Le fonti vengono usate solo per generare una proposta.
        </p>
        <form onSubmit={handleSaveSources}>
          <div className="bi-form-grid">
            <div className="gcr-field">
              <label htmlFor="srcBrandName">Nome brand *</label>
              <input
                id="srcBrandName"
                value={sourcesForm.brandName}
                onChange={(e) => setSourcesForm((f) => ({ ...f, brandName: e.target.value }))}
                required
              />
            </div>
            <div className="gcr-field">
              <label htmlFor="srcWebsite">Sito web</label>
              <input
                id="srcWebsite"
                value={sourcesForm.websiteUrl}
                onChange={(e) => setSourcesForm((f) => ({ ...f, websiteUrl: e.target.value }))}
              />
            </div>
            {(
              [
                ["instagramUrl", "Instagram"],
                ["facebookUrl", "Facebook"],
                ["tiktokUrl", "TikTok"],
                ["youtubeUrl", "YouTube"],
                ["linkedinUrl", "LinkedIn"],
                ["trustpilotUrl", "Trustpilot"],
                ["googleBusinessUrl", "Google Business"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field" key={key}>
                <label htmlFor={key}>{label}</label>
                <input
                  id={key}
                  value={sourcesForm[key]}
                  onChange={(e) => setSourcesForm((f) => ({ ...f, [key]: e.target.value }))}
                />
              </div>
            ))}
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="otherSources">Altre fonti (una per riga: etichetta|url)</label>
              <textarea
                id="otherSources"
                rows={3}
                value={sourcesForm.otherSourcesText}
                onChange={(e) =>
                  setSourcesForm((f) => ({ ...f, otherSourcesText: e.target.value }))
                }
              />
            </div>
          </div>
          <div className="bi-profile-actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={enrich.isPending || !sourcesForm.brandName}
              onClick={handleEnrich}
            >
              {enrich.isPending ? "Recupero in corso…" : "Recupera informazioni"}
            </button>
            <button type="submit" className="gcr-btn gcr-btn--ghost" disabled={update.isPending}>
              Salva manualmente
            </button>
          </div>
        </form>
      </section>

      {proposal && (
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Blocco 2 — Proposta AI</h3>
          <p className="bi-panel__subtitle">
            Revisiona e modifica la proposta prima di applicarla al profilo ufficiale.
          </p>

          {enrichResult && (
            <div className="bi-source-results">
              {enrichResult.sources.map((s: BrandProfileSourceResult) => (
                <span
                  key={`${s.type}-${s.url}`}
                  className={`bi-source-badge bi-source-badge--${s.status}`}
                  title={s.warning ?? undefined}
                >
                  {s.type}: {s.status}
                </span>
              ))}
              <span className="bi-source-confidence">
                Confidence: {Math.round(enrichResult.confidence * 100)}%
              </span>
            </div>
          )}

          {enrichResult?.warnings.length ? (
            <ul className="bi-warnings-list">
              {enrichResult.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          ) : null}

          <div className="bi-form-grid">
            <div className="gcr-field bi-form-grid--full">
              <label>Descrizione breve</label>
              <textarea
                rows={3}
                value={proposal.shortDescription ?? ""}
                onChange={(e) =>
                  setProposal((p) => (p ? { ...p, shortDescription: e.target.value } : p))
                }
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Storia</label>
              <textarea
                rows={4}
                value={proposal.story ?? ""}
                onChange={(e) => setProposal((p) => (p ? { ...p, story: e.target.value } : p))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Missione</label>
              <textarea
                rows={2}
                value={proposal.mission ?? ""}
                onChange={(e) => setProposal((p) => (p ? { ...p, mission: e.target.value } : p))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Valori (uno per riga)</label>
              <textarea
                rows={3}
                value={(proposal.values ?? []).join("\n")}
                onChange={(e) =>
                  setProposal((p) =>
                    p
                      ? {
                          ...p,
                          values: e.target.value.split("\n").map((v) => v.trim()).filter(Boolean),
                        }
                      : p,
                  )
                }
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Differenziatori (uno per riga)</label>
              <textarea
                rows={3}
                value={(proposal.differentiators ?? []).join("\n")}
                onChange={(e) =>
                  setProposal((p) =>
                    p
                      ? {
                          ...p,
                          differentiators: e.target.value
                            .split("\n")
                            .map((v) => v.trim())
                            .filter(Boolean),
                        }
                      : p,
                  )
                }
              />
            </div>
            {(
              [
                ["originNotes", "Note origine"],
                ["productionNotes", "Note produzione"],
                ["toneNotes", "Tono"],
                ["customerNotes", "Note clienti"],
                ["aiSummary", "Summary AI"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field bi-form-grid--full" key={key}>
                <label>{label}</label>
                <textarea
                  rows={key === "aiSummary" ? 4 : 2}
                  value={proposal[key] ?? ""}
                  onChange={(e) =>
                    setProposal((p) => (p ? { ...p, [key]: e.target.value } : p))
                  }
                />
              </div>
            ))}
          </div>
          <div className="bi-profile-actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={applyProposal.isPending}
              onClick={handleApplyProposal}
            >
              {applyProposal.isPending ? "Applicazione…" : "Applica proposta"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              disabled={enrich.isPending}
              onClick={handleEnrich}
            >
              Rigenera
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              onClick={() => {
                setProposal(null);
                setEnrichResult(null);
              }}
            >
              Annulla
            </button>
          </div>
        </section>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Blocco 3 — Profilo ufficiale</h3>
        <p className="bi-panel__subtitle">
          Dati salvati e usati dai moduli AI (Content SEO, Product SEO, ecc.).
        </p>
        <form onSubmit={handleSaveOfficial}>
          <div className="bi-form-grid">
            <div className="gcr-field">
              <label>Brand</label>
              <input value={official.brandName ?? ""} readOnly />
            </div>
            <div className="gcr-field">
              <label>Sito</label>
              <input value={official.websiteUrl ?? ""} readOnly />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Descrizione breve</label>
              <textarea
                rows={3}
                value={official.shortDescription ?? ""}
                onChange={(e) =>
                  setOfficialForm((f) => ({ ...f, shortDescription: e.target.value }))
                }
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Storia</label>
              <textarea
                rows={4}
                value={official.story ?? ""}
                onChange={(e) => setOfficialForm((f) => ({ ...f, story: e.target.value }))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Missione</label>
              <textarea
                rows={2}
                value={official.mission ?? ""}
                onChange={(e) => setOfficialForm((f) => ({ ...f, mission: e.target.value }))}
              />
            </div>
            {(
              [
                ["originNotes", "Note origine"],
                ["productionNotes", "Note produzione"],
                ["toneNotes", "Tono"],
                ["customerNotes", "Note clienti"],
                ["aiSummary", "Summary AI"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field bi-form-grid--full" key={key}>
                <label>{label}</label>
                <textarea
                  rows={2}
                  value={official[key] ?? ""}
                  onChange={(e) => setOfficialForm((f) => ({ ...f, [key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          <button type="submit" className="gcr-btn gcr-btn--ghost" disabled={update.isPending}>
            Salva modifiche ufficiali
          </button>
        </form>
      </section>
    </div>
  );
}
