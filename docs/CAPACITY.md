# Corpus capacity estimate

This is a planning estimate for the local corpus snapshot in [`DATASET.md`](../DATASET.md), not a report of embeddings already created. CropCover has no configured tokenizer, chunker, or embedding model yet.

| Measure | Estimate | Assumption |
|---|---:|---|
| Average tokens per page | ~391 | 1,153,214 extracted characters / 4 / 737 pages; approximate only |
| Full corpus | ~0.288 M tokens | 1,153,214 characters / 4 |
| Chunks | ~641 | 500-token chunks with 50-token overlap; `ceil((288304 - 50) / (500 - 50))` |
| Embedding input charge | ~₹0.54 | Scenario using OpenAI `text-embedding-3-small` at $0.02 per million input tokens and RBI's 23 Nov 2026 rate of ₹92.7968/USD; excludes tax and any provider-side changes. [Model price](https://developers.openai.com/api/docs/models/text-embedding-3-small) · [RBI exchange rate](https://www.rbi.org.in/home.aspx/Scripts/Home.aspx/Webservice/Scripts/scripts/FS_InterOperableRegSandbox.aspx) |
| Vector storage | ~3.94 MB | 641 vectors × 1,536 dimensions × 4 bytes (float32); excludes database and index overhead |

The four-characters-per-token rule is only a sizing proxy. It can differ substantially from an actual tokenizer, especially for Tamil text, tables, and scanned pages. The vector and price figures must be recalculated when a model, tokenizer, and chunking implementation are selected. No embedding or vector charge has occurred yet.
