
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
