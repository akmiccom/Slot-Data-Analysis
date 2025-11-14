import datetime
import streamlit as st
from data_from_supabase import fetch

N_PAST_DAYS = 5
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=N_PAST_DAYS)
yesterday = today - datetime.timedelta(days=1)


st.set_page_config(page_title="スロットデータ分析", layout="wide")

st.header("TOP PAGE に乗せるもの")
st.subheader("グラフなどでホール分析のダッシュボードを作成")
st.subheader("月別、機種別出玉推移")


df = fetch("result_joined", n_d_ago, today, hall=None, model=None)

st.subheader("データベース確認用")
st.text(df.hall.unique())
st.text(df.model.unique())
st.text(f"読み込み数: {df.shape[0]} 件")
st.dataframe(df)
