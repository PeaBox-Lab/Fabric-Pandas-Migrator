from pathlib import Path
import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider
from .models import Finding, FileResult

RISKY = {
    "iterrows": ("HIGH", "Row iteration does not scale; replace with Spark expressions."),
    "itertuples": ("HIGH", "Driver-side row iteration does not scale."),
    "apply": ("HIGH", "Review apply/lambda logic; prefer Spark SQL functions or a typed pandas UDF."),
    "iloc": ("HIGH", "Positional indexing has no direct distributed equivalent."),
    "loc": ("MEDIUM", "Review label-based selection and assignment semantics."),
    "merge": ("MEDIUM", "Validate join type, duplicate keys, null semantics, and column collisions."),
    "pivot_table": ("MEDIUM", "Review pivot aggregation and resulting schema."),
    "read_excel": ("HIGH", "Excel is not a distributed Spark source; ingest/convert it explicitly."),
    "to_excel": ("HIGH", "Excel output is not a native distributed Spark sink."),
    "plot": ("MEDIUM", "Collect only a bounded result before plotting."),
    "rolling": ("HIGH", "Translate rolling logic to an explicit Spark Window specification."),
    "resample": ("HIGH", "Translate resampling to time bucketing and aggregation."),
}

class UsageVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)
    def __init__(self): self.uses=False; self.findings=[]
    def visit_Import(self, node):
        for a in node.names:
            if isinstance(a.name, cst.Name) and a.name.value == "pandas": self.uses=True
    def visit_ImportFrom(self, node):
        if isinstance(node.module, cst.Name) and node.module.value == "pandas": self.uses=True
    def visit_Attribute(self, node):
        name=node.attr.value
        if name in RISKY:
            sev,msg=RISKY[name]; pos=self.get_metadata(PositionProvider,node)
            self.findings.append(Finding(f"PANDAS_{name.upper()}",sev,msg,pos.start.line))

def scan_file(path: Path) -> FileResult:
    result=FileResult(str(path),False)
    try:
        module=cst.parse_module(path.read_text(encoding="utf-8"))
        visitor=UsageVisitor(); MetadataWrapper(module).visit(visitor)
        result.uses_pandas=visitor.uses
        result.findings=visitor.findings if visitor.uses else []
        result.status="detected" if visitor.uses else "no-pandas"
    except Exception as exc:
        result.status="error"; result.error=str(exc)
    return result

def python_files(root: Path):
    excluded={".git",".venv","venv","build","dist","__pycache__",".tox"}
    return sorted(p for p in root.rglob("*.py") if not any(x in excluded for x in p.parts))
