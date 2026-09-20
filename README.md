# Fabric Pandas Migrator

A GitHub-ready, review-first codemod for bulk migration of Python files that use **pandas** toward **PySpark** workloads in Microsoft Fabric.

## Why review-first?

Pandas and PySpark have different execution models. No codemod can safely infer every schema, index assumption, Python UDF, ordering dependency, or data source credential. This tool therefore:

1. discovers every `.py` file,
2. detects pandas usage,
3. copies the repository to a separate output directory by default,
4. applies deterministic conversions,
5. adds a Fabric Spark bootstrap where needed,
6. produces JSON, CSV, and Markdown reports,
7. flags unsupported or risky patterns for manual review,
8. optionally fails CI when unresolved findings remain.

## Migration modes

### `pandas-api` (recommended first pass)
Changes `import pandas as pd` to `import pyspark.pandas as pd`. This preserves much of the pandas-shaped API while moving execution to Spark. It is the quickest route for compatible analytics code, but unsupported APIs and index semantics still require validation.

### `native`
Converts a conservative set of common patterns to native PySpark DataFrame code:

- `pd.read_csv(path, ...)` -> `spark.read.options(...).csv(path)`
- `pd.read_parquet(path)` -> `spark.read.parquet(path)`
- `pd.read_json(path, ...)` -> `spark.read.options(...).json(path)`
- `df.to_parquet(path, index=False)` -> `df.write.mode("overwrite").parquet(path)`
- `df.to_csv(path, index=False)` -> `df.write.mode("overwrite").option("header", True).csv(path)`
- `df.head(n)` -> `df.limit(n)`
- `df.shape` -> `(df.count(), len(df.columns))`

Everything else is retained and reported for review.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e .

fabric-pandas-migrate scan ./legacy-app
fabric-pandas-migrate migrate ./legacy-app --output ./fabric-app --mode native
fabric-pandas-migrate check ./fabric-app --fail-on-review
```

Dry run:

```bash
fabric-pandas-migrate migrate ./legacy-app --output ./fabric-app --mode native --dry-run
```

In-place migration requires an explicit flag and creates `.bak` files:

```bash
fabric-pandas-migrate migrate ./legacy-app --mode pandas-api --in-place
```

## Output

The output root contains:

- transformed source files,
- `migration-report.json`,
- `migration-report.csv`,
- `MIGRATION_REPORT.md`.

Exit codes: `0` success, `1` operational error, `2` unresolved review findings when `--fail-on-review` is used.

## Microsoft Fabric deployment

1. Create a Fabric Lakehouse and a Notebook or Spark Job Definition.
2. Attach the Lakehouse to the notebook/job.
3. Upload migrated modules as notebook resources, or build a wheel with `python -m build` and add it to a Fabric Environment.
4. Prefer OneLake/Lakehouse paths and Delta tables over local paths.
5. Run the migrated workload against representative data.
6. Compare row counts, schemas, null counts, aggregates, and business outputs with the pandas baseline.
7. Resolve every `REVIEW` item before production scheduling.

See [docs/FABRIC_DEPLOYMENT.md](docs/FABRIC_DEPLOYMENT.md) and [docs/RULES.md](docs/RULES.md).

## CI

A GitHub Actions workflow runs tests and scans the repository. Adapt the migration command to point to your application folder.

## Safety

- Default behavior never overwrites the source tree.
- Generated code is formatted by LibCST and remains parseable.
- The tool never executes source files.
- Dynamic imports, aliases other than common `pd`, `.apply(axis=1)`, `.iterrows()`, `.iloc`, `.loc`, Excel I/O, SQL connections, plotting, and index-heavy logic are reported.

## License

MIT. See [LICENSE](LICENSE).
