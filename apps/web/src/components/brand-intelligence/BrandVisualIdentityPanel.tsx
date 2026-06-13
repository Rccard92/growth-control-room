import { FormEvent, useEffect, useState } from "react";
import type { BrandVisualIdentity, VisualColorSwatch, VisualExtractProposal } from "@gcr/shared";
import {
  useApplyVisualProposal,
  useBrandProfile,
  useBrandVisualIdentity,
  useExtractVisualFromWebsite,
  useUpdateBrandVisualIdentity,
} from "../../hooks/useBrandIntelligence";

interface BrandVisualIdentityPanelProps {
  projectId: string;
}

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function paletteToText(palette: VisualColorSwatch[] | null | undefined): string {
  return (palette ?? [])
    .map((s) => {
      const parts = [s.hex];
      if (s.role) parts.push(s.role);
      if (s.label) parts.push(s.label);
      return parts.join(" | ");
    })
    .join("\n");
}

function textToPalette(text: string): VisualColorSwatch[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [hex, role, label] = line.split("|").map((s) => s.trim());
      return { hex: hex || "#000000", role: role || null, label: label || null };
    });
}

function fontsToText(fonts: BrandVisualIdentity["fonts"]): string {
  return (fonts ?? [])
    .map((f) => {
      const parts = [f.name];
      if (f.role) parts.push(f.role);
      if (f.usage) parts.push(f.usage);
      return parts.join(" | ");
    })
    .join("\n");
}

function textToFonts(text: string): BrandVisualIdentity["fonts"] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [name, role, usage] = line.split("|").map((s) => s.trim());
      return { name: name || "Font", role: role || null, usage: usage || null };
    });
}

function visualToForm(visual: BrandVisualIdentity): Partial<BrandVisualIdentity> {
  return {
    primaryLogoUrl: visual.primaryLogoUrl ?? "",
    secondaryLogoUrl: visual.secondaryLogoUrl ?? "",
    faviconUrl: visual.faviconUrl ?? "",
    primaryColor: visual.primaryColor ?? "",
    secondaryColor: visual.secondaryColor ?? "",
    accentColor: visual.accentColor ?? "",
    backgroundColor: visual.backgroundColor ?? "",
    textColor: visual.textColor ?? "",
    colorPalette: visual.colorPalette ?? [],
    fonts: visual.fonts ?? [],
    visualStyleNotes: visual.visualStyleNotes ?? "",
    imageStyleNotes: visual.imageStyleNotes ?? "",
    doShow: visual.doShow ?? [],
    doNotShow: visual.doNotShow ?? [],
  };
}

function proposalHasData(proposal: VisualExtractProposal): boolean {
  return Boolean(
    proposal.primaryLogoUrl?.trim()
      || proposal.faviconUrl?.trim()
      || proposal.visualStyleNotes?.trim()
      || (proposal.colorPalette?.length ?? 0) > 0
      || (proposal.fonts?.length ?? 0) > 0,
  );
}

function visualHasData(visual: BrandVisualIdentity): boolean {
  return Boolean(
    visual.primaryLogoUrl?.trim()
      || visual.faviconUrl?.trim()
      || visual.visualStyleNotes?.trim()
      || (visual.colorPalette?.length ?? 0) > 0
      || visual.primaryColor?.trim(),
  );
}

