import pandas as pd

sales = pd.read_csv("sales.csv", sep=",")
recent = sales.head(10)
recent.to_parquet("recent_sales", index=False)
print(recent.shape)
