# import os
import streamlit as st
# import pandas as pd
import datetime
import time
from utils import validate_dates
from data_from_supabase import fetch, get_latest_data


PAST_N_DAYS = 5

st.markdown('<a id="page_top"></a>', unsafe_allow_html=True)

# --- page_config ---
page_title = "データベース検索"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

# --- Title etc. ---
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.header(page_title)
st.markdown(
    """
    - ホール・機種・台番・期間で絞り込みが可能です。
    - ホールごとに台数が多い機種を優先的に表示します。
    - 台番号で「すべて表示」して、日付を一日に絞るとその日のデータを一覧で確認できます。
    """
)

# --- UI ---
help_text = f"過去{PAST_N_DAYS}日間のデータを表示しています。"
st.subheader("フィルター設定", divider="rainbow", help=help_text)

# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

# --- 初期読み込み ---

# -- フィルター設定 ---
ALL = "すべて表示"
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    start = st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col2:
    end = st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
with col3:
    # halls = sorted(df["hall"].unique().tolist())
    df_unique, df_final, halls = get_latest_data("result_joined", start, end)
    hall = st.selectbox("ホールを選択", halls, help="お気に入り機能追加??")
    df_hall = df_final[(df_final["hall"] == hall)]
    df_hall = df_hall.drop_duplicates()
with col4:
    models = df_hall["model"].value_counts().index.tolist()
    model = st.selectbox("機種を選択", models, help="台数の多い順に表示")
    df_model = df_hall[(df_hall["model"] == model)]
    df_model = df_model.drop_duplicates()
with col5:
    units = sorted(df_model["unit_no"].unique().tolist()) + [ALL]
    unit = st.selectbox("台番号を選択", units, help="すべて表示も可能")
    df_unit = df_model
    if unit != ALL:
        df_unit = df_model[df_model["unit_no"] == unit]
    df_unit = df_unit.drop_duplicates()

# --- Display ---
st.subheader("検索結果", divider="rainbow", help=help_text)
st.markdown(
    f"""
    - 📅 検索期間: {ss.start_date} ～ {ss.end_date}
    - 📅 ホール: {df_unit.hall.values[0]}
    - 📅 機種: {df_unit.model.values[0]}
    """
)
show_cols = ["model", "date", "unit_no", "game", "medal", "bb", "rb"]
show_df = df_unit[show_cols]

st.dataframe(show_df, height="auto", width="stretch", hide_index=True)
if show_df.shape[0]:
    st.text(f"{show_df.shape[0]} 件のデータが存在します。")
else:
    st.text(f"データが存在しません。検索条件の見直しをしてください。")

# トップに戻るリンク
st.markdown(
    """
    <div style="text-align: right;">
        <a href="/"
           target="_self"
           style="font-size: 16px; text-decoration: none;">
            🏠 HOME
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)
