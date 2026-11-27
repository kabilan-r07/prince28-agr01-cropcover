"""Validated metadata contract for CropCover documents."""

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

Short = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]

MetadataValue = Short | list[Short] | None

Kind = Literal[
    "guideline",
    "rule",
    "notice",
    "notification",
    "list",
    "report",
    "faq",
    "form",
    "tutorial",
    "reference",
    "other",
]


class DocMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_kind: Kind
    year: int | None = Field(default=None, ge=1950, le=2027)
    language: Literal["en", "ta", "hi", "other"]
    summary: str = Field(min_length=20, max_length=300)
    topics: Annotated[list[Short], Field(min_length=1, max_length=6)]

    season: MetadataValue = None
    district: MetadataValue = None
    crop: MetadataValue = None
    sum_insured_per_ha: MetadataValue = None
    farmer_premium_pct: MetadataValue = None
    cutoff_date: MetadataValue = None
    insurer: MetadataValue = None

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value):
        aliases = {
            "English": "en",
            "Tamil": "ta",
            "Hindi": "hi",
        }
        return aliases.get(value, value)

    @field_validator("topics")
    @classmethod
    def tidy_topics(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(topic.lower() for topic in value))

    @field_validator("farmer_premium_pct")
    @classmethod
    def validate_premium(cls, value):
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item is None:
                continue
            try:
                number = float(item.replace("%", "").strip())
            except (ValueError, AttributeError):
                continue
            if not 0 <= number <= 100:
                raise ValueError("farmer premium percentage must be between 0 and 100")
        return value
