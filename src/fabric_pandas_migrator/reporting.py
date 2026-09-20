from pathlib import Path
import csv, json

def write_reports(root: Path, results):
    data=[r.dict() for r in results]
    (root/"migration-report.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    with (root/"migration-report.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["path","uses_pandas","changed","status","finding_count","error"])
        w.writeheader()
        for r in results: w.writerow({"path":r.path,"uses_pandas":r.uses_pandas,"changed":r.changed,"status":r.status,"finding_count":len(r.findings),"error":r.error or ""})
    changed=sum(r.changed for r in results); reviews=sum(len(r.findings) for r in results)
    lines=["# Migration report","",f"- Files scanned: {len(results)}",f"- Files changed: {changed}",f"- Review findings: {reviews}","","## Findings",""]
    for r in results:
        for x in r.findings: lines.append(f"- **{x.severity}** `{r.path}:{x.line or '?'} {x.code}`: {x.message}")
    (root/"MIGRATION_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
