from pathlib import Path
import shutil, typer
from rich.console import Console
from .scanner import python_files, scan_file
from .transformer import transform
from .reporting import write_reports

app=typer.Typer(no_args_is_help=True,help="Bulk pandas-to-PySpark migration for Microsoft Fabric.")
console=Console()

@app.command()
def scan(source: Path):
    """Inventory pandas usage without changing files."""
    results=[scan_file(p) for p in python_files(source)]
    for r in results:
        if r.uses_pandas: console.print(f"[yellow]{r.path}[/] findings={len(r.findings)}")
    console.print(f"Scanned {len(results)} files; pandas files: {sum(r.uses_pandas for r in results)}")

@app.command()
def migrate(source: Path, output: Path|None=typer.Option(None), mode: str=typer.Option("native"), in_place: bool=False, dry_run: bool=False, fail_on_review: bool=False):
    """Copy and transform a Python repository."""
    if mode not in {"native","pandas-api"}: raise typer.BadParameter("mode must be native or pandas-api")
    source=source.resolve()
    if in_place: target=source
    else:
        if output is None: raise typer.BadParameter("--output is required unless --in-place is used")
        target=output.resolve()
        if target==source: raise typer.BadParameter("Use --in-place explicitly to overwrite source files")
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source,target,ignore=shutil.ignore_patterns(".git",".venv","venv","__pycache__","build","dist"))
    results=[]
    for path in python_files(source):
        r=scan_file(path); results.append(r)
        if not r.uses_pandas or r.error: continue
        rel=path.relative_to(source); dest=target/rel
        old=path.read_text(encoding="utf-8"); new,extra=transform(old,mode); r.findings.extend(extra)
        r.path=str(rel); r.changed=(new!=old); r.status="would-change" if dry_run and r.changed else ("changed" if r.changed else "unchanged")
        if r.changed and not dry_run:
            if in_place: dest.with_suffix(dest.suffix+".bak").write_text(old,encoding="utf-8")
            dest.write_text(new,encoding="utf-8")
    report_root=target if not dry_run else (output.resolve() if output else source)
    report_root.mkdir(parents=True,exist_ok=True); write_reports(report_root,results)
    reviews=sum(len(r.findings) for r in results)
    console.print(f"Changed {sum(r.changed for r in results)} files; review findings: {reviews}; report: {report_root}")
    if fail_on_review and reviews: raise typer.Exit(2)

@app.command()
def check(source: Path, fail_on_review: bool=True):
    """Scan migrated code and optionally fail CI on findings or remaining pandas imports."""
    results=[scan_file(p) for p in python_files(source)]
    issues=sum(len(r.findings) for r in results)+sum(r.uses_pandas for r in results)
    console.print(f"Outstanding issues: {issues}")
    if fail_on_review and issues: raise typer.Exit(2)

if __name__=="__main__": app()
