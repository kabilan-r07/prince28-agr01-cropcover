
## Idempotent Loader Test Results

### Test 1 – First Run (Insert 20 Records)

```text
records=20 inserted=20 updated=0 unchanged=0
```

Result: Successfully inserted 20 new records.

### Test 2 – Second Run (No Changes)

```text
records=20 inserted=0 updated=0 unchanged=20
```

Result: Detected all 20 records as unchanged. No duplicates created.

### Test 3 – Update One Record

```text
records=20 inserted=0 updated=1 unchanged=19
```

Result: Successfully updated one modified record and skipped 19 unchanged records.

# Engineering notes: CropCover

## D03 · PostgreSQL

### Migrations (upgrade, downgrade, upgrade)

```text
paste the output of:
uv run alembic downgrade -1
uv run alembic current
uv run alembic upgrade head
uv run alembic history
```

### The loader is idempotent

```text
run 1: paste here
run 2: paste here
run 3 (after editing one record): paste here
```

### EXPLAIN for ?season=VALUE

```text
paste the output of: uv run python scripts/explain.py season VALUE
```

Why did the planner choose a Seq Scan on my table? (2 lines, your own words)

When would it switch to the GIN index? (1 line)


### Migrations (upgrade, downgrade, upgrade)

```text
Downgrade:
705bf1db39f3 -> e4897ad68ecd
add gin index on metadata

Current:
e4897ad68ecd

Upgrade:
e4897ad68ecd -> 705bf1db39f3
add gin index on metadata

History:
e4897ad68ecd -> 705bf1db39f3 (head), add gin index on metadata
<base> -> e4897ad68ecd, create documents and pages
```

## D04 · Docker

```text
First build: about 38 seconds
Rebuild after changing one source line: 7.6 seconds
The dependency-only uv sync layer was CACHED on rebuild.
Image disk usage: 300 MB (under the 400 MB target).
Container identity: uid=999(app) gid=999(app) groups=999(app)
```

## D05 · Compose

```text
First migration/seed: records=20 inserted=20 updated=0 unchanged=0
GET /health with Postgres stopped: {"status":"ok","app":"cropcover","env":"local"}
GET /ready with Postgres stopped: {"status":"not_ready","checks":{"database":false}}
GET /ready after Postgres restart: {"status":"ready","checks":{"database":true}}
Second migration/seed after compose down/up: records=20 inserted=0 updated=0 unchanged=20
Final services: db and redis healthy; api healthy; migrate exited (0)
Initial Compose test database: test (owner app); integration base database: app_test (owner app)
```

## D04 · Docker, Compose and tests

### The image

```text
IMAGE           ID             DISK USAGE   CONTENT SIZE
cropcover:dev   0df71ec51a4f        300MB           70MB
uid=999(app) gid=999(app) groups=999(app)
```

- Size: 300 MB (target: under 400 MB)
- First build: about 38 s. After changing one line of code: 7.6 s.
- The dependency-only `uv sync --locked --no-install-project --no-dev` step was `CACHED`; it only depends on the lockfile and project metadata, which did not change.

### The stack

```text
NAME                  SERVICE   STATUS
cropcover-api-1       api       Up (healthy)
cropcover-db-1        db        Up (healthy)
cropcover-migrate-1   migrate   Exited (0)
cropcover-redis-1     redis     Up (healthy)

First migrate log: records=20 inserted=20 updated=0 unchanged=0
After down + up:   records=20 inserted=0 updated=0 unchanged=20
```

### Breaking the database on purpose

```text
db stopped:  /health -> {"status":"ok","app":"cropcover","env":"local"}
db stopped:  /ready  -> {"status":"not_ready","checks":{"database":false}}
db started:  /ready  -> {"status":"ready","checks":{"database":true}}
```

A load balancer should stop sending traffic while readiness is false because the API cannot serve database-backed requests. The process is alive, so restarting it would not fix the stopped database.

### Tests and coverage

```text
uv run poe test              -> 16 passed in 0.44s
uv run poe test-integration  -> 7 passed in 2.44s (second run also passed: 7)
coverage TOTAL, unit only    -> TOTAL 254 36 26 2 83%
coverage TOTAL, with integration tests -> TOTAL 254 9 26 3 96%
```

