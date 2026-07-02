import { motion } from "framer-motion";
import type { SeoSkillCatalogItem } from "@gcr/shared";
import { SeoAuditPresetCard } from "./SeoAuditPresetCard";
import { getPrimaryAuditPresets } from "./seo-skill-presets";
import { resolvePresetSkills } from "./seo-skills-utils";

interface SeoAuditPresetPickerProps {
  catalog: SeoSkillCatalogItem[];
  selectedKey: string;
  onSelect: (key: string) => void;
  compact?: boolean;
}

export function SeoAuditPresetPicker({
  catalog,
  selectedKey,
  onSelect,
  compact = false,
}: SeoAuditPresetPickerProps) {
  const presets = getPrimaryAuditPresets();

  return (
    <section
      className={`seo-audit-presets ${compact ? "seo-audit-presets--compact" : ""}`}
      aria-label="Tipi di audit"
    >
      <header className="seo-audit-presets__header">
        <h2 className="seo-audit-presets__title">
          {compact ? "Cambia tipo di audit" : "Scegli il tipo di audit"}
        </h2>
        {!compact && (
          <p className="seo-audit-presets__subtitle">
            Ogni preset combina più controlli SEO in un flusso guidato.
          </p>
        )}
      </header>

      <div className="seo-audit-presets__grid">
        {presets.map((preset, index) => {
          const resolved = resolvePresetSkills(preset, catalog);
          return (
            <motion.div
              key={preset.key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.04 }}
            >
              <SeoAuditPresetCard
                preset={preset}
                selected={selectedKey === preset.key}
                availableSkillCount={resolved.availableKeys.length}
                totalSkillCount={
                  preset.key === "custom" ? 0 : preset.includedSkills.length
                }
                onSelect={onSelect}
              />
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
