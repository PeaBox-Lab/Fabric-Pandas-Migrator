from fabric_pandas_migrator.transformer import transform

def test_pandas_api_import():
    out, _ = transform("import pandas as pd\n", "pandas-api")
    assert "import pyspark.pandas as pd" in out

def test_native_read_write():
    src = 'import pandas as pd\ndf = pd.read_csv("a.csv", sep=",")\ndf.to_parquet("b", index=False)\n'
    out, _ = transform(src, "native")
    assert "SparkSession.builder.getOrCreate" in out
    assert "spark.read.options" in out
    assert '.csv("a.csv")' in out
    assert ".write.mode('overwrite').parquet(\"b\")" in out
    compile(out, "<migrated>", "exec")

def test_shape():
    out, _ = transform("print(df.shape)\n", "native")
    assert "df.count()" in out