`src/cropcover/api/deps.py:38-39` is the database-error readiness branch; it matters because readiness must fail on database errors.
`src/cropcover/api/middleware.py:23-25` is the unhandled-error response path; it matters for returning a consistent 500 response with a request ID.



## D05 · CI/CD and going live

- Live URL: https://cropcover.onrender.com
- CI run for pull request 1: https://github.com/kabilan-r07/prince28-agr01-cropcover/actions/runs/44699540404
- First deploy that ran by itself: https://github.com/kabilan-r07/prince28-agr01-cropcover/actions/runs/44702916046
- Merge clicked at 1:59 PM → "Smoke test passed" at 2:00 PM → lead time: 1 min

### Smoke test output from that CD run

Run:
`uv run python scripts/smoke.py "https://cropcover.onrender.com" --expect-version "${SHA}"`

```text
ok version ed98c578d0ae13f71a684d1a9c6b97aadb3e98e2; database ready; documents serving

Smoke test passed
```

### Rollback drill

- Rolled back to SHA `ed98c578d0ae13f71a684d1a9c6b97aadb3e98e2`: started **6:28 PM**, smoke passed **approximately 6:31 PM** (approximately 3 min).
- Rolled forward to SHA `7fbd906fc978aab41a2b8651576b97a1aeb7bbd50`: deployment version matched; final smoke test confirmation and duration pending.

During the rollback, the database stayed on the newer schema. Why is that safe here?

The newer database schema is backward-compatible with the older application version. No destructive database changes were made during rollback.

### Where my secrets live

- Neon string: GitHub Secret DATABASE_URL + Render environment. Not in Git, not in the image.
- Render deploy hook: GitHub Secret RENDER_DEPLOY_HOOK only.

### Monitoring

- UptimeRobot checks /health every 5 minutes; alerts go to my email.
- One thing that would make my live app faster on its first request: Using an always-on Render instance prevents cold starts.

## D06 - Collecting the corpus

- Start target: Operational guidelines + FAQs + latest Tamil Nadu notification.
- Collected today: 10 files, 737 pages, 71.90 MB (from `DATASET.md`). The current corpus is older than the full start target; it contains earlier guidelines and 2024-26 Tamil Nadu tender annexures.
- Doors used: URL list.

### Crawl numbers

- 10 unique downloaded URLs: PMFBY 3 files / 63.29 MB; Tamil Nadu Agrisnet 7 files / 8.61 MB (decimal MB, latest manifest record per URL).
- Slowest site cannot be determined for this historical run: the manifest has fetch timestamps but no per-response duration. New HTTP downloads now record `elapsed_seconds` for future comparisons.
- 0 of 10 unique files needed more than one attempt; every latest downloaded record says `attempts: 1`.

### Licence check

| Source | Licence or terms, in my words | May I show full text in answers? |
|---|---|---|
| PMFBY | Copyright policy requires prior permission for reproduction and prominent source acknowledgement. | No, until permission is granted. |
| Tamil Nadu Agrisnet | Copyright notice is present; I did not find a clear reuse grant or terms page. | Not confirmed; do not display full text until clarified. |
| Coimbatore District (candidate 2026-27 notice) | Copyright policy requires permission by email; third-party material can require separate permission. | No, until permission is granted. |

### robots.txt

- PMFBY: `https://pmfby.gov.in/robots.txt` returned HTTP 200 with homepage HTML, not usable robots directives.
- Tamil Nadu Agrisnet: `https://www.tnagrisnet.tn.gov.in/robots.txt` returned 404; no robots rules were published at that URL.
- Blocked for this bot: 0 sources in the final successful run. This is only the fetcher's robots result; it does not establish copyright permission.

### Kill and resume

- Run 1: Ctrl+C after 6 completed files; the expected `Stopped. Run the same command again: finished files are skipped.` message appeared.
- Run 2: downloaded=4, skipped=6.
- Run 3: downloaded=0, skipped=10.
- Deleted one PDF and reran: only that file returned (`downloaded=1`, `skipped=9`). No `.part` files remained.

### Capacity

