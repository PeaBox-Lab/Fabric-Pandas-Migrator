from dataclasses import asdict, dataclass, field

@dataclass
class Finding:
    code: str
    severity: str
    message: str
    line: int | None = None

@dataclass
class FileResult:
    path: str
    uses_pandas: bool
    changed: bool = False
    status: str = "skipped"
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None

    def dict(self):
        return asdict(self)
