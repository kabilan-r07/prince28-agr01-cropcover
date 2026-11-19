
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
