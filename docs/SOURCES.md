# CropCover sources

Started 26 November 2026. Each row records format and access terms for the current D06 corpus. Links are the publishers' sources; permission is not implied by public access.

| Source | Format / retrieval | Terms and use |
|---|---|---|
| [PMFBY 2023 Operational Guidelines](https://pmfby.gov.in/downloads) | PDF, 213 pages; the PMFBY partner-hosted PDF is in `data/raw/pmfby/`. | PMFBY's [copyright policy](https://pmfby.gov.in/copyrightPolicy) requires prior permission for reproduction. Cite the source; do not reproduce full text without permission. |
| [PMFBY current FAQ](https://pmfby.gov.in/faq) | JavaScript page. Direct fetch is an empty shell; the visible page was rendered to HTML with headless Chrome and registered via `scripts/fetch.py manual`. | Same PMFBY copyright policy. Treat as research/citation material pending permission. |
| [PMFBY FAQ for Portal Login and Registration](https://pmfby.gov.in/pdf/FAQ%E2%80%93For%20Portal.pdf) | PDF, 5 pages; downloaded by `scripts/fetch.py urls`. This is portal-use FAQ material, supplementary to the farmer-facing FAQ page. | PMFBY copyright policy applies; permission is required before reproducing text. |
| [Nagapattinam 2026-27 PMFBY enrollment extension](https://nagapattinam.nic.in/deadline-for-farmers-to-enroll-in-crop-insurance-under-the-pradhan-mantri-fasal-bima-yojana-has-been-extended-until-01-12-2026/) | Official district notice page, HTML. The linked CDN PDF was blocked by `robots.txt`; the downloader used this landing page and did not bypass the block. | District website copyright and any third-party rights apply. Confirm permission before reproducing notice text. |

`data/sources.csv` is the downloader's active URL list. `data/manifest.jsonl` also records the browser-rendered FAQ copy and all retrieval outcomes. Public availability is not a reuse licence; use citations and confirm permissions before answer-text display.
