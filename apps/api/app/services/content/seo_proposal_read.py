"""Build API read models for SEO proposals."""

from app.models.seo_optimizer import SeoOptimizationProposal
from app.services.content.seo_proposal_diff import proposal_changed_fields


def proposal_to_read_dict(proposal: SeoOptimizationProposal) -> dict:
    return {
        "id": proposal.id,
        "entity_type": proposal.entity_type,
        "entity_id": proposal.entity_id,
        "entity_gid": proposal.entity_gid,
        "status": proposal.status,
        "source": proposal.source,
        "current_values": proposal.current_values,
        "proposed_values": proposal.proposed_values,
        "reasoning": proposal.reasoning,
        "risk_level": proposal.risk_level,
        "approved_at": proposal.approved_at,
        "applied_at": proposal.applied_at,
        "created_at": proposal.created_at,
        "changed_fields": proposal_changed_fields(
            proposal.current_values,
            proposal.proposed_values,
        ),
    }
