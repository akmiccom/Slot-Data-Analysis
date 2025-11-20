import streamlit as st
import pandas as pd
import datetime
import time
from data_from_supabase import fetch
from utils import HALLS, WEEKDAY_MAP
from utils import auto_height
from utils import style_val
from utils import make_style_val
from utils import validate_dates


PAST_N_DAYS = 5

# --- page_config ---
st.set_page_config(page_title="ホール別の出玉率・回転数履歴", layout="wide")

# --- Title etc. ---
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.title("ホール別の出玉率・回転数履歴")
st.markdown(
    f"""
    ホール別の**出玉率履歴データ**を表示します。機能は順次追加する予定です。
    - 初期設定では**{PAST_N_DAYS}**日間を表示しています。
    """
)

# --- UI ---
st.subheader("フィルター設定", divider="rainbow")

# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

# --- 初期読み込み ---
df = fetch("result_joined", n_d_ago, today)
st.text(df.columns)
df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.day
df["weekday_num"] = df["date"].dt.weekday
df["weekday"] = df["weekday_num"].map(WEEKDAY_MAP)
df["day_last"] = df["day"].astype(str).str[-1]
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d %a")

# -- フィルター設定 ---
col1, col2, col3 = st.columns(3)
with col1:
    st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col2:
    st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
ALL = "すべて表示"
with col3:
    halls = sorted(df.hall.unique().tolist())
    if len(halls) > 5:
        halls.insert(5, ALL)
    else:
        halls.append(ALL)
    hall = st.selectbox("ホールを選択", halls)
    if hall != ALL:
        df = df[df["hall"] == hall]

col1, col2, col3 = st.columns(3)
with col1:
    day_last_list = [ALL] + sorted(df["day_last"].unique().tolist())
    day_last = st.selectbox("末尾日を選択", day_last_list)
    if day_last != ALL:
        df = df[df["day_last"] == day_last]
with col2:
    day_list = [ALL] + sorted(df["day"].unique().tolist())
    day = st.selectbox("毎月〇〇日を選択", day_list)
    if day != ALL:
        df = df[df["day"] == day]
with col3:
    weekday_list = [ALL, "土", "日", "月", "火", "水", "木", "金"]
    weekday = st.selectbox("曜日を選択", weekday_list)
    if weekday != ALL:
        df = df[df["weekday"] == weekday]
    

# --- pivot_table ---
games = df.pivot_table(
    index=["hall"],
    columns="date",
    values="game",
    aggfunc="mean",
    margins=True,
    margins_name="SubTotal",
)
medals = df.pivot_table(
    index=["hall"],
    columns="date",
    values="medal",
    aggfunc="mean",
    margins=True,
    margins_name="SubTotal",
)
rate = (games * 3 + medals) / (games * 3)
sorted_game = games.iloc[:, ::-1]
sorted_rate = rate.iloc[:, ::-1]


# --- Display ---
st.subheader("ホール別出玉率履歴", divider="rainbow")
threshold_value = 1.02
style_func = make_style_val(threshold_value)
num_cols = sorted_rate.select_dtypes(include="number").columns
df_styled = sorted_rate.style.map(style_func, subset=num_cols).format(
    {col: "{:.3f}" for col in num_cols}
)
st.dataframe(df_styled, height=auto_height(sorted_rate))


# --- Display ---
st.subheader("ホール別回転数履歴", divider="rainbow")

threshold_value = 5000
style_func = make_style_val(threshold_value)
num_cols = sorted_game.select_dtypes(include="number").columns
df_styled = sorted_game.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)
st.dataframe(df_styled, height=auto_height(sorted_game))

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