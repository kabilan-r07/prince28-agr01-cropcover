"""Validated, document-level facts extracted for CropCover."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DocMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    doc_kind: Annotated[str, Field(min_length=2, max_length=40)]
    year: int | None = Field(default=None, ge=1900, le=2100)
    topics: list[Annotated[str, Field(min_length=2, max_length=60)]] = Field(max_length=12)
    language: Annotated[str, Field(min_length=2, max_length=30)]
    summary: Annotated[str, Field(min_length=20, max_length=800)]
    season: str | None = Field(default=None, max_length=40)
    district: str | None = Field(default=None, max_length=80)
    crop: str | None = Field(default=None, max_length=80)
    sum_insured_per_ha: float | None = Field(default=None, gt=0)
    farmer_premium_pct: float | None = Field(default=None, ge=0, le=100)
    cutoff_date: date | None = None
    insurer: str | None = Field(default=None, max_length=120)
