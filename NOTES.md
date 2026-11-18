
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
