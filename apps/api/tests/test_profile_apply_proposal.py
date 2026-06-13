"""Apply proposal schema tests."""

from app.schemas.brand_profile_v1 import BrandProfileApplyProposalRequest, BrandProfileProposal


def test_apply_proposal_request_accepts_proposal() -> None:
    req = BrandProfileApplyProposalRequest(
        proposal=BrandProfileProposal(
            brandName="Acme",
            shortDescription="Desc",
            values=["v1"],
        ),
        confidence=0.8,
        warnings=["instagram: blocked"],
    )
    assert req.proposal.brand_name == "Acme"
    assert req.confidence == 0.8


def test_proposal_coerces_null_lists() -> None:
    p = BrandProfileProposal.model_validate({"values": None, "differentiators": None})
    assert p.values == []
    assert p.differentiators == []
