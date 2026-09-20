import pandas as pd

df = pd.read_csv("input.csv", sep=",")
print(df.head(5))
df.to_parquet("output.parquet", index=False)
