
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
