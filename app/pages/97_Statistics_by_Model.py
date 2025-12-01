import os
from datetime import date
from typing import Optional, Union, Any
import pandas as pd
from supabase import create_client, Client
import streamlit as st

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import auto_height, make_style_val


supabase = get_supabase_client()


page_title = "Statistics_by_Model"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

st.subheader("Medal Rate by Model")


# --- filter ---
ALL = "すべて"
col1, col2, col3 = st.columns(3)
with col1:
    query = supabase.table("prefectures").select("name")
    rows = _fetch_all_rows(query)
    prefectures = [row["name"] for row in rows]
    pref = st.selectbox("都道府県を選択", prefectures)
    
    query = supabase.table("medal_rate_by_model").select("day_last,count,hall,model,medal_rate,prefecture,avg_game").eq("prefecture", pref)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    df = df[df["prefecture"] == pref]
with col2:
    halls = df["hall"].value_counts().index.tolist() + [ALL]
    hall = st.selectbox("hall", halls)
    if hall not in (None, ALL):
        df = df[df["hall"] == hall]
with col3:
    models = [ALL] + df["model"].value_counts().index.tolist()
    model = st.selectbox("model", models)
    if model not in (None, ALL):
        df = df[df["model"] == model]
# st.dataframe(df)
medal_rate = df.pivot_table(
    index=["hall", "model"], columns="day_last", values="medal_rate"
)

# --- style and display ---
value_list = [102.0, 103.0, 104.0]
threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
style_func = make_style_val(threshold_value)
num_cols = medal_rate.select_dtypes(include="number").columns
df_styled = medal_rate.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)
st.dataframe(df_styled, width="stretch", height=auto_height(medal_rate))


# --- style and display ---
st.subheader("Game by Model")
avg_game = df.pivot_table(
    index=["hall", "model"], columns="day_last", values="avg_game"
)

value_list = [3000, 4000, 5000, 6000]
threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
style_func = make_style_val(threshold_value)
num_cols = avg_game.select_dtypes(include="number").columns
df_styled = avg_game.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)
st.dataframe(df_styled, width="stretch", height=auto_height(avg_game))
