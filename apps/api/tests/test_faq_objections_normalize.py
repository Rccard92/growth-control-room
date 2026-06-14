"""FAQ & Objections AI output normalization tests."""

from app.schemas.brand_faq_objections import BrandFaqObjectionsProposal
from app.services.brand_intelligence.faq_objections_import import normalize_faq_objections_ai_output


def test_normalize_objections_as_strings() -> None:
    normalized, warnings = normalize_faq_objections_ai_output(
        {"objections": ["prezzo alto", "  ", "non mi fido"]}
    )
    assert normalized["objections"] == ["prezzo alto", "non mi fido"]
    assert warnings == []


def test_normalize_objections_as_objects_splits_recommended() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {
            "objections": [
                {"objection": "Costa troppo", "answer": "Spiega il valore artigianale"},
            ]
        }
    )
    assert normalized["objections"] == ["Costa troppo"]
    assert "Obiezione: Costa troppo" in (normalized["recommended_answers"] or [])[0]
    assert "Risposta consigliata: Spiega il valore artigianale" in (
        normalized["recommended_answers"] or []
    )[0]


def test_normalize_general_faq_as_object() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {"generalFaq": [{"question": "Spedite?", "answer": "Sì, in 48h"}]}
    )
    assert normalized["general_faq"] == ["Domanda: Spedite?\nRisposta: Sì, in 48h"]


def test_normalize_myths_as_object() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {"mythsMisconceptions": [{"myth": "Non è naturale", "correction": "È 100% artigianale"}]}
    )
    assert normalized["myths_misconceptions"] == [
        "Mito: Non è naturale\nCorrezione: È 100% artigianale"
    ]


def test_normalize_snake_case_fields() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {
            "general_faq": ["Domanda: Q?\nRisposta: A"],
            "recommended_answers": ["Risposta consigliata test"],
        }
    )
    assert normalized["general_faq"] == ["Domanda: Q?\nRisposta: A"]
    assert normalized["recommended_answers"] == ["Risposta consigliata test"]


def test_normalize_camel_case_fields() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {
            "productProcessQuestions": [{"question": "Ingredienti?", "answer": "Miele puro"}],
            "contentOpportunities": ["Post blog su spedizioni"],
        }
    )
    assert normalized["product_process_questions"] == [
        "Domanda: Ingredienti?\nRisposta: Miele puro"
    ]
    assert normalized["content_opportunities"] == ["Post blog su spedizioni"]


def test_normalize_filters_empty_and_null_items() -> None:
    normalized, warnings = normalize_faq_objections_ai_output(
        {"objections": [None, "", "  ", "valida"]}
    )
    assert normalized["objections"] == ["valida"]
    assert isinstance(warnings, list)


def test_normalize_output_validates_with_proposal_schema() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {
            "generalFaq": [{"question": "FAQ?", "answer": "Sì"}],
            "objections": [{"objection": "Dubbio", "answer": "Risposta"}],
            "socialCommentInsights": [
                {"insight": "Cliente scettico", "doubt": "Prezzo alto", "suggestedReply": "Valore"}
            ],
            "notes": "Note operative",
        }
    )
    proposal = BrandFaqObjectionsProposal.model_validate(normalized)
    assert proposal.general_faq is not None
    assert proposal.objections == ["Dubbio"]
    assert proposal.recommended_answers is not None
    assert len(proposal.recommended_answers) >= 1
    assert proposal.social_comment_insights is not None
    assert proposal.notes == "Note operative"


def test_normalize_deduplicates_strings() -> None:
    normalized, _ = normalize_faq_objections_ai_output(
        {"objections": ["stesso", "stesso", "altro"]}
    )
    assert normalized["objections"] == ["stesso", "altro"]
