# Conversion rules and review boundaries

## Automatically converted

The native mode intentionally handles only deterministic patterns. It replaces common readers, writers, `head(n)`, and `shape`, removes the pandas import, and inserts a `SparkSession` bootstrap.

## Manual migration patterns

- Replace `axis=1` row lambdas with `pyspark.sql.functions` expressions.
- Replace `groupby(...).apply(...)` with aggregations, window functions, or typed pandas UDFs.
- Replace `iloc` with explicit keys and window-generated row numbers only when ordering is defined.
- Replace index-dependent joins with explicit join keys.
- Replace object dtype assumptions with an explicit `StructType` schema.
- Replace local files with Lakehouse Files, Tables, OneLake ABFS paths, or Fabric connections.
- Prefer Delta tables for governed production data.
- Do not call `toPandas()` on unbounded data. Aggregate or limit first.

## Validation gates

For every migrated job compare: schema and nullable flags; total and distinct row counts; primary-key duplicates; null counts; numeric sums/min/max; timestamp timezone behavior; join cardinality; output partitions; and representative business reconciliations.
