import pandas as pd
import streamlit as st

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import auto_height, make_style_val


supabase = get_supabase_client()

page_title = "Statistics_by_Hall"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")

st.subheader("Medal Rate by Hall")
# query = supabase.table("medal_rate_by_hall").select("*")
# rows = _fetch_all_rows(query)
# df = pd.DataFrame(rows).round(1)
# st.dataframe(df)

col1, col2, col3 = st.columns(3)
with col1:
    query = supabase.table("prefectures").select("name")
    rows = _fetch_all_rows(query)
    prefectures = [row["name"] for row in rows]
    pref = st.selectbox("都道府県を選択", prefectures)
    # prefectures = df["prefecture"].value_counts().index.tolist()
    # pref = st.selectbox("都道府県を選択", prefectures)
    
    query = supabase.table("medal_rate_by_hall").select("*").eq("prefecture", pref)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    df = df[df["prefecture"] == pref]
    pivot = df.pivot_table(index="hall", columns="day_last", values="medal_rate")


with col2:
    value_list = [100.0, 101.0, 102.0]
    threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
    # --- style ---
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )

# --- display ---
st.dataframe(df_styled, width="stretch", height=auto_height(pivot))
