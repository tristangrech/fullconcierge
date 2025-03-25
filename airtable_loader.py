import pandas as pd
from pyairtable import Table

def fetch_airtable_data(api_key, base_id, table_name):
    try:
        table = Table(api_key, base_id, table_name)
        records = table.all()
        return records
    except Exception as e:
        import streamlit as st
        st.error(f"❌ Airtable Error: {e}")
        raise
