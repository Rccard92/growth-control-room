from typing import Any

from app.models.seo_optimizer import SeoOptimizationProposal


def _normalize_value(value: Any) -> Any:
    if isinstance(value, list):
        return value
    if value is None:
        return None
    return value


def _values_equal(current: Any, proposed: Any) -> bool:
    return _normalize_value(current) == _normalize_value(proposed)


def build_proposal_preview(proposal: SeoOptimizationProposal) -> dict[str, Any]:
    current = proposal.current_values or {}
    proposed = proposal.proposed_values or {}
    reasoning = proposal.reasoning or []
    reasoning_text = (
        reasoning[0] if isinstance(reasoning, list) and reasoning else str(reasoning or "")
    )

    fields: list[dict[str, Any]] = []
    all_keys = set(current.keys()) | set(proposed.keys())
    for key in sorted(all_keys):
        cur = current.get(key)
        prop = proposed.get(key)
        if prop is None and key not in proposed:
            continue
        changed = not _values_equal(cur, prop)
        fields.append(
            {
                "field": key,
                "current": cur,
                "proposed": prop,
                "changed": changed,
                "reasoning": reasoning_text if changed else None,
                "risk": proposal.risk_level if changed else None,
            }
        )

    changed_fields = [f["field"] for f in fields if f["changed"]]

    return {
        "proposal_id": str(proposal.id),
        "entity_type": proposal.entity_type,
        "entity_id": str(proposal.entity_id),
        "status": proposal.status,
        "source": proposal.source,
        "risk_level": proposal.risk_level,
        "reasoning": proposal.reasoning,
        "fields": fields,
        "changed_fields": changed_fields,
        "current_values": current,
        "proposed_values": proposed,
    }
