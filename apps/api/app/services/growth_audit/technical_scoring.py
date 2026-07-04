"""Deterministic technical scoring for Growth Audit page scans."""

from __future__ import annotations

from typing import Any


def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _finding(
    *,
    category: str,
    severity: str,
    priority: str,
    title: str,
    description: str,
    evidence: str,
    recommendation: str,
    how_to_validate: str,
    impact: str,
    effort: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "priority": priority,
        "title": title,
        "description": description,
        "evidence": evidence,
        "recommendation": recommendation,
        "howToValidate": how_to_validate,
        "impact": impact,
        "effort": effort,
    }


def _task(
    *,
    title: str,
    description: str,
    owner_type: str,
    priority: str,
    estimated_effort: str,
) -> dict[str, str]:
    return {
        "title": title,
        "description": description,
        "ownerType": owner_type,
        "priority": priority,
        "estimatedEffort": estimated_effort,
    }


def score_technical_scan(scan: dict, page_type: str) -> tuple[int, list[dict], list[dict]]:
    score = 100
    findings: list[dict] = []
    tasks: list[dict] = []

    http_status = scan.get("httpStatus")
    title = scan.get("title")
    title_length = scan.get("titleLength", 0)
    meta_description = scan.get("metaDescription")
    meta_description_length = scan.get("metaDescriptionLength", 0)
    canonical_url = scan.get("canonicalUrl")
    h1_count = scan.get("h1Count", 0)
    robots = scan.get("robots") or {}
    schema = scan.get("schema") or {}
    schema_types = schema.get("types") or []
    open_graph = scan.get("openGraph") or {}
    images = scan.get("images") or {}
    missing_alt = images.get("missingAlt", 0)
    checks = dict(scan.get("checks") or {})

    canonical_same_domain = checks.get("canonicalSameDomain", False)

    if http_status is None or not (200 <= http_status < 300):
        score -= 35
        findings.append(
            _finding(
                category="technical",
                severity="critical",
                priority="high",
                title="HTTP status non OK",
                description="La pagina non risponde con uno status HTTP 2xx.",
                evidence=f"HTTP status: {http_status}",
                recommendation="Verifica che la pagina sia raggiungibile e restituisca 200.",
                how_to_validate="Apri l'URL e controlla lo status nella scheda Network.",
                impact="high",
                effort="medium",
            )
        )
        tasks.append(
            _task(
                title="Correggere HTTP status pagina",
                description=f"La pagina risponde con status {http_status}. Ripristina risposta 200.",
                owner_type="dev",
                priority="high",
                estimated_effort="medium",
            )
        )

    if not title:
        score -= 15
        findings.append(
            _finding(
                category="seo",
                severity="high",
                priority="high",
                title="Title mancante",
                description="La pagina non ha un tag title.",
                evidence="Nessun <title> rilevato.",
                recommendation="Aggiungi un title descrittivo e unico di 30-65 caratteri.",
                how_to_validate="Ispeziona il sorgente HTML e verifica il tag <title>.",
                impact="high",
                effort="low",
            )
        )
        tasks.append(
            _task(
                title="Aggiungere title pagina",
                description="Scrivi un title unico e descrittivo di 30-65 caratteri.",
                owner_type="seo",
                priority="high",
                estimated_effort="low",
            )
        )
    elif title_length < 30 or title_length > 65:
        score -= 6
        findings.append(
            _finding(
                category="seo",
                severity="medium",
                priority="medium",
                title="Lunghezza title non ottimale",
                description="Il title è fuori dal range indicativo 30-65 caratteri.",
                evidence=f"Title length: {title_length}",
                recommendation="Riscrivi il title tra 30 e 65 caratteri.",
                how_to_validate="Conta i caratteri del title in SERP preview o nel sorgente.",
                impact="medium",
                effort="low",
            )
        )

    meta_severity = "high" if page_type in ("product", "homepage") else "medium"
    if not meta_description:
        score -= 14
        findings.append(
            _finding(
                category="seo",
                severity=meta_severity,
                priority="high" if meta_severity == "high" else "medium",
                title="Meta description mancante",
                description="La pagina non ha meta description.",
                evidence="Nessun meta name=description rilevato.",
                recommendation="Scrivi una meta description orientata al click, 80-165 caratteri.",
                how_to_validate="Verifica meta description nel sorgente o in strumenti SEO.",
                impact="high" if meta_severity == "high" else "medium",
                effort="low",
            )
        )
        tasks.append(
            _task(
                title="Aggiungere meta description",
                description="Scrivi una meta description di 80-165 caratteri orientata al click.",
                owner_type="content",
                priority="high" if meta_severity == "high" else "medium",
                estimated_effort="low",
            )
        )
    elif meta_description_length < 80 or meta_description_length > 165:
        score -= 6
        findings.append(
            _finding(
                category="seo",
                severity="low",
                priority="low",
                title="Lunghezza meta description non ottimale",
                description="La meta description è fuori dal range indicativo 80-165 caratteri.",
                evidence=f"Meta description length: {meta_description_length}",
                recommendation="Riscrivi la meta description tra 80 e 165 caratteri.",
                how_to_validate="Conta i caratteri della meta description.",
                impact="low",
                effort="low",
            )
        )

    if h1_count == 0:
        score -= 10
        findings.append(
            _finding(
                category="seo",
                severity="high",
                priority="high",
                title="H1 mancante",
                description="La pagina non ha un heading H1.",
                evidence="Nessun <h1> rilevato.",
                recommendation="Aggiungi un H1 unico che descriva il contenuto principale.",
                how_to_validate="Verifica presenza di un solo H1 nel DOM.",
                impact="high",
                effort="low",
            )
        )
        tasks.append(
            _task(
                title="Aggiungere H1 pagina",
                description="Inserisci un H1 unico e descrittivo.",
                owner_type="content",
                priority="high",
                estimated_effort="low",
            )
        )
    elif h1_count > 1:
        score -= 5
        findings.append(
            _finding(
                category="seo",
                severity="medium",
                priority="medium",
                title="Più H1 presenti",
                description="La pagina ha più di un H1.",
                evidence=f"H1 count: {h1_count}",
                recommendation="Mantieni un solo H1 principale per pagina.",
                how_to_validate="Conta gli elementi h1 nel DOM.",
                impact="medium",
                effort="low",
            )
        )

    if not canonical_url:
        score -= 8
        findings.append(
            _finding(
                category="seo",
                severity="medium",
                priority="medium",
                title="Canonical mancante",
                description="La pagina non ha link rel=canonical.",
                evidence="Nessun canonical rilevato.",
                recommendation="Aggiungi un canonical che punti all'URL preferito.",
                how_to_validate="Verifica link rel=canonical nel sorgente.",
                impact="medium",
                effort="low",
            )
        )
    elif not canonical_same_domain:
        score -= 12
        findings.append(
            _finding(
                category="seo",
                severity="high",
                priority="high",
                title="Canonical fuori dominio",
                description="Il canonical punta a un dominio diverso.",
                evidence=f"Canonical: {canonical_url}",
                recommendation="Allinea il canonical al dominio principale del sito.",
                how_to_validate="Confronta hostname canonical e dominio root.",
                impact="high",
                effort="medium",
            )
        )

    if robots.get("noindex"):
        noindex_severity = "high" if page_type in ("cart", "checkout") else "critical"
        score -= 25
        findings.append(
            _finding(
                category="seo",
                severity=noindex_severity,
                priority="high",
                title="Noindex presente",
                description="La pagina ha meta robots noindex.",
                evidence=f"Robots: {robots.get('raw', 'noindex')}",
                recommendation="Verifica se la pagina deve essere indicizzabile. Se sì, rimuovi noindex.",
                how_to_validate="Controlla meta robots e header X-Robots-Tag.",
                impact="high",
                effort="low",
            )
        )
        tasks.append(
            _task(
                title="Verificare noindex",
                description="Rimuovi noindex se la pagina deve essere indicizzata.",
                owner_type="seo",
                priority="high",
                estimated_effort="low",
            )
        )

    if schema.get("jsonLdCount", 0) == 0:
        score -= 8
        findings.append(
            _finding(
                category="schema",
                severity="medium",
                priority="medium",
                title="JSON-LD mancante",
                description="Nessuno schema JSON-LD rilevato.",
                evidence="jsonLdCount: 0",
                recommendation="Aggiungi JSON-LD coerente con il tipo di pagina.",
                how_to_validate="Cerca script type=application/ld+json nel sorgente.",
                impact="medium",
                effort="medium",
            )
        )

    if page_type == "product" and "Product" not in schema_types:
        score -= 12
        findings.append(
            _finding(
                category="schema",
                severity="high",
                priority="high",
                title="Product schema mancante",
                description="Pagina prodotto senza schema Product.",
                evidence=f"Schema types: {', '.join(schema_types) or 'nessuno'}",
                recommendation=(
                    "Aggiungi JSON-LD Product coerente con dati visibili: "
                    "nome, immagine, prezzo, disponibilità, brand."
                ),
                how_to_validate="Valida lo schema con Rich Results Test.",
                impact="high",
                effort="medium",
            )
        )
        tasks.append(
            _task(
                title="Aggiungere Product schema",
                description="Implementa JSON-LD Product con dati prodotto visibili.",
                owner_type="dev",
                priority="high",
                estimated_effort="medium",
            )
        )

    if page_type == "collection" and not any(
        t in schema_types for t in ("BreadcrumbList", "ItemList")
    ):
        score -= 8
        findings.append(
            _finding(
                category="schema",
                severity="medium",
                priority="medium",
                title="Schema collezione mancante",
                description="Pagina collezione senza BreadcrumbList o ItemList.",
                evidence=f"Schema types: {', '.join(schema_types) or 'nessuno'}",
                recommendation="Aggiungi BreadcrumbList o ItemList per la collezione.",
                how_to_validate="Valida lo schema con Rich Results Test.",
                impact="medium",
                effort="medium",
            )
        )

    if missing_alt > 0:
        alt_penalty = min(8, missing_alt)
        score -= alt_penalty
        img_severity = "medium" if missing_alt >= 3 else "low"
        findings.append(
            _finding(
                category="images",
                severity=img_severity,
                priority="medium" if img_severity == "medium" else "low",
                title="Immagini senza alt",
                description="Alcune immagini non hanno attributo alt.",
                evidence=f"Immagini senza alt: {missing_alt} su {images.get('total', 0)}",
                recommendation="Aggiungi alt descrittivi e utili, non keyword stuffing.",
                how_to_validate="Ispeziona tag img e verifica attributo alt.",
                impact="medium" if img_severity == "medium" else "low",
                effort="low",
            )
        )
        tasks.append(
            _task(
                title="Aggiungere alt alle immagini",
                description=f"Aggiungi alt descrittivi a {missing_alt} immagini.",
                owner_type="content",
                priority="medium",
                estimated_effort="low",
            )
        )

    has_og = bool(
        open_graph.get("title") or open_graph.get("description") or open_graph.get("image")
    )
    if not has_og:
        score -= 4
        findings.append(
            _finding(
                category="seo",
                severity="low",
                priority="low",
                title="Open Graph mancante",
                description="Tag Open Graph incompleti o assenti.",
                evidence="og:title, og:description o og:image non rilevati.",
                recommendation="Aggiungi og:title, og:description e og:image.",
                how_to_validate="Verifica meta property og:* nel sorgente.",
                impact="low",
                effort="low",
            )
        )

    final_score = _clamp_score(score)
    scan["score"] = final_score
    scan["findings"] = findings
    scan["tasks"] = tasks
    return final_score, findings, tasks
