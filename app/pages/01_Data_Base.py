import streamlit as st
import pandas as pd

import datetime
import time
from utils_for_streamlit import auto_height
from data_from_supabase import fetch

# --- page_config ---
st.set_page_config(page_title="データベース", page_icon="", layout="wide")

# --- Title etc. ---
st.title("データベース")
st.header("データベースの表示", divider="rainbow")
st.markdown(
    """
    メモリ削減のため、必要なデータのみ表示しています。
    - 期間指定で日付範囲を絞り込み可能
    - ホール・機種・台番で絞り込み可能
    """
)

help_text = "過去5日間のデータを初期表示しています。"
st.subheader("フィルター設定", divider="rainbow", help=help_text)


# --- 日付処理 ---
PAST_N_DAYS = 5
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

def validate_dates():
    if ss.end_date < ss.start_date:
        ss.start_date = ss.end_date

col1, col2 = st.columns(2)
with col1:
    st.date_input(
        "検索開始日",
        key="start_date",
        value=ss["start_date"],
        max_value=yesterday,
        on_change=validate_dates,
    )
with col2:
    st.date_input(
        "検索終了日",
        key="end_date",
        value=ss["end_date"],
        # min_value=ss["start_date"],
        max_value=yesterday,
        on_change=validate_dates,
    )
st.write(f"📅 検索期間: {ss.start_date} ～ {ss.end_date}")

df = fetch("result_joined", ss.start_date, ss.end_date, hall=None, model=None)

# --- リスト&フィルター ---
col1, col2, col3 = st.columns(3)
with col1:
    halls = sorted(df["hall"].unique())
    hall = st.selectbox("ホールを選択", halls, help="お気に入り機能追加??")
    df_hall = df[(df["hall"] == hall)]
    time.sleep(0.2)
with col2:
    models = df_hall["model"].value_counts().index.tolist()
    if len(models) > 6:
        models.insert(6, "すべて表示")
    else:
        models.append("すべて表示")
    model = st.selectbox("機種を選択", models, help="台数の多い順に表示")
    df_model = df_hall
    if model != "すべて表示":
        df_model = df_hall[(df_hall["model"] == model)]
    time.sleep(0.2)
with col3:
    units = df_model["unit_no"].unique().tolist()
    if len(units) > 6:
        units.insert(6, "すべて表示")
    else:
        units.append("すべて表示")
    unit = st.selectbox("台番号を選択", units, help="すべて表示も可能")
    df_unit = df_model
    if unit != "すべて表示":
        df_unit = df_model[df_model["unit_no"] == unit]
    time.sleep(0.2)

# --- Display ---
show_cols = ["hall", "model", "date", "unit_no", "game", "medal", "bb", "rb"]
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