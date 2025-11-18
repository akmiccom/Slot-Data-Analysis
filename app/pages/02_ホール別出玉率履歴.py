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


PAST_N_DAYS = 7

# --- page_config ---
st.set_page_config(page_title="ホール別の出玉率・回転数履歴", layout="wide")

# --- Title etc. ---
st.title("ホール別の出玉率・回転数履歴")
st.subheader("ホール別出玉率履歴", divider="rainbow")
st.markdown(
    f"""
    ホール別の**出玉率履歴データ**を表示します。機能は順次追加する予定です。
    - 初期設定では**{PAST_N_DAYS}**日間を表示しています。
    """
)


# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

col1, col2, col3 = st.columns(3)
with col1:
    st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col2:
    st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
with col3:
    df = fetch("result_joined", ss.start_date, ss.end_date, hall=None, model=None)
    halls = ["すべてのホール"] + df["hall"].unique().tolist()
    hall = st.selectbox("ホールを選択", halls)

if hall != "すべてのホール":
    df = df[df["hall"] == hall]
    
    
df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.day
df["weekday_num"] = df["date"].dt.weekday
df["weekday"] = df["weekday_num"].map(WEEKDAY_MAP)
df["day_last"] = df["day"].astype(str).str[-1]
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d %a")


ALL = "すべて表示"
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
sorted_games = games.iloc[:, ::-1]
sorted_rate = rate.iloc[:, ::-1]


# --- Display ---
threshold_value = 1.02
style_func = make_style_val(threshold_value)
num_cols = sorted_rate.select_dtypes(include="number").columns
df_styled = sorted_rate.style.map(style_func, subset=num_cols).format(
    {col: "{:.3f}" for col in num_cols}
)
if len(sorted_rate) > 10:
    height = min(100 + len(sorted_rate) * 30, 800)
else:
    height = "auto"
st.dataframe(df_styled, height=height)


# --- Display ---
st.subheader("ホール別平均回転数履歴", divider="rainbow")

threshold_value = 5000
style_func = make_style_val(threshold_value)
num_cols = sorted_games.select_dtypes(include="number").columns
df_styled = sorted_games.style.map(style_func, subset=num_cols).format(
    {col: "{:.1f}" for col in num_cols}
)

if len(sorted_games) > 10:
    height = min(100 + len(sorted_games) * 30, 800)
else:
    height = "auto"
st.dataframe(df_styled, height=height)