- Tokens per page, measured estimate: ~391, using extracted characters divided by four (not a model tokenizer).
- Full corpus: ~0.288 M estimated tokens, ~641 assumed 500-token chunks with 50-token overlap, embedding scenario ~₹0.54, vectors ~3.94 MB. Assumptions and limits are in [`docs/CAPACITY.md`](docs/CAPACITY.md).
- The number that surprised me most: the YES-TECH manual is 61.7 MB, about 86% of the corpus bytes, despite being 116 pages. Its embedded PDF assets make file size a poor proxy for text volume.

### One thing that went wrong today, and how I fixed it

Six initial links returned JavaScript shell pages rather than documents. I inspected file signatures, replaced those entries with direct PDF links, removed the shell files, and verified the final ten local files are PDFs. Current-target candidates and their permission requirements are noted above; they have not been added or downloaded.

## D07 - Parser comparison

| File | Parser A (pages/chars) | Parser B (pages/chars) | Better and why |
|---|---:|---:|---|
| `data\raw\pmfby\yes-tech-manual-2023-09c72587.pdf` | PyMuPDF: 116/101563 | pypdf: 116/88781 | _review_ |
| `data\raw\tnagrisnet\9-02ffba92.pdf` | PyMuPDF: ParseError: no_text_layer: 393 characters on 178 pages: needs OCR | pypdf: 178/263404 | _review_ |
| `data\raw\tnagrisnet\7-c913d110.pdf` | PyMuPDF: ParseError: no_text_layer: 94 characters on 173 pages: needs OCR | pypdf: 173/129139 | _review_ |
| `data\raw\tnagrisnet\1-01f7218f.pdf` | PyMuPDF: 56/95460 | pypdf: 56/92905 | _review_ |
| `data\raw\pmfby\revised-operational-guidelines-53ba6b34.pdf` | PyMuPDF: 99/271074 | pypdf: 99/256199 | _review_ |
| `data\raw\tnagrisnet\3-080e8e63.pdf` | PyMuPDF: 11/30275 | pypdf: 11/22892 | _review_ |
| `data\raw\pmfby\rwbcis-revised-guidelines-1-1a893711.pdf` | PyMuPDF: 19/37766 | pypdf: 19/36323 | _review_ |
| `data\raw\tnagrisnet\4-8d7afd1a.pdf` | PyMuPDF: 36/136658 | pypdf: 36/132171 | _review_ |
| `data\raw\tnagrisnet\5-22729f04.pdf` | PyMuPDF: ParseError: no_text_layer: 0 characters on 11 pages: needs OCR | pypdf: 11/22988 | _review_ |
| `data\raw\tnagrisnet\2-c87bf560.pdf` | PyMuPDF: 38/96258 | pypdf: 38/82582 | PyMuPDF (+13,676 chars; 15 tables) |

### D07 - Parsing my corpus

- Files in manifest: 10 | parsed: 10 | failed: 0 | pages in Postgres: 737
- Parsing coverage: 100% of files (10 / 10)

#### Failures by reason

| Reason | Files | What I did |
|---|---:|---|
| no_text_layer (initial run) | 3 | PyMuPDF rejected `tnagrisnet/5.pdf`, `7.pdf`, and `9.pdf`; pypdf extracted their text on retry and the failure rows were cleared. |

- The one I fixed: `tnagrisnet/5.pdf`, reason `no_text_layer`; added pypdf fallback after PyMuPDF rejects the text layer, then retried all three affected files successfully.

#### What I saw when I read my parsed pages

- A page where the heading path is right: `OPERATIONAL GUIDELINES`, page 3, `['Index']`.
- Something that came out wrong: `Document Control Sheet`, page 3, has a private-use glyph in ?Classification?; its pages 1-2 are blank in both parsers.
- A table: `OPERATIONAL GUIDELINES`, page 2, rendered as a Markdown grid.

#### My parser choice

- For PDFs, PyMuPDF is the default: it found more characters on all 7 PDFs it accepted and recovered Markdown tables/headings. When it reported `no_text_layer`, pypdf recovered all 3 files (11, 173, and 178 pages).
- A kind of document neither parser handles well: PDFs with blank front pages and non-Unicode/private-use glyphs; those still need source-level checking.

