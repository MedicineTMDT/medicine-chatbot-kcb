import pandas as pd
import re

df = pd.read_csv("evaluate/experiments/vigorous_codd.csv")

def extract_metric_value(cell_value):
    if isinstance(cell_value, str) and "value=" in cell_value:
        match = re.search(r"value=([0-9.]+)", cell_value)
        if match:
            return float(match.group(1))
    return cell_value # Nếu nó đã là số sẵn thì để nguyên

metric_columns = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall'] 

for col in metric_columns:
    if col in df.columns:
        df[col] = df[col].apply(extract_metric_value)

print(df[metric_columns].mean())

