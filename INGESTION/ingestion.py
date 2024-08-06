from function import creating_index_body, scoring_embedder, ingestion_data_to_elastic
from datetime import datetime
import pandas as pd

dataframe = pd.read_csv("../EXTRACTION/thai_leave_policy_chunks.csv")

index_name = "hr-policy-index"
creating_index_body(index_name, 768)

ingestion_data_to_elastic(index_name, dataframe)