- One thing that went wrong today, and how I fixed it: PyMuPDF treated three readable Tamil Nadu annexures as scans. I compared pypdf independently, added a fallback, and reran them; all 10 documents now have pages in Postgres.

### D08 · LLM gateway

- Primary: `gemini-3.8-flash` (Gemini) · fallback: `openai/gpt-oss-20b` (Groq)
- Gateway, streaming `/v1/chat`, `/v1/usage`, call logging, migration, prompt, and CLI client implemented.
- Verification: 78 unit tests pass; Ruff check and format pass. The `llm_calls` migration is applied to the configured database at revision `4d950cb419ab`.
- Provider ping: Groq returned `pong`; Gemini first returned HTTP 503 and later HTTP 401 `invalid_api_key`. No model answer or real-call token/cost measurements were collected because Gemini rejected the configured key.
- First laptop question (after restoring the intended Gemini primary URL): first words after 5.28 s, total 5.70 s, tokens in 258 / out 280, cost Rs 0.009818; Groq answered after Gemini returned HTTP 503.
- Fallback/breaker: Groq answered after three Gemini 404s with `gemini-no-such-model`; Gemini was skipped on the fourth request while its circuit was open.
- `/v1/usage` today: 19 calls, 9 errors, 10 fallbacks, Rs 0.0922 total (includes the earlier misconfigured call and breaker exercise).
- Token experiment: `Hi` 239 tokens in; English CropCover question 254; Tamil translation 269. Excluding the shared prompt, Tamil used 30 tokens vs English's 15 (about 2x). Tamil characters rendered as `?` in this PowerShell console, but the request reached the model.
- Groundedness miss: asked “When will my claim money be credited?” The model claimed within 72 hours after submitting a form. The 72-hour rule is for reporting a crop loss after the peril, not a promise that payment will arrive then. The guidelines describe payment timing separately (including 15 days after the loss survey report for specified claims, subject to subsidy conditions). [Official revised guidelines](https://pmfby.gov.in/pdf/Revised_Operational_Guidelines.pdf).
- On the premium-share question it said it was unsure rather than giving the known cap: up to 2% of sum insured for Kharif food-grain/oilseed crops and 1.5% for Rabi (or actuarial rate if lower). [Official revised guidelines](https://pmfby.gov.in/pdf/Revised_Operational_Guidelines.pdf).
- Off-topic: asked who won the 2011 Cricket World Cup; the model declined in one sentence. Live URL result: pending merge/deploy. Gemini's key is set, but the provider returned HTTP 503 during laptop chats; the earlier ping also returned HTTP 401 once, so verify the key and provider status again before deployment.
- One thing that went wrong today: `.env` still pointed the Gemini primary at Groq after a provider-switch experiment. Removed only the two primary model/URL overrides; keys were preserved. Then proved fallback and circuit opening using a temporary invalid model in the server process.

## P01 / D06 / D08 recheck - 26 November 2026

### D06 - Current source corpus

- Replaced the old PMFBY and 2024-26 tender-annexure URL list with the current PMFBY 2023 Operational Guidelines, current PMFBY FAQ page, its portal FAQ PDF, and the latest Nagapattinam PMFBY enrollment-extension notice found for this snapshot.
- `scripts/fetch.py urls`: first pass downloaded the guideline, portal FAQ, and FAQ page shell; the CDN PDF linked by the district notice was blocked by `robots.txt`. Replaced that direct PDF URL with the official Nagapattinam landing page and reran: one downloaded, three skipped, zero blocked/failed. The downloader never bypassed robots rules.
- The PMFBY FAQ page is a JavaScript app. Its ordinary download had zero extractable text, so I rendered the visible page with headless Chrome and registered the copy through the manual door. Extracted text: 5,966 characters. The original shell remains marked in the manifest but is excluded from usable corpus totals.
- The current guideline PDF has 213 pages and 624,698 extracted characters. The portal FAQ PDF has 5 pages and 9,823 characters. The Nagapattinam notice page has 2,294 extracted characters. Current usable corpus: 4 documents, 220 PDF/HTML pages, 642,781 characters, 3.69 MB. See `DATASET.md` and `docs/CAPACITY.md`.
- The district notice was published 14 November 2026 and extends Samba/Thaladi enrollment to 1 December 2026. PMFBY copyright policy requires permission for reproduction; district terms also require permission. Documents are for internal research and cited answers only until permissions are confirmed.
- Current sources and formats are listed in `docs/SOURCES.md`. The parsed Postgres corpus was not changed in this D06 collection pass; this records source acquisition and measurements.

### D08 - Live usage and chat verification

- GitHub merged PR #9 at commit `3ec4de9f36cefe5cadae34ce7ec4f0c7f46e4d0a`; Render reports that same version live. The CD workflow's normal deployment runs `alembic upgrade head` using the GitHub `DATABASE_URL` secret before deploying.
- `GET https://cropcover.onrender.com/health`: HTTP 200, version `3ec4de9f36cefe5cadae34ce7ec4f0c7f46e4d0a`.
- `GET https://cropcover.onrender.com/v1/usage`: HTTP 200; the database returned recorded calls, confirming the usage table is available. At the check, it reported 28 calls and Rs 0.1276 total across 25-26 November.
- Two live `POST /v1/chat` checks returned HTTP 200. Gemini answered the first (186 input / 6 output tokens, Rs 0.01539); Groq answered the second after Gemini failed over (250 input / 59 output tokens, Rs 0.003463). The follow-up usage response reported 7 calls for 26 November, Rs 0.0253 that day, and 28 calls total.
- The earlier 503 is resolved at this snapshot. The two malformed test payloads returned 422 and were not counted as provider calls.

### P01 - Week 1 self-check

- Added `scripts/check_week1.py` from the supplied P01 material. It checks D01-D05 files, git state, unit tests, and the live `/health` version when run with the live URL.
- Added `docs/SOURCES.md` with one row per current source, its format, terms, and retrieval method.

## Prompt Comparison Results

| Prompt Version | Correct Answers | Total Questions | Accuracy |
|---|---:|---:|---:|
| classify_v1 | 11 | 20 | 55% |
| classify_v2 | 17 | 20 | 85% |
| classify_v3 | 20 | 20 | 100% |

Best performing version: classify_v3
Model calls made: 7 (remaining results from cache).

Metadata extraction observation:
Gemini API returned HTTP 429 due to quota limits.
Only 1 document was extracted successfully; remaining documents are pending.
The extraction script can be rerun after quota becomes available.

### D09 · Prompts and structured output

- My best router prompt: classify_v3 with 20 / 20
- What I changed in v4, and what happened to the score: v4 was not created or tested.
- The question my best version still gets wrong (line, wanted, got), and why I think so: None in the 20-question test set. classify_v3 scored 20/20.
- A label in my test set that I changed after seeing the results (or "none"): Not recorded.
- Input tokens per question: v1 Not measured, best version Not measured. Is the extra accuracy worth it? Yes, based on the improvement from 11/20 to 20/20.
- What I changed in v4, and what happened to the score: classify_v4.md was removed from the final prompt set. Its score and exact changes are not confirmed.

### My contract (DocMeta)

- Fields I kept from my project card: season, district, crop, sum_insured_per_ha, farmer_premium_pct, cutoff_date, insurer.
- Fields I deleted, and why they make no sense per document: Not recorded.
- The field I tightened, and how: topics — restricted to 1–6 items using Pydantic Field(min_length=1, max_length=6).

### Extraction run

- Prompt version: extract_v3 · documents: 10 ok, 1 repaired, 0 failed (of 10 parsed).
- Not finished? Why, and how many are left: The latest extraction run reported pending=2, and both were processed successfully. No remaining failed documents were reported.
- Most common failure reason, and what I did about it: "the reply contains no JSON object". The extraction script repaired the response successfully.
- A record that was valid but wrong (document, field, what it said, what is true): Not identified yet.
- Cost at list price: Rs 0.1584 for the latest run (2 documents); total cost and cost per document for all 10 documents not confirmed.

### One thing that went wrong today, and how I fixed it

One document returned a response without a JSON object. The extraction script repaired it, and the final run reported 0 failed documents.
