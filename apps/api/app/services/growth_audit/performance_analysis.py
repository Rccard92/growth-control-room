"""Normalize PageSpeed/CrUX payloads and build performance findings/tasks."""

from __future__ import annotations

from typing import Any

AUDIT_IDS = (
    "largest-contentful-paint",
    "cumulative-layout-shift",
    "total-blocking-time",
    "first-contentful-paint",
    "speed-index",
    "interactive",
    "render-blocking-resources",
    "unused-javascript",
    "unused-css-rules",
    "modern-image-formats",
    "uses-optimized-images",
    "offscreen-images",
    "server-response-time",
    "redirects",
)


def _metric_value(audit: dict[str, Any] | None) -> float | None:
    if not audit:
        return None
    numeric = audit.get("numericValue")
    if isinstance(numeric, (int, float)):
        return float(numeric)
    display = audit.get("displayValue")
    if isinstance(display, str):
        cleaned = display.replace("s", "").replace("ms", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _category_score(categories: dict[str, Any], key: str) -> int | None:
    entry = categories.get(key) or {}
    score = entry.get("score")
    if isinstance(score, (int, float)):
        return int(round(score * 100))
    return None


def _extract_audit(lighthouse: dict[str, Any], audit_id: str) -> dict[str, Any] | None:
    audits = lighthouse.get("audits") or {}
    audit = audits.get(audit_id)
    if not isinstance(audit, dict):
        return None
    return {
        "id": audit_id,
        "title": audit.get("title"),
        "score": audit.get("score"),
        "displayValue": audit.get("displayValue"),
        "numericValue": audit.get("numericValue"),
        "description": audit.get("description"),
    }


def normalize_pagespeed_result(raw: dict[str, Any]) -> dict[str, Any]:
    lighthouse = raw.get("lighthouseResult") or {}
    categories = lighthouse.get("categories") or {}
    audits = lighthouse.get("audits") or {}

    performance_score = _category_score(categories, "performance")
    accessibility_score = _category_score(categories, "accessibility")
    best_practices_score = _category_score(categories, "best-practices")
    seo_lighthouse_score = _category_score(categories, "seo")

    lcp_audit = audits.get("largest-contentful-paint")
    cls_audit = audits.get("cumulative-layout-shift")
    tbt_audit = audits.get("total-blocking-time")
    fcp_audit = audits.get("first-contentful-paint")
    speed_index_audit = audits.get("speed-index")
    interactive_audit = audits.get("interactive")

    flagged_audits: list[dict[str, Any]] = []
    for audit_id in AUDIT_IDS:
        audit = audits.get(audit_id)
        if not isinstance(audit, dict):
            continue
        score = audit.get("score")
        if score is None or score < 0.9:
            flagged_audits.append(_extract_audit(lighthouse, audit_id) or {"id": audit_id})

    return {
        "performanceScore": performance_score,
        "accessibilityScore": accessibility_score,
        "bestPracticesScore": best_practices_score,
        "seoLighthouseScore": seo_lighthouse_score,
        "lcp": _metric_value(lcp_audit),
        "cls": _metric_value(cls_audit),
        "tbt": _metric_value(tbt_audit),
        "fcp": _metric_value(fcp_audit),
        "speedIndex": _metric_value(speed_index_audit),
        "interactive": _metric_value(interactive_audit),
        "audits": flagged_audits,
    }


def _crux_percentile(metric: dict[str, Any] | None) -> float | None:
    if not metric:
        return None
    percentiles = metric.get("percentiles") or {}
    p75 = percentiles.get("p75")
    if isinstance(p75, (int, float)):
        return float(p75)
    return None


def _crux_rating(metric: dict[str, Any] | None) -> str | None:
    if not metric:
        return None
    histogram = metric.get("histogram") or []
    if not histogram:
        return None
    ratings = ("good", "needs_improvement", "poor")
    best_idx = 0
    best_density = -1.0
    for idx, bucket in enumerate(histogram[:3]):
        density = bucket.get("density", 0)
        if isinstance(density, (int, float)) and density > best_density:
            best_density = float(density)
            best_idx = idx
    return ratings[best_idx] if best_idx < len(ratings) else None


def normalize_crux_result(raw: dict[str, Any] | None) -> dict[str, Any]:
    if raw is None:
        return {
            "source": "missing",
            "lcpP75": None,
            "clsP75": None,
            "inpP75": None,
            "fcpP75": None,
            "ttfbP75": None,
            "ratings": {},
            "formFactor": None,
            "collectionPeriod": None,
        }

    record = raw.get("record") or {}
    metrics = record.get("metrics") or {}
    collection_period = record.get("collectionPeriod")

    lcp_metric = metrics.get("largest_contentful_paint") or metrics.get("largest_contentful_paint_ms")
    cls_metric = metrics.get("cumulative_layout_shift")
    inp_metric = metrics.get("interaction_to_next_paint") or metrics.get("experimental_interaction_to_next_paint")
    fcp_metric = metrics.get("first_contentful_paint") or metrics.get("first_contentful_paint_ms")
    ttfb_metric = metrics.get("experimental_time_to_first_byte") or metrics.get("time_to_first_byte")

    cls_p75 = _crux_percentile(cls_metric)
    if cls_p75 is not None and cls_p75 > 1:
        cls_p75 = cls_p75 / 100

    return {
        "source": raw.get("_cruxSource", "url"),
        "lcpP75": _crux_percentile(lcp_metric),
        "clsP75": cls_p75,
        "inpP75": _crux_percentile(inp_metric),
        "fcpP75": _crux_percentile(fcp_metric),
        "ttfbP75": _crux_percentile(ttfb_metric),
        "ratings": {
            "lcp": _crux_rating(lcp_metric),
            "cls": _crux_rating(cls_metric),
            "inp": _crux_rating(inp_metric),
            "fcp": _crux_rating(fcp_metric),
            "ttfb": _crux_rating(ttfb_metric),
        },
        "formFactor": (record.get("key") or {}).get("formFactor"),
        "collectionPeriod": collection_period,
    }


def _severity_for_lcp_ms(value: float | None) -> str | None:
    if value is None:
        return None
    if value > 4000:
        return "high"
    if value > 2500:
        return "medium"
    return None


def _severity_for_cls(value: float | None) -> str | None:
    if value is None:
        return None
    if value > 0.25:
        return "high"
    if value > 0.1:
        return "medium"
    return None


def _severity_for_inp_ms(value: float | None) -> str | None:
    if value is None:
        return None
    if value > 500:
        return "high"
    if value > 200:
        return "medium"
    return None


def _severity_for_tbt_ms(value: float | None) -> str | None:
    if value is None:
        return None
    if value > 600:
        return "high"
    if value > 300:
        return "medium"
    return None


def build_performance_findings(
    normalized_pagespeed: dict[str, Any],
    normalized_crux: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    lcp = normalized_crux.get("lcpP75") or normalized_pagespeed.get("lcp")
    cls = normalized_crux.get("clsP75") or normalized_pagespeed.get("cls")
    inp = normalized_crux.get("inpP75")
    tbt = normalized_pagespeed.get("tbt")

    lcp_severity = _severity_for_lcp_ms(lcp)
    if lcp_severity:
        findings.append(
            {
                "category": "performance",
                "severity": lcp_severity,
                "priority": lcp_severity,
                "title": "LCP elevato",
                "description": "Il Largest Contentful Paint supera le soglie consigliate.",
                "evidence": f"LCP: {lcp}ms",
                "recommendation": "Ottimizza immagini hero, server response e risorse above the fold.",
                "howToValidate": "Riesegui PageSpeed o verifica CrUX dopo il deploy.",
                "impact": "high",
                "effort": "medium",
            }
        )

    cls_severity = _severity_for_cls(cls)
    if cls_severity:
        findings.append(
            {
                "category": "performance",
                "severity": cls_severity,
                "priority": cls_severity,
                "title": "CLS elevato",
                "description": "Il layout shift impatta l'esperienza mobile.",
                "evidence": f"CLS: {cls}",
                "recommendation": "Riserva spazio per immagini/font e evita inserimenti dinamici above the fold.",
                "howToValidate": "Verifica layout shift su mobile in PageSpeed.",
                "impact": "high",
                "effort": "medium",
            }
        )

    inp_severity = _severity_for_inp_ms(inp)
    if inp_severity:
        findings.append(
            {
                "category": "performance",
                "severity": inp_severity,
                "priority": inp_severity,
                "title": "INP elevato",
                "description": "L'interattività real-user risulta lenta.",
                "evidence": f"INP p75: {inp}ms",
                "recommendation": "Riduci JavaScript lungo e migliora handler di input.",
                "howToValidate": "Controlla CrUX dopo ottimizzazioni JS.",
                "impact": "high",
                "effort": "medium",
            }
        )

    tbt_severity = _severity_for_tbt_ms(tbt)
    if tbt_severity:
        findings.append(
            {
                "category": "performance",
                "severity": tbt_severity,
                "priority": tbt_severity,
                "title": "Total Blocking Time alto",
                "description": "Il main thread resta bloccato troppo a lungo.",
                "evidence": f"TBT: {tbt}ms",
                "recommendation": "Suddividi task JS, rimuovi codice inutilizzato e posticipa script non critici.",
                "howToValidate": "Riesegui PageSpeed e verifica TBT in Lighthouse.",
                "impact": "medium",
                "effort": "medium",
            }
        )

    audit_titles = {
        "render-blocking-resources": "Risorse render-blocking",
        "unused-javascript": "JavaScript inutilizzato",
        "unused-css-rules": "CSS inutilizzato",
        "modern-image-formats": "Formati immagine non moderni",
        "uses-optimized-images": "Immagini non ottimizzate",
        "offscreen-images": "Immagini offscreen non differite",
        "server-response-time": "Server response lento",
        "redirects": "Redirect multipli",
    }

    for audit in normalized_pagespeed.get("audits") or []:
        audit_id = audit.get("id")
        if audit_id not in audit_titles:
            continue
        score = audit.get("score")
        if score is not None and score >= 0.9:
            continue
        findings.append(
            {
                "category": "performance",
                "severity": "medium",
                "priority": "medium",
                "title": audit_titles[audit_id],
                "description": audit.get("description") or audit.get("title") or audit_titles[audit_id],
                "evidence": audit.get("displayValue"),
                "recommendation": f"Risolvi l'audit Lighthouse: {audit.get('title') or audit_id}.",
                "howToValidate": "Riesegui PageSpeed dopo la correzione.",
                "impact": "medium",
                "effort": "medium",
            }
        )

    if normalized_pagespeed.get("performanceScore") is not None and normalized_pagespeed["performanceScore"] < 50:
        findings.append(
            {
                "category": "performance",
                "severity": "high",
                "priority": "high",
                "title": "Performance Score basso",
                "description": "Il punteggio Lighthouse performance è sotto la soglia critica.",
                "evidence": f"Score: {normalized_pagespeed['performanceScore']}",
                "recommendation": "Prioritizza LCP, TBT e risorse render-blocking.",
                "howToValidate": "Riesegui analisi performance dopo gli interventi.",
                "impact": "high",
                "effort": "high",
            }
        )

    return findings


def build_performance_tasks(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    titles = {finding.get("title") for finding in findings}

    if "LCP elevato" in titles:
        tasks.append(
            {
                "title": "Ottimizza immagini above the fold",
                "description": "Comprimi e servi formati moderni per l'elemento LCP.",
                "ownerType": "dev",
                "priority": "high",
                "estimatedEffort": "medium",
            }
        )
    if "Risorse render-blocking" in titles:
        tasks.append(
            {
                "title": "Riduci risorse render-blocking",
                "description": "Differisci CSS/JS non critici e inline solo ciò che serve al first paint.",
                "ownerType": "dev",
                "priority": "high",
                "estimatedEffort": "medium",
            }
        )
    if "JavaScript inutilizzato" in titles:
        tasks.append(
            {
                "title": "Rimuovi JavaScript inutilizzato",
                "description": "Elimina bundle non usati e splitta codice per route prioritarie.",
                "ownerType": "dev",
                "priority": "medium",
                "estimatedEffort": "medium",
            }
        )
    if "CSS inutilizzato" in titles:
        tasks.append(
            {
                "title": "Riduci CSS inutilizzato",
                "description": "Purge CSS non usato e carica fogli di stile per sezione.",
                "ownerType": "design",
                "priority": "medium",
                "estimatedEffort": "medium",
            }
        )
    if "CLS elevato" in titles:
        tasks.append(
            {
                "title": "Verifica layout shift su mobile",
                "description": "Riserva dimensioni per media e banner dinamici.",
                "ownerType": "design",
                "priority": "high",
                "estimatedEffort": "low",
            }
        )
    if "Server response lento" in titles:
        tasks.append(
            {
                "title": "Migliora TTFB e caching server",
                "description": "Ottimizza cache, CDN e risposta HTML iniziale.",
                "ownerType": "dev",
                "priority": "high",
                "estimatedEffort": "medium",
            }
        )
    if "Formati immagine non moderni" in titles or "Immagini non ottimizzate" in titles:
        tasks.append(
            {
                "title": "Converti immagini prioritarie in WebP/AVIF",
                "description": "Aggiorna asset hero e gallery con dimensioni responsive.",
                "ownerType": "content",
                "priority": "medium",
                "estimatedEffort": "low",
            }
        )

    if not tasks and findings:
        tasks.append(
            {
                "title": "Rivedi problemi performance individuati",
                "description": "Affronta i finding performance aperti in ordine di priorità.",
                "ownerType": "seo",
                "priority": "medium",
                "estimatedEffort": "medium",
            }
        )

    return tasks
