# CropCover corpus snapshot

Snapshot: 23 November 2026. The downloader's URL list currently resolves to ten local PDF files under `data/raw/`.

| Measure | Value | Method |
|---|---:|---|
| Files | 10 | Files under `data/raw/` |
| PDF pages | 737 | `pypdf` page count |
| Disk size | 71.90 MB (68.56 MiB) | Sum of file sizes; MB is decimal |
| Extracted text | 1,153,214 characters | `pypdf` text extraction across pages |
| Estimated tokens | 288,304 (~0.288 M) | Character count divided by 4; rough proxy, not a model tokenizer |
| Average estimated tokens per page | 391 | Estimated tokens divided by page count |

The current files include older PMFBY guidelines and Tamil Nadu tender annexures. They do not yet meet the requested target of current operational guidelines, usable FAQs, and the latest Tamil Nadu crop notification. Candidate current links and access findings are recorded in `NOTES.md`. The PMFBY copyright policy requires permission before reproduction; the Tamil Nadu district notice policy also requires permission. Do not treat the corpus as cleared for answer-text display until the applicable permissions or licences are confirmed.

`data/raw/` is ignored by Git. `data/manifest.jsonl` records retrieval status, provenance, byte count, and SHA-256 for the downloaded files.
