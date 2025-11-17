import os
import streamlit as st
import pandas as pd

import datetime
import time
from utils_for_streamlit import validate_dates
from data_from_supabase import fetch, fetch_halls

PAST_N_DAYS = 8

# --- page_config ---
page_title = "データベース検索"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

# --- Title etc. ---
st.page_link("Slot_Data_Analysis.py", label="🏠 トップページへ戻る")
st.header(page_title)
st.markdown("フィルター設定で、ホール・機種・台番・期間で絞り込みが可能です。")

# st.divider()
help_text = f"過去{PAST_N_DAYS}日間のデータを表示しています。"
st.subheader("フィルター設定", divider="rainbow", help=help_text)


# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
display_date = today - datetime.timedelta(days=30)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

col1, col2 = st.columns(2)
with col1:
    st.date_input(
        "検索開始日",
        key="start_date",
        max_value=yesterday,
        on_change=validate_dates,
    )
    time.sleep(0.1)
with col2:
    st.date_input(
        "検索終了日",
        key="end_date",
        max_value=yesterday,
        on_change=validate_dates,
    )
    time.sleep(0.1)

# --- リスト&フィルター ---
col1, col2, col3 = st.columns(3)
with col1:
    # --- hall ---
    halls = fetch_halls()["name"].tolist()
    hall = st.selectbox("ホールを選択", halls, help="お気に入り機能追加??")
    df = fetch("result_joined", ss.start_date, ss.end_date, hall=hall, model=None)
    df_hall = df[(df["hall"] == hall)]
    time.sleep(0.1)
with col2:
    # --- model ---
    models = df_hall["model"].value_counts().index.tolist()
    model = st.selectbox("機種を選択", models, help="台数の多い順に表示")
    df_model = df_hall[(df_hall["model"] == model)]
    time.sleep(0.1)
with col3:
    # --- unit_no ---
    units = sorted(df_model["unit_no"].unique().tolist())
    if len(units) > 5:
        units.insert(5, "すべて表示")
    else:
        units.append("すべて表示")
    unit = st.selectbox("台番号を選択", units, help="すべて表示も可能")
    df_unit = df_model
    if unit != "すべて表示":
        df_unit = df_model[df_model["unit_no"] == unit]
    time.sleep(0.1)

# --- Display ---
st.divider()
# st.subheader("データベース", divider="rainbow", help=help_text)
st.markdown(
    f"""
    - 📅 検索期間: {ss.start_date} ～ {ss.end_date}
    - 📅 ホール: {df_unit.hall.values[0]}
    - 📅 機種: {df_unit.model.values[0]}
    """
)
show_cols = ["model", "date", "unit_no", "game", "medal", "bb", "rb"]
show_df = df_unit[show_cols]

if len(show_df) > 10:
    height = min(100 + len(show_df) * 30, 800)
else:
    height = "auto"
st.dataframe(show_df, height=height, width="stretch", hide_index=True)
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
            🏠 トップへ戻る
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)


start_date, end_date = st.slider(
    "検索期間",
    min_value=display_date,
    max_value=today,
    value=(n_d_ago, today),
    format="YYYY-MM-DD",
)
st.write(f"📅 検索期間: {start_date} ～ {end_date}")
