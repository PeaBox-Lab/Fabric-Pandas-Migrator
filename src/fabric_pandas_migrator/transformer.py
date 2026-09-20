import libcst as cst
from .models import Finding

class PandasApiTransformer(cst.CSTTransformer):
    def leave_Import(self, original, updated):
        names=[]
        for a in updated.names:
            if isinstance(a.name,cst.Name) and a.name.value=="pandas":
                names.append(a.with_changes(name=cst.parse_expression("pyspark.pandas")))
            else: names.append(a)
        return updated.with_changes(names=names)
    def leave_ImportFrom(self, original, updated):
        if isinstance(updated.module,cst.Name) and updated.module.value=="pandas":
            return updated.with_changes(module=cst.parse_expression("pyspark.pandas"))
        return updated

class NativeTransformer(cst.CSTTransformer):
    def __init__(self): self.needs_spark=False; self.findings=[]
    def leave_Import(self, original, updated):
        kept=[]
        for a in updated.names:
            if isinstance(a.name,cst.Name) and a.name.value=="pandas": self.needs_spark=True
            else: kept.append(a)
        if not kept: return cst.RemoveFromParent()
        return updated.with_changes(names=kept)
    def leave_SimpleStatementLine(self, original, updated):
        if not updated.body: return cst.RemoveFromParent()
        return updated
    def leave_Call(self, original, updated):
        fn=updated.func
        if isinstance(fn,cst.Attribute):
            method=fn.attr.value
            if isinstance(fn.value,cst.Name) and fn.value.value in {"pd","pandas"} and method in {"read_csv","read_parquet","read_json"}:
                self.needs_spark=True
                if not updated.args: return updated
                path=updated.args[0].value
                if method=="read_parquet":
                    return cst.Call(cst.parse_expression("spark.read.parquet"),[cst.Arg(path)])
                options=[]
                for arg in updated.args[1:]:
                    if arg.keyword:
                        key=arg.keyword.value
                        mapped={"sep":"sep","delimiter":"sep","header":"header","encoding":"encoding","quotechar":"quote","escapechar":"escape"}.get(key)
                        if mapped: options.append(cst.Arg(arg.value,keyword=cst.Name(mapped)))
                        else: self.findings.append(Finding("UNSUPPORTED_READ_OPTION","MEDIUM",f"Review unsupported {method} option: {key}"))
                reader="spark.read.options"
                chain=cst.Call(cst.parse_expression(reader),options)
                target="csv" if method=="read_csv" else "json"
                return cst.Call(cst.Attribute(chain,cst.Name(target)),[cst.Arg(path)])
            if method in {"to_parquet","to_csv"} and updated.args:
                self.needs_spark=True; path=updated.args[0].value
                base=fn.value
                if method=="to_parquet": expr=f"{cst.Module([]).code_for_node(base)}.write.mode('overwrite').parquet"
                else: expr=f"{cst.Module([]).code_for_node(base)}.write.mode('overwrite').option('header', True).csv"
                return cst.Call(cst.parse_expression(expr),[cst.Arg(path)])
            if method=="head" and updated.args:
                return updated.with_changes(func=fn.with_changes(attr=cst.Name("limit")))
        return updated
    def leave_Attribute(self, original, updated):
        if updated.attr.value=="shape":
            obj=cst.Module([]).code_for_node(updated.value)
            return cst.parse_expression(f"({obj}.count(), len({obj}.columns))")
        return updated

def add_spark_bootstrap(module: cst.Module) -> cst.Module:
    code=module.code
    if "SparkSession" in code or "spark =" in code: return module
    header=cst.parse_module("from pyspark.sql import SparkSession\n\nspark = SparkSession.builder.getOrCreate()\n\n")
    return module.with_changes(body=tuple(header.body)+tuple(module.body))

def transform(code: str, mode: str):
    module=cst.parse_module(code)
    if mode=="pandas-api":
        out=module.visit(PandasApiTransformer()); return out.code, []
    tx=NativeTransformer(); out=module.visit(tx)
    if tx.needs_spark: out=add_spark_bootstrap(out)
    return out.code, tx.findings
