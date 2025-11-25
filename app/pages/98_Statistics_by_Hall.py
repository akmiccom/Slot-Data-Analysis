import os
from datetime import date
from typing import Optional, Union, Any
import pandas as pd
from supabase import create_client, Client
import streamlit as st

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import auto_height


supabase = get_supabase_client()


page_title = "Statistics_by_Hall"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

st.subheader("Medal Rate by Hall")
query = supabase.table("medal_rate_by_hall").select("*")
rows = _fetch_all_rows(query)
df = pd.DataFrame(rows).round(1)
pivot = df.pivot_table(
    index="hall", columns="day_last", values="medal_rate"
)
st.dataframe(pivot, width="stretch", height=auto_height(pivot))


