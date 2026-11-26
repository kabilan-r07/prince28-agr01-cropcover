"""Extract and validate document metadata; each document commits independently for resume."""

import argparse
import asyncio
import json
import re

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from cropcover.config import get_settings
from cropcover.db.llm_calls import make_recorder
from cropcover.db.models import Document
from cropcover.db.session import make_engine, make_sessionmaker
from cropcover.llm.doc_meta import DocMeta
from cropcover.llm.gateway import LLMUnavailable, build_gateway
from cropcover.llm.prompts import latest, read_prompt


def schema_format() -> dict:
    schema = DocMeta.model_json_schema()
    schema["additionalProperties"] = False
    return {
        "type": "json_schema",
        "json_schema": {"name": "doc_meta", "strict": True, "schema": schema},
    }


def parse_output(reply: str) -> DocMeta:
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        raise ValueError("reply contains no JSON object")
    payload = json.loads(match.group())
    crop_fields = payload.get("CropCover")
    if isinstance(crop_fields, dict):
        if set(payload).intersection(crop_fields):
            raise ValueError("CropCover wrapper duplicates top-level fields")
        payload = {**payload, **crop_fields}
        del payload["CropCover"]
    return DocMeta.model_validate(payload)


def validate_document_claims(meta: DocMeta, text: str) -> None:
    if meta.year is not None and not re.search(rf"(?<!\d){meta.year}(?!\d)", text):
        raise ValueError(f"year {meta.year} is not in the document")
    seasons = {s.lower() for s in ("Kharif", "Rabi", "Special") if re.search(s, text, re.I)}
    if meta.season and len(seasons) > 1:
        meta.season = None


def record_failure(document: Document, reason: str) -> None:
    document.metadata_ = {**document.metadata_, "extraction_error": reason[:300]}


def document_excerpt(pages, max_chars: int = 6000) -> str:
    """Sample pages across the whole source while staying below provider token limits."""
    page_texts = [f"[page {p.page_no}]\n{p.text.strip()}" for p in pages if p.text.strip()]
    combined = "\n\n".join(page_texts)
    if len(combined) <= max_chars:
        return combined
    sample_count = min(len(page_texts), 8)
    if sample_count == 1:
        return page_texts[0][:max_chars]
    chars_each = max(500, max_chars // sample_count)
    indexes = sorted(
        {round(i * (len(page_texts) - 1) / (sample_count - 1)) for i in range(sample_count)}
    )
    selected = [page_texts[i][:chars_each] for i in indexes]
    return "\n\n".join(selected)[:max_chars]


async def extract(args: argparse.Namespace) -> int:
    settings = get_settings()
    engine = make_engine(settings)
    sessions = make_sessionmaker(engine)
    gateway = build_gateway(settings, recorder=make_recorder(sessions))
    prompt_name = latest(settings.prompts_dir, "extract")
    prompt = read_prompt(settings.prompts_dir, prompt_name)
    counts = {"ok": 0, "repaired": 0, "failed": 0}
    interrupted = False
    try:
        async with sessions() as session:
            stmt = (
                select(Document)
                .where(Document.doc_type != "record")
                .options(selectinload(Document.pages))
                .order_by(Document.external_id)
            )
            docs = list(await session.scalars(stmt))
            pending = [d for d in docs if args.retry_failed or d.metadata_.get("doc_kind") is None]
            if args.external_id:
                pending = [d for d in docs if d.external_id == args.external_id]
            if args.limit:
                pending = pending[: args.limit]
            print(f"prompt={prompt_name} documents={len(docs)} pending={len(pending)}")
            for index, doc in enumerate(pending, 1):
                source_text = "\n\n".join(p.text for p in doc.pages)
                text = document_excerpt(doc.pages)
                if not source_text.strip():
                    counts["failed"] += 1
                    record_failure(doc, "empty document text")
                    await session.commit()
                    print(f"FAILED {doc.external_id}: empty document text")
                    continue
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"<document>\n{text}\n</document>"},
                ]
                try:
                    result = await gateway.generate(
                        messages,
                        purpose="extract",
                        prompt_version=prompt_name,
                        temperature=0,
                        max_tokens=1200,
                        **({"response_format": schema_format()} if args.schema else {}),
                    )
                    was_repaired = False
                    try:
                        meta = parse_output(result.text)
                        validate_document_claims(meta, source_text)
                    except (ValueError, ValidationError) as first_error:
                        repair_prompt = (
                            "Return a corrected JSON object matching the requested schema. "
                            "Do not add facts. Invalid reply: " + result.text[:5000]
                        )
                        repaired = await gateway.generate(
                            messages
                            + [
                                {"role": "assistant", "content": result.text},
                                {"role": "user", "content": repair_prompt},
                            ],
                            purpose="extract",
                            prompt_version=prompt_name,
                            temperature=0,
                            max_tokens=1200,
                            **({"response_format": schema_format()} if args.schema else {}),
                        )
                        try:
                            meta = parse_output(repaired.text)
                            validate_document_claims(meta, source_text)
                            was_repaired = True
                            counts["repaired"] += 1
                        except (ValueError, ValidationError) as repair_error:
                            raise first_error from repair_error
                    doc.metadata_ = {**doc.metadata_, **meta.model_dump(mode="json")}
                    doc.metadata_.pop("extraction_error", None)
                    await session.commit()
                    if not was_repaired:
                        counts["ok"] += 1
                    print(f"{index}/{len(pending)} OK {doc.external_id}")
                except (ValueError, ValidationError) as exc:
                    counts["failed"] += 1
                    record_failure(doc, str(exc))
                    await session.commit()
                    print(f"FAILED {doc.external_id}: {exc}")
                except LLMUnavailable as exc:
                    await session.rollback()
                    print(f"stopped: {exc}; progress remains committed and resumable")
                    interrupted = True
                    break
                await asyncio.sleep(60 / max(args.rpm, 1))
    finally:
        await gateway.aclose()
        await engine.dispose()
    print(f"ok={counts['ok']} repaired={counts['repaired']} failed={counts['failed']}")
    return 1 if interrupted else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--rpm", type=int, default=12)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--schema", action="store_true")
    parser.add_argument("--external-id", help="extract one document by external ID")
    return asyncio.run(extract(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
