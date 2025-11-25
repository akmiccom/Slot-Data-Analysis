import os
from datetime import date
from typing import Optional, Union, Any
import pandas as pd
from supabase import create_client, Client
import streamlit as st

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import auto_height


supabase = get_supabase_client()

page_title = "Statistics_by_Unit"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.subheader(page_title)

# --- selecter ---
ALL = "すべて表示"
col1, col2, col3 = st.columns(3)
with col1:
    day_lasts = [i for i in range(10)] + [ALL]
    day_last = st.selectbox("day_last", day_lasts)
with col2:
    query = supabase.table("halls").select("name")
    rows = _fetch_all_rows(query)
    halls = sorted([row["name"] for row in rows]) + [ALL]
    hall = st.selectbox("hall", halls)
with col3:
    query = (
        supabase.table("result_joined")
        .select("model")
        .eq("hall", hall)
        .gte("date", "2025-11-22")
        .lte("date", "2025-11-24")
    )
    rows = _fetch_all_rows(query)
    models = [ALL] + sorted(set([row["model"] for row in rows]))
    model = st.selectbox("model", models)

# --- fetch ---
query = supabase.table("medal_rate_by_unit_no").select("*")
if hall is not None and hall != ALL:
    query = query.eq("hall", hall)
if model is not None and model != ALL:
    query = query.eq("model", model)
if day_last is not None and day_last != ALL:
    query = query.eq("day_last", day_last)
rows = _fetch_all_rows(query)
df = pd.DataFrame(rows)


# --- preprocess ---
sort_list = ["rb_rate", "win_rate"]
ascending_list = [True, False]
df = df.sort_values(sort_list, ascending=ascending_list)
round_list = ["bb_rate", "rb_rate", "total_rate", "medal_rate", "avg_game", "avg_medal"]
df[round_list] = df[round_list].round(1)
df["win_rate"] = df["win_rate"].round(2)
df = df[df["avg_game"] >= 3000]
df = df[df["avg_medal"] >= 500]
df = df[df["medal_rate"] >= 103]
df = df[df["rb_rate"] <= 322]
df = df[df["win_rate"] >= 0.51]
df = df[df["count"] >= 5]


# --- display ---
# df_show = df[["model", "rb_rate", "medal_rate", "win_rate", "avg_game"]]
df_show  =df
st.dataframe(df_show, height=auto_height(df_show), hide_index=True)
