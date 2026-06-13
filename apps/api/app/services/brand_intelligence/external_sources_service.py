"""Brand external sources lifecycle for import batches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand_intelligence import BrandExternalSource, BrandImportBatch
from app.schemas.brand_intelligence import BrandExternalSourceInput, BrandExternalSourceRead
from app.services.brand_intelligence.source_fetcher import (
    INACCESSIBLE_MESSAGE,
    fetch_url_content,
)

VALID_SOURCE_TYPES = frozenset(
    {
        "website",
        "instagram",
        "facebook",
        "tiktok",
        "youtube",
        "linkedin",
        "trustpilot",
        "google_business",
        "other",
    }
)

TERMINAL_BATCH_FOR_ADD = frozenset({"review_ready", "partially_failed", "completed", "pending", "uploading", "extracting", "ai_processing"})


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL vuoto.")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"URL non valido: {url}")
    return url


def _dedupe_key(source_type: str, url: str) -> tuple[str, str]:
    return (source_type, normalize_url(url).rstrip("/").lower())


def build_sources_from_form(
    *,
    website_url: str | None,
    sources: list[BrandExternalSourceInput],
) -> list[BrandExternalSourceInput]:
    """Merge explicit website + typed social/review URLs into source inputs."""
    out: list[BrandExternalSourceInput] = []
    seen: set[tuple[str, str]] = set()

    def add(item: BrandExternalSourceInput) -> None:
        key = _dedupe_key(item.source_type, item.url)
        if key in seen:
            return
        seen.add(key)
        out.append(
            BrandExternalSourceInput(
                source_type=item.source_type,
                url=normalize_url(item.url),
                label=item.label,
            )
        )

    if website_url and website_url.strip():
        add(BrandExternalSourceInput(source_type="website", url=website_url.strip()))

    for src in sources:
        if not src.url or not src.url.strip():
            continue
        st = src.source_type if src.source_type in VALID_SOURCE_TYPES else "other"
        add(BrandExternalSourceInput(source_type=st, url=src.url.strip(), label=src.label))

    return out


async def create_external_sources_for_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
    sources: list[BrandExternalSourceInput],
) -> list[BrandExternalSource]:
    created: list[BrandExternalSource] = []
    seen: set[tuple[str, str]] = set()
    for item in sources:
        key = _dedupe_key(item.source_type, item.url)
        if key in seen:
            continue
        seen.add(key)
        row = BrandExternalSource(
            project_id=project_id,
            batch_id=batch_id,
            source_type=item.source_type,
            label=item.label,
            url=normalize_url(item.url),
            status="pending",
        )
        session.add(row)
        created.append(row)
    if created:
        await session.flush()
    return created


async def list_external_sources_for_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
) -> list[BrandExternalSource]:
    return list(
        (
            await session.execute(
                select(BrandExternalSource)
                .where(
                    BrandExternalSource.project_id == project_id,
                    BrandExternalSource.batch_id == batch_id,
                )
                .order_by(BrandExternalSource.created_at.asc())
            )
        ).scalars().all()
    )


async def _get_batch(session: AsyncSession, project_id: UUID, batch_id: UUID) -> BrandImportBatch:
    batch = (
        await session.execute(
            select(BrandImportBatch).where(
                BrandImportBatch.id == batch_id,
                BrandImportBatch.project_id == project_id,
            )
        )
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch non trovato.")
    return batch


def validate_batch_input(
    *,
    brand_name: str | None,
    website_url: str | None,
    files_count: int,
    sources_count: int,
) -> None:
    has_brand = bool(brand_name and brand_name.strip())
    has_website = bool(website_url and website_url.strip())
    has_files = files_count > 0
    has_sources = sources_count > 0
    if not (has_brand or has_website or has_files or has_sources):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inserisci almeno il nome brand, il sito web o un file da caricare.",
        )


async def add_external_sources_to_batch(
    session: AsyncSession,
    project_id: UUID,
    batch_id: UUID,
    sources: list[BrandExternalSourceInput],
) -> list[BrandExternalSourceRead]:
    batch = await _get_batch(session, project_id, batch_id)
    if batch.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile aggiungere fonti a un batch fallito.",
        )
    rows = await create_external_sources_for_batch(session, project_id, batch_id, sources)
    await session.commit()
    return [BrandExternalSourceRead.model_validate(r) for r in rows]


async def fetch_batch_external_sources(
    session: AsyncSession,
    batch_id: UUID,
    *,
    refetch_failed: bool = False,
) -> tuple[list[str], int]:
    """Fetch all pending (or failed/skipped if refetch) sources. Returns warnings, fetched count."""
    batch = (
        await session.execute(
            select(BrandImportBatch).where(BrandImportBatch.id == batch_id)
        )
    ).scalar_one_or_none()
    if not batch:
        return [], 0

    statuses = ["pending"]
    if refetch_failed:
        statuses.extend(["failed", "skipped"])

    sources = list(
        (
            await session.execute(
                select(BrandExternalSource).where(
                    BrandExternalSource.batch_id == batch_id,
                    BrandExternalSource.status.in_(statuses),
                )
            )
        ).scalars().all()
    )

    warnings: list[str] = []
    fetched_count = 0
    now = datetime.now(timezone.utc)

    for idx, source in enumerate(sources):
        source.status = "fetching"
        await session.commit()

        step_label = _progress_step_for_source(source.source_type, idx, len(sources))
        batch.current_step = step_label
        if len(sources) > 1:
            pct = 35 + int((idx / len(sources)) * 15)
            batch.progress_percent = pct
        await session.commit()

        result = await fetch_url_content(source.source_type, source.url)
        source.status = result["status"]
        source.fetched_title = result.get("fetched_title")
        source.fetched_text = result.get("fetched_text")
        source.fetched_summary = result.get("fetched_summary")
        source.fetch_error = result.get("fetch_error")
        source.last_fetched_at = now

        if result["status"] == "fetched":
            fetched_count += 1
        elif result["status"] in ("failed", "skipped"):
            msg = f"{source.source_type} ({source.url}): {result.get('fetch_error') or INACCESSIBLE_MESSAGE}"
            warnings.append(msg)

        await session.commit()

    if warnings:
        existing = list(batch.warnings or [])
        for w in warnings:
            if w not in existing:
                existing.append(w)
        batch.warnings = existing
        await session.commit()

    return warnings, fetched_count


def _progress_step_for_source(source_type: str, idx: int, total: int) -> str:
    if source_type == "website":
        return "Sto analizzando il sito web"
    if source_type in ("trustpilot", "google_business"):
        return "Sto leggendo fonti recensioni"
    if source_type in ("instagram", "facebook", "tiktok", "youtube", "linkedin"):
        return f"Sto integrando fonti esterne ({idx + 1} di {total})"
    return f"Recupero fonti esterne ({idx + 1} di {total})"


def parse_sources_json(raw: str | None) -> list[BrandExternalSourceInput]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sources JSON non valido: {exc}",
        ) from exc
    if not isinstance(data, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sources deve essere un array.")
    out: list[BrandExternalSourceInput] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        st = str(item.get("sourceType") or item.get("source_type") or "other")
        if st not in VALID_SOURCE_TYPES:
            st = "other"
        out.append(
            BrandExternalSourceInput(
                source_type=st,
                url=url,
                label=item.get("label"),
            )
        )
    return out
