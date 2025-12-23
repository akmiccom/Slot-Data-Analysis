import os
from datetime import date
from typing import Optional, Union, Any
import pandas as pd
from supabase import create_client, Client
import streamlit as st

from fetch_functions import get_supabase_client, _fetch_all_rows
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models
from utils import auto_height, make_style_val


@st.cache_data
def medal_rate_by_model(pref, hall, model):
    ALL = "すべて"
    supabase = get_supabase_client()
    query = (
        supabase.table("medal_rate_by_model")
        .select("day_last,count,hall,model,medal_rate,prefecture,avg_game")
        .eq("prefecture", pref)
        # .eq("hall", hall)
    )
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    if model not in (None, ALL):
        query = query.eq("model", model)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    return df


page_title = "機種別出玉率"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader(page_title, divider="rainbow")


# --- filter ---
ALL = "すべて"
col1, col2, col3 = st.columns(3)
with col1:
    prefectures = fetch_prefectures()
    pref = st.selectbox("都道府県を選択", prefectures)

with col2:
    halls = fetch_halls(pref) + [ALL]
    hall = st.selectbox("hall", halls)
with col3:
    models = [ALL] + fetch_models(pref, hall)
    model = st.selectbox("model", models)
# st.dataframe(df)

df = medal_rate_by_model(pref, hall, model)

medal_rate = df.pivot_table(
    index=["hall", "model"], columns="day_last", values="medal_rate"
)

# --- style and display ---
value_list = [101.0, 102.0, 103.0, 104.0]
threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
style_func = make_style_val(threshold_value)
num_cols = medal_rate.select_dtypes(include="number").columns
df_styled = medal_rate.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)
st.subheader("末尾日別出玉率", divider="rainbow")
st.dataframe(df_styled, width="stretch", height=auto_height(medal_rate))


# --- style and display ---
avg_game = df.pivot_table(
    index=["hall", "model"], columns="day_last", values="avg_game"
)

value_list = [3000, 4000, 5000, 6000]
threshold_value = st.pills("回転数を選択", value_list, default=value_list[1])
style_func = make_style_val(threshold_value)
num_cols = avg_game.select_dtypes(include="number").columns
df_styled = avg_game.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)
st.subheader("末尾日別回転数", divider="rainbow")
st.dataframe(df_styled, width="stretch", height=auto_height(avg_game))
