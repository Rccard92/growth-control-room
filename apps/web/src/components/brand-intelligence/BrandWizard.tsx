import { useState } from "react";
import {
  useBrandKnowledgeScore,
  useCreateBrandAudience,
  useCreateBrandClaim,
  useCreateBrandGuardrail,
  useCreateBrandPillar,
  useCreateBrandProduct,
  useUpdateBrandProfile,
  useUpdateBrandSeoStrategy,
  useUpdateBrandVoice,
} from "../../hooks/useBrandIntelligence";
import { BrandScoreRing } from "./BrandScoreRing";

const WIZARD_STEPS = [
  { id: 1, label: "Brand Basics" },
  { id: 2, label: "Voice & Tone" },
  { id: 3, label: "Products" },
  { id: 4, label: "Audience" },
  { id: 5, label: "Claims" },
  { id: 6, label: "SEO & Content" },
  { id: 7, label: "Guardrails" },
  { id: 8, label: "Completato" },
] as const;

interface BrandWizardProps {
  projectId: string;
  onComplete: () => void;
}

export function BrandWizard({ projectId, onComplete }: BrandWizardProps) {
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateProfile = useUpdateBrandProfile(projectId);
  const updateVoice = useUpdateBrandVoice(projectId);
  const createProduct = useCreateBrandProduct(projectId);
  const createAudience = useCreateBrandAudience(projectId);
  const createClaim = useCreateBrandClaim(projectId);
  const updateSeo = useUpdateBrandSeoStrategy(projectId);
  const createPillar = useCreateBrandPillar(projectId);
  const createGuardrail = useCreateBrandGuardrail(projectId);
  const { data: score, refetch: refetchScore } = useBrandKnowledgeScore(projectId);

  const [profile, setProfile] = useState({ brandName: "", shortDescription: "", websiteUrl: "", industry: "" });
  const [voice, setVoice] = useState({ tone: "", styleNotes: "" });
  const [product, setProduct] = useState({ name: "", description: "" });
  const [audience, setAudience] = useState({ segmentName: "", description: "" });
  const [claim, setClaim] = useState({ title: "", description: "" });
  const [seo, setSeo] = useState({ keywords: "", pillarName: "" });
  const [guardrail, setGuardrail] = useState({ title: "", description: "" });

  async function handleNext() {
    setError(null);
    setSaving(true);
    try {
      if (step === 1) {
        await updateProfile.mutateAsync({
          brandName: profile.brandName.trim() || undefined,
          shortDescription: profile.shortDescription.trim() || undefined,
          websiteUrl: profile.websiteUrl.trim() || undefined,
          industry: profile.industry.trim() || undefined,
        });
      } else if (step === 2) {
        await updateVoice.mutateAsync({
          tone: voice.tone.trim() || undefined,
          styleNotes: voice.styleNotes.trim() || undefined,
        });
      } else if (step === 3) {
        if (product.name.trim()) {
          await createProduct.mutateAsync({
            name: product.name.trim(),
            description: product.description.trim() || undefined,
            entityType: "product",
          });
        }
      } else if (step === 4) {
        if (audience.segmentName.trim()) {
          await createAudience.mutateAsync({
            segmentName: audience.segmentName.trim(),
            description: audience.description.trim() || undefined,
          });
        }
      } else if (step === 5) {
        if (claim.title.trim()) {
          await createClaim.mutateAsync({
            title: claim.title.trim(),
            description: claim.description.trim() || undefined,
            ruleType: "forbidden",
            severity: "critical",
          });
        }
      } else if (step === 6) {
        const keywords = seo.keywords.split(",").map((k) => k.trim()).filter(Boolean);
        if (keywords.length) {
          await updateSeo.mutateAsync({ primaryKeywords: keywords });
        }
        if (seo.pillarName.trim()) {
          await createPillar.mutateAsync({ name: seo.pillarName.trim() });
        }
      } else if (step === 7) {
        if (guardrail.title.trim()) {
          await createGuardrail.mutateAsync({
            title: guardrail.title.trim(),
            description: guardrail.description.trim() || undefined,
            ruleType: "must_not",
          });
        }
        await refetchScore();
        setStep(8);
        setSaving(false);
        return;
      }
      setStep((s) => Math.min(s + 1, 8));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore nel salvataggio");
    } finally {
      setSaving(false);
    }
  }

  function handleBack() {
    setStep((s) => Math.max(s - 1, 1));
  }

  return (
    <div className="bi-wizard">
      <div className="bi-wizard__stepper">
        {WIZARD_STEPS.map((s) => (
          <div
            key={s.id}
            className={`bi-wizard__step ${step === s.id ? "bi-wizard__step--active" : ""} ${step > s.id ? "bi-wizard__step--done" : ""}`}
          >
            <span className="bi-wizard__dot">{step > s.id ? "✓" : s.id}</span>
            <span>{s.label}</span>
          </div>
        ))}
      </div>

      <div className="bi-panel">
        {step === 1 && (
          <>
            <h3 className="bi-panel__title">Brand Basics</h3>
            <p className="bi-panel__subtitle">Nome, descrizione e presenza online del brand.</p>
            <div className="bi-form-grid">
              <div className="gcr-field">
                <label>Nome brand *</label>
                <input value={profile.brandName} onChange={(e) => setProfile((p) => ({ ...p, brandName: e.target.value }))} />
              </div>
              <div className="gcr-field">
                <label>Sito web</label>
                <input value={profile.websiteUrl} onChange={(e) => setProfile((p) => ({ ...p, websiteUrl: e.target.value }))} />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Descrizione breve *</label>
                <textarea rows={3} value={profile.shortDescription} onChange={(e) => setProfile((p) => ({ ...p, shortDescription: e.target.value }))} />
              </div>
              <div className="gcr-field">
                <label>Settore</label>
                <input value={profile.industry} onChange={(e) => setProfile((p) => ({ ...p, industry: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h3 className="bi-panel__title">Voice & Tone</h3>
            <p className="bi-panel__subtitle">Come deve suonare il brand nei contenuti AI.</p>
            <div className="bi-form-grid">
              <div className="gcr-field bi-form-grid--full">
                <label>Tono *</label>
                <input value={voice.tone} onChange={(e) => setVoice((v) => ({ ...v, tone: e.target.value }))} placeholder="Es. autentico, premium, accessibile" />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Note di stile</label>
                <textarea rows={3} value={voice.styleNotes} onChange={(e) => setVoice((v) => ({ ...v, styleNotes: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h3 className="bi-panel__title">Products & Categories</h3>
            <p className="bi-panel__subtitle">Aggiungi almeno un prodotto o categoria chiave.</p>
            <div className="bi-form-grid">
              <div className="gcr-field">
                <label>Nome prodotto</label>
                <input value={product.name} onChange={(e) => setProduct((p) => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Descrizione</label>
                <textarea rows={3} value={product.description} onChange={(e) => setProduct((p) => ({ ...p, description: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <h3 className="bi-panel__title">Audience</h3>
            <p className="bi-panel__subtitle">Chi è il tuo cliente ideale?</p>
            <div className="bi-form-grid">
              <div className="gcr-field">
                <label>Nome segmento</label>
                <input value={audience.segmentName} onChange={(e) => setAudience((a) => ({ ...a, segmentName: e.target.value }))} />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Descrizione</label>
                <textarea rows={3} value={audience.description} onChange={(e) => setAudience((a) => ({ ...a, description: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 5 && (
          <>
            <h3 className="bi-panel__title">Claims & Compliance</h3>
            <p className="bi-panel__subtitle">Cosa non deve mai dire il brand?</p>
            <div className="bi-form-grid">
              <div className="gcr-field bi-form-grid--full">
                <label>Claim vietato</label>
                <input value={claim.title} onChange={(e) => setClaim((c) => ({ ...c, title: e.target.value }))} placeholder="Es. Non promettere cure mediche" />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Dettaglio</label>
                <textarea rows={2} value={claim.description} onChange={(e) => setClaim((c) => ({ ...c, description: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 6 && (
          <>
            <h3 className="bi-panel__title">SEO & Content</h3>
            <p className="bi-panel__subtitle">Keyword e primo content pillar.</p>
            <div className="bi-form-grid">
              <div className="gcr-field bi-form-grid--full">
                <label>Keyword primarie (virgola)</label>
                <input value={seo.keywords} onChange={(e) => setSeo((s) => ({ ...s, keywords: e.target.value }))} />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Content pillar</label>
                <input value={seo.pillarName} onChange={(e) => setSeo((s) => ({ ...s, pillarName: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 7 && (
          <>
            <h3 className="bi-panel__title">AI Guardrails</h3>
            <p className="bi-panel__subtitle">Regola che l&apos;AI non deve mai violare.</p>
            <div className="bi-form-grid">
              <div className="gcr-field bi-form-grid--full">
                <label>Guardrail must_not</label>
                <input value={guardrail.title} onChange={(e) => setGuardrail((g) => ({ ...g, title: e.target.value }))} placeholder="Es. Non inventare ingredienti" />
              </div>
              <div className="gcr-field bi-form-grid--full">
                <label>Dettaglio</label>
                <textarea rows={2} value={guardrail.description} onChange={(e) => setGuardrail((g) => ({ ...g, description: e.target.value }))} />
              </div>
            </div>
          </>
        )}

        {step === 8 && score && (
          <div style={{ textAlign: "center" }}>
            <h3 className="bi-panel__title">Profilo brand creato!</h3>
            <p className="bi-panel__subtitle">Il tuo Brand Knowledge Score è pronto.</p>
            <div style={{ display: "flex", justifyContent: "center", margin: "1.5rem 0" }}>
              <BrandScoreRing score={score} />
            </div>
            <button type="button" className="gcr-btn gcr-btn--primary" onClick={onComplete}>
              Vai alla Brand Intelligence
            </button>
          </div>
        )}

        {error && (
          <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
            {error}
          </div>
        )}

        {step < 8 && (
          <div className="bi-wizard__actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              onClick={handleBack}
              disabled={step === 1 || saving}
            >
              Indietro
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              onClick={handleNext}
              disabled={saving}
            >
              {saving ? "Salvataggio…" : step === 7 ? "Completa" : "Avanti"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function useBrandWizard(projectId: string) {
  const [active, setActive] = useState(false);
  return {
    active,
    start: () => setActive(true),
    stop: () => setActive(false),
    projectId,
  };
}
