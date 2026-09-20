# Deploy to Microsoft Fabric

## Notebook route

1. Create a Fabric workspace backed by Fabric capacity.
2. Create a Lakehouse and a Notebook with PySpark as the primary language.
3. Attach the Lakehouse.
4. Upload migrated modules to notebook resources or paste the entry point into cells.
5. Replace local paths with Lakehouse Tables/Files paths.
6. Run reconciliation tests on sampled and full-scale data.
7. Schedule the notebook only after all migration findings are closed.

## Spark Job Definition route

Use a Spark Job Definition for modular Python applications and production scheduling. Upload the application entry file and dependencies, attach an Environment, configure arguments, then run and monitor it.

## Package route

Build a wheel:

```bash
pip install build
python -m build
```

Upload the wheel to a Fabric Environment. Use a stable published Environment for scheduled production workloads.

## Recommended release sequence

- assessment and inventory,
- automated first pass in a feature branch,
- code review,
- unit tests locally,
- Fabric development workspace validation,
- parallel reconciliation against pandas,
- performance tuning and partition review,
- controlled production cutover with rollback retained.