export function BrandVisualIdentityPanel({ projectId }: BrandVisualIdentityPanelProps) {
  const { data: visual, isLoading } = useBrandVisualIdentity(projectId);
  const { data: profile } = useBrandProfile(projectId);
  const update = useUpdateBrandVisualIdentity(projectId);
  const extract = useExtractVisualFromWebsite(projectId);
  const applyProposal = useApplyVisualProposal(projectId);

  const [form, setForm] = useState<Partial<BrandVisualIdentity>>({});
  const [extractUrl, setExtractUrl] = useState("");
  const [proposal, setProposal] = useState<VisualExtractProposal | null>(null);
  const [extractWarnings, setExtractWarnings] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!visual) return;
    setForm(visualToForm(visual));
  }, [visual]);

  function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    update.mutate(
      {
        primaryLogoUrl: form.primaryLogoUrl || undefined,
        secondaryLogoUrl: form.secondaryLogoUrl || undefined,
        faviconUrl: form.faviconUrl || undefined,
        primaryColor: form.primaryColor || undefined,
        secondaryColor: form.secondaryColor || undefined,
        accentColor: form.accentColor || undefined,
        backgroundColor: form.backgroundColor || undefined,
        textColor: form.textColor || undefined,
        colorPalette: form.colorPalette?.length ? form.colorPalette : undefined,
        fonts: form.fonts?.length ? form.fonts : undefined,
        visualStyleNotes: form.visualStyleNotes || undefined,
        imageStyleNotes: form.imageStyleNotes || undefined,
        doShow: form.doShow?.length ? form.doShow : undefined,
        doNotShow: form.doNotShow?.length ? form.doNotShow : undefined,
      },
      { onError: (err: Error) => setError(err.message) },
    );
  }

  function handleExtract() {
    setError(null);
    const url = extractUrl.trim() || profile?.websiteUrl?.trim() || "";
    if (!url) {
      setError("Inserisci un URL sito o compila il sito nel Brand Profile.");
      return;
    }
    extract.mutate(
      { websiteUrl: url },
      {
        onSuccess: (res) => {
          setProposal({ ...res.proposal });
          setExtractWarnings(res.warnings);
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleApplyProposal() {
    if (!proposal) return;
    setError(null);
    setSuccessMessage(null);
    const hadProposalData = proposalHasData(proposal);
    applyProposal.mutate(
      { proposal },
      {
        onSuccess: (data) => {
          if (hadProposalData && !visualHasData(data.visualIdentity)) {
            setError("La proposta non è stata salvata correttamente. Riprova.");
            return;
          }
          setForm(visualToForm(data.visualIdentity));
          setSuccessMessage(data.message || "Visual Identity aggiornata.");
          setProposal(null);
          setExtractWarnings([]);
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  const palette = proposal?.colorPalette ?? form.colorPalette ?? [];

  return (
    <div className="bi-profile-v1">
      {error && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      {successMessage && (
        <div className="gcr-alert gcr-alert--success" style={{ marginBottom: "1rem" }}>
          {successMessage}
        </div>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Recupera da sito</h3>
        <p className="bi-panel__subtitle">
          Estrae logo, favicon, palette e font dal sito. La proposta non viene salvata finché non
          la applichi.
        </p>
        <div className="bi-form-grid">
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="extractUrl">URL sito</label>
            <input
              id="extractUrl"
              placeholder={profile?.websiteUrl ?? "https://…"}
              value={extractUrl}
              onChange={(e) => setExtractUrl(e.target.value)}
            />
          </div>
        </div>
        <div className="bi-profile-actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={extract.isPending}
            onClick={handleExtract}
          >
            {extract.isPending ? "Recupero in corso…" : "Recupera da sito"}
          </button>
        </div>
      </section>

      {proposal && (
        <section className="bi-profile-block gcr-card bi-visual-proposal">
          <h3 className="bi-panel__title">Proposta estrazione</h3>
          {extractWarnings.length > 0 && (
            <ul className="bi-warnings-list">
              {extractWarnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          )}
          <div className="bi-form-grid">
            <div className="gcr-field">
              <label>Logo principale</label>
              <input
                value={proposal.primaryLogoUrl ?? ""}
                onChange={(e) =>
                  setProposal((p) => (p ? { ...p, primaryLogoUrl: e.target.value } : p))
                }
              />
            </div>
            <div className="gcr-field">
              <label>Favicon</label>
              <input
                value={proposal.faviconUrl ?? ""}
                onChange={(e) =>
                  setProposal((p) => (p ? { ...p, faviconUrl: e.target.value } : p))
                }
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label>Note stile visuale</label>
              <textarea
                rows={2}
                value={proposal.visualStyleNotes ?? ""}
                onChange={(e) =>
                  setProposal((p) => (p ? { ...p, visualStyleNotes: e.target.value } : p))
                }
              />
            </div>
          </div>

          {(proposal.colorPalette?.length ?? 0) > 0 && (
            <div className="bi-palette-preview">
              {proposal.colorPalette!.map((swatch) => (
                <div key={swatch.hex + (swatch.role ?? "")} className="bi-color-swatch-item">
                  <span
                    className="bi-color-swatch"
                    style={{ backgroundColor: swatch.hex }}
                    title={swatch.hex}
                  />
                  <span className="bi-color-swatch__meta">
                    {swatch.hex}
                    {swatch.role ? ` · ${swatch.role}` : ""}
                    {swatch.confidence != null
                      ? ` · ${Math.round(swatch.confidence * 100)}%`
                      : ""}
                  </span>
                </div>
              ))}
            </div>
          )}

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
              onClick={() => {
                setProposal(null);
                setExtractWarnings([]);
              }}
            >
              Annulla
            </button>
          </div>
        </section>
      )}

      <form onSubmit={handleSave}>
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Visual Identity ufficiale</h3>
          <p className="bi-panel__subtitle">
            Dati salvati ufficialmente. Aggiornati automaticamente dopo Applica proposta o
            salvataggio manuale.
          </p>
        </section>

        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Logo &amp; Assets</h3>
          <div className="bi-form-grid">
            <div className="gcr-field">
              <label htmlFor="primaryLogo">Logo principale (URL)</label>
              <input
                id="primaryLogo"
                value={form.primaryLogoUrl ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, primaryLogoUrl: e.target.value }))}
              />
            </div>
            <div className="gcr-field">
              <label htmlFor="secondaryLogo">Logo secondario (URL)</label>
              <input
                id="secondaryLogo"
                value={form.secondaryLogoUrl ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, secondaryLogoUrl: e.target.value }))}
              />
            </div>
            <div className="gcr-field">
              <label htmlFor="favicon">Favicon (URL)</label>
              <input
                id="favicon"
                value={form.faviconUrl ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, faviconUrl: e.target.value }))}
              />
            </div>
          </div>
        </section>

        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Palette</h3>
          <div className="bi-form-grid">
            {(
              [
                ["primaryColor", "Primario"],
                ["secondaryColor", "Secondario"],
                ["accentColor", "Accento"],
                ["backgroundColor", "Sfondo"],
                ["textColor", "Testo"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field" key={key}>
                <label htmlFor={key}>{label}</label>
                <div className="bi-color-field">
                  <span
                    className="bi-color-swatch"
                    style={{
                      backgroundColor: (form[key] as string) || "#333",
                    }}
                  />
                  <input
                    id={key}
                    value={(form[key] as string) ?? ""}
                    placeholder="#RRGGBB"
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              </div>
            ))}
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="extraPalette">Palette extra (hex | ruolo | etichetta, uno per riga)</label>
              <textarea
                id="extraPalette"
                rows={4}
                value={paletteToText(form.colorPalette)}
                onChange={(e) =>
                  setForm((f) => ({ ...f, colorPalette: textToPalette(e.target.value) }))
                }
              />
            </div>
          </div>
          {palette.length > 0 && !proposal && (
            <div className="bi-palette-preview">
              {palette.map((swatch) => (
                <div key={swatch.hex + (swatch.role ?? "")} className="bi-color-swatch-item">
                  <span
                    className="bi-color-swatch"
                    style={{ backgroundColor: swatch.hex }}
                    title={swatch.hex}
                  />
                  <span className="bi-color-swatch__meta">
                    {swatch.hex}
                    {swatch.role ? ` · ${swatch.role}` : ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Font</h3>
          <div className="gcr-field bi-form-grid--full">
            <label htmlFor="fonts">Font (nome | ruolo | utilizzo, uno per riga)</label>
            <textarea
              id="fonts"
              rows={3}
              value={fontsToText(form.fonts)}
              onChange={(e) => setForm((f) => ({ ...f, fonts: textToFonts(e.target.value) }))}
            />
          </div>
        </section>

        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Stile visuale</h3>
          <div className="bi-form-grid">
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="visualStyleNotes">Note stile visuale</label>
              <textarea
                id="visualStyleNotes"
                rows={3}
                value={form.visualStyleNotes ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, visualStyleNotes: e.target.value }))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="imageStyleNotes">Note stile immagini</label>
              <textarea
                id="imageStyleNotes"
                rows={3}
                value={form.imageStyleNotes ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, imageStyleNotes: e.target.value }))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="doShow">Da mostrare (uno per riga)</label>
              <textarea
                id="doShow"
                rows={3}
                value={listToLines(form.doShow)}
                onChange={(e) => setForm((f) => ({ ...f, doShow: linesToList(e.target.value) }))}
              />
            </div>
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor="doNotShow">Da non mostrare (uno per riga)</label>
              <textarea
                id="doNotShow"
                rows={3}
                value={listToLines(form.doNotShow)}
                onChange={(e) =>
                  setForm((f) => ({ ...f, doNotShow: linesToList(e.target.value) }))
                }
              />
            </div>
          </div>
        </section>

        <div className="bi-profile-actions">
          <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
            {update.isPending ? "Salvataggio…" : "Salva manualmente"}
          </button>
        </div>
      </form>
    </div>
  );
}
