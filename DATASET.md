# CropCover corpus snapshot

Snapshot: 26 November 2026. The active source list has four official URLs. Three were saved directly; the current PMFBY FAQ page required a browser render because the downloader receives only its JavaScript shell. The rendered FAQ copy is separately registered in `data/manifest.jsonl`.

| Measure | Value | Method |
|---|---:|---|
| Usable source documents | 4 | Operational guidelines, current FAQ, portal FAQ PDF, and latest Nagapattinam notice page |
| PDFs / PDF pages | 2 / 218 | `pypdf` page count |
| HTML pages with extracted text | 2 | Rendered PMFBY FAQ page and Nagapattinam notice page |
| Extracted text | 642,781 characters | `pypdf` plus `trafilatura` |
| Disk size | 3.69 MB (3.52 MiB) | Sum of the four usable files; decimal MB |
| Estimated tokens | 160,695 (~0.161 M) | Character count divided by 4; rough proxy, not a model tokenizer |
| Average estimated tokens per page | 730 | Estimated tokens divided by 220 PDF/HTML pages |

The current operational-guidelines PDF is listed on the [PMFBY Guidelines page](https://pmfby.gov.in/downloads) as “2023 Operational Guidelines”; its downloadable PDF is hosted by the PMFBY platform partner. The current [PMFBY FAQ page](https://pmfby.gov.in/faq) is a JavaScript app: the plain HTTP downloader saved a 6.8 kB shell with zero extractable characters, so the visible page was rendered with headless Chrome and registered with the manual fetch door. The page shell is retained as a retrieval record but excluded from the usable-document totals.

The latest Nagapattinam district PMFBY notice found for this snapshot was published 14 November 2026 and extends Samba/Thaladi enrollment through 1 December 2026. Its linked PDF was blocked by the CDN's `robots.txt`; the official district landing page was downloaded instead. The downloader did not bypass that block.

PMFBY copyright policy and Tamil Nadu district website terms require permission before reproduction. These files are for internal research and source-linked answers only; the corpus is not cleared for displaying reproduced answer text until permissions are confirmed. `data/raw/` is ignored by Git. `data/manifest.jsonl` records retrieval status, provenance, byte count, and SHA-256.

## Duplicate check

This 10-line snippet groups the latest manifest record for each URL by SHA-256 and prints only hashes shared by distinct URLs:

```python
import json
from collections import defaultdict

print("Duplicate SHA-256 groups across URLs:")
rows = [json.loads(line) for line in open("data/manifest.jsonl", encoding="utf-8") if line.strip()]
latest = {row["url"]: row for row in rows if row.get("status") == "downloaded"}
groups = defaultdict(list)
for row in latest.values():
    groups[row["sha256"]].append(row["url"])
for digest, urls in groups.items():
    if len(urls) > 1:
        print(digest, urls)
```

Result for this snapshot: the rendered FAQ has one expected duplicate hash across its canonical page URL and its manual-render fragment URL. It is one document captured once, not a second source file.
