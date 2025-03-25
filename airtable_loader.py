import pandas as pd
from pyairtable import Table

def fetch_airtable_data(api_key, base_id, table_name):
    table = Table(api_key, base_id, table_name)
    records = table.all()
    df = pd.DataFrame([rec['fields'] for rec in records])
    df = df.fillna('')
    df['text'] = df.apply(lambda row: f"{row['Name']}, {row['Address']}, Cuisine: {row.get('Cuisine')}, Atmosphere: {row.get('Atmosphere')}, Capacity: {row.get('Capacity_Max')}, Features: {row.get('Special_Features')}", axis=1)
    return df
