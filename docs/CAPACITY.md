# Corpus capacity estimate

This is a planning estimate for the local corpus snapshot in [`DATASET.md`](../DATASET.md), not a report of embeddings already created. CropCover has no configured tokenizer, chunker, or embedding model yet.

| Measure | Estimate | Assumption |
|---|---:|---|
| Average tokens per page | ~730 | 642,781 extracted characters / 4 / 220 PDF and HTML pages; approximate only |
| Full corpus | ~0.161 M tokens | 642,781 characters / 4 |
| Chunks | ~357 | 500-token chunks with 50-token overlap; `ceil((160695 - 50) / (500 - 50))` |
| Embedding input charge | ~Rs 0.30 | Scenario using OpenAI `text-embedding-3-small` at $0.02 per million input tokens and the RBI 23 Nov 2026 rate of Rs 92.7968/USD; excludes tax and future provider changes. [Model price](https://developers.openai.com/api/docs/models/text-embedding-3-small) · [RBI exchange rate](https://www.rbi.org.in/home.aspx/Scripts/Home.aspx/Webservice/Scripts/scripts/FS_InterOperableRegSandbox.aspx) |
| Vector storage | ~2.19 MB | 357 vectors × 1,536 dimensions × 4 bytes (float32); excludes database and index overhead |

The four-characters-per-token rule is only a sizing proxy. It can differ substantially from an actual tokenizer, especially for Tamil text, tables, and scanned pages. The vector and price figures must be recalculated when a model, tokenizer, and chunking implementation are selected. No embedding or vector charge has occurred yet.
