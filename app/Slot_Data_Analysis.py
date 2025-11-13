import streamlit as st
from scraper.data_from_supabase import fetch

st.set_page_config(page_title="スロットデータ分析", layout="wide")

st.header("TOP PAGE に乗せるもの")
st.subheader("グラフなどでホール分析のダッシュボードを作成")
st.subheader("月別、機種別出玉推移")

df = fetch("result_joined", "2025-10-1", "2025-11-13", hall=None, model=None)
st.dataframe(df)