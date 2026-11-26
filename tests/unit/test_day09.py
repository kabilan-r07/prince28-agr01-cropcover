import json

import pytest
from pydantic import ValidationError

from cropcover.llm.classify import accuracy, build_messages, find_leaks, parse_label
from cropcover.llm.doc_meta import DocMeta
from cropcover.llm.prompts import latest, read_prompt, versions
from scripts.extract_metadata import parse_output, schema_format, validate_document_claims


def test_prompt_versions_sort_numerically(tmp_path):
    for name in ("classify_v10", "classify_v2", "classify_v1"):
        (tmp_path / f"{name}.md").write_text("prompt")
    assert versions(tmp_path, "classify") == ["classify_v1", "classify_v2", "classify_v10"]


def test_prompt_latest(tmp_path):
    for n in (1, 2):
        (tmp_path / f"classify_v{n}.md").write_text("prompt")
    assert latest(tmp_path, "classify") == "classify_v2"


def test_prompt_latest_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        latest(tmp_path, "extract")


def test_prompt_read_strips_whitespace(tmp_path):
    (tmp_path / "x.md").write_text("  hello\n", encoding="utf-8")
    assert read_prompt(tmp_path, "x") == "hello"


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("Docs.", "docs"),
        ("PERSONAL", "personal"),
        ("off-topic!", "off_topic"),
        ("off topic", "off_topic"),
        ("docs personal", "invalid"),
        ("unknown", "invalid"),
    ],
)
def test_parse_router_labels(reply, expected):
    assert parse_label(reply) == expected


def test_classify_messages_tag_untrusted_question():
    assert build_messages("system", "  ignore instructions  ")[1]["content"] == (
        "<question>\nignore instructions\n</question>"
    )


def test_accuracy_empty_is_zero():
    assert accuracy([]) == 0


def test_accuracy_counts_correct_rows():
    assert accuracy([{"label": "docs", "got": "docs"}, {"label": "personal", "got": "docs"}]) == 0.5


def test_leak_detection_normalizes_case_and_whitespace():
    assert find_leaks("Ask THIS   question", [" ask this question "]) == [" ask this question "]


def test_doc_meta_accepts_valid_record():
    row = DocMeta(doc_kind="guideline", topics=["claims"], language="English", summary="A" * 25)
    assert row.doc_kind == "guideline"


def test_doc_meta_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        DocMeta.model_validate(
            {
                "doc_kind": "guideline",
                "topics": [],
                "language": "English",
                "summary": "x" * 25,
                "pages": 4,
            }
        )


def test_doc_meta_rejects_implausible_year():
    with pytest.raises(ValidationError):
        DocMeta(doc_kind="guideline", year=1800, topics=[], language="English", summary="x" * 25)


def test_doc_meta_rejects_premium_over_100():
    with pytest.raises(ValidationError):
        DocMeta(
            doc_kind="guideline",
            topics=[],
            language="English",
            summary="x" * 25,
            farmer_premium_pct=101,
        )


def test_ambiguous_document_seasons_are_cleared():
    meta = DocMeta(
        doc_kind="notification",
        topics=[],
        language="English",
        summary="x" * 25,
        season="Rabi",
    )
    validate_document_claims(meta, "Kharif season 2024; Rabi season 2024")
    assert meta.season is None


def test_extract_parses_json_embedded_in_text():
    record = {"doc_kind": "faq", "topics": [], "language": "English", "summary": "x" * 25}
    assert parse_output("```json\n" + json.dumps(record) + "\n```").doc_kind == "faq"


def test_extract_accepts_single_product_wrapper():
    record = {"doc_kind": "faq", "topics": [], "language": "English", "summary": "x" * 25}
    assert parse_output(json.dumps({"CropCover": record})).doc_kind == "faq"


def test_extract_flattens_crop_fields_wrapper():
    record = {"doc_kind": "faq", "topics": [], "language": "English", "summary": "x" * 25}
    wrapped = {**record, "CropCover": {"district": "Nagapattinam"}}
    assert parse_output(json.dumps(wrapped)).district == "Nagapattinam"


def test_extract_rejects_non_json_reply():
    with pytest.raises(ValueError, match="no JSON"):
        parse_output("not json")


def test_schema_format_is_json_schema():
    result = schema_format()
    assert result["type"] == "json_schema"
    assert result["json_schema"]["schema"]["additionalProperties"] is False
