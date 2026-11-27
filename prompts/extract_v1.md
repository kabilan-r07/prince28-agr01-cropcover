You read one document from CropCover's collection and fill in a small record about it.

What CropCover does: Explains crop insurance under PMFBY for Tamil Nadu farmers: what is covered, how to claim within 72 hours, premiums and sum insured.

Rules:
- Reply with one JSON object and nothing else: no explanation, no Markdown fences.
- Use only what the document says. If it does not say, use null for the year and [] for a list.
- summary: one or two plain sentences, at most 300 characters.
- topics: 1 to 6 short topics.
- For each project field, use a short value, a list of up to 8 short values, or null if the document does not say.

What each field means:
- doc_kind: what kind of document this is.
- year: the year it was published or came into force.
- language: the main language of the text (en, ta, hi or other).
- season: every "season" this document is mainly about.
- district: every "district" this document is mainly about.
- crop: every "crop" this document is mainly about.
- sum_insured_per_ha: every "sum insured per ha" this document is mainly about.
- farmer_premium_pct: every "farmer premium pct" this document is mainly about.
- cutoff_date: every "cutoff date" this document is mainly about.
- insurer: every "insurer" this document is mainly about.
