import streamlit as st
import pandas as pd
import datetime
import time
from data_from_supabase import fetch
from utils_for_streamlit import HALLS, WEEKDAY_MAP
from utils_for_streamlit import auto_height
from utils_for_streamlit import style_val
from utils_for_streamlit import make_style_val


PAST_N_DAYS = 7

# --- page_config ---
st.set_page_config(page_title="台番号別の出玉率・回転数履歴", layout="wide")

# --- Title etc. ---
st.title("台番号別の出玉率・回転数履歴")
st.header("台番号別出玉率履歴", divider="rainbow")
st.markdown(
    f"""
    台番号別の**出玉率履歴データ**を表示します。機能は順次追加する予定です。
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


def validate_dates():
    if ss.end_date < ss.start_date:
        ss.start_date = ss.end_date


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

ALL = "すべて表示"
df_fetch = fetch("result_joined", ss.start_date, ss.end_date, hall=None, model=None)

col1, col2, col3 = st.columns(3)
# --- 1) ホール選択 ---
halls = sorted(df_fetch["hall"].unique().tolist()) + [ALL]
with col1:
    hall = st.selectbox("ホールを選択", halls)
df_h = df_fetch if hall == ALL else df_fetch[df_fetch["hall"] == hall]
# --- 2) モデル選択（ホールに従属）---
models = sorted(df_h["model"].dropna().unique().tolist()) + [ALL]
with col2:
    model = st.selectbox("モデルを選択", models)
df_hm = [ALL] + df_h if model == ALL else df_h[df_h["model"] == model]
# --- 3) ユニット選択（ホール＋モデルに従属）---
units = sorted(df_hm["unit_no"].dropna().unique().tolist()) + [ALL]
with col3:
    unit = st.selectbox("台番号を選択", units)
# --- 4) 最終フィルタ（段階結果に基づいて AND 結合）---
df_filtered = df_hm if unit == ALL else df_hm[df_hm["unit_no"] == unit]

df = df_filtered
# groupby 用のカラムを追加
df["BB_rate"] = (df["game"] / df["bb"]).round(1)
df["RB_rate"] = (df["game"] / df["rb"]).round(1)
df["Total_rate"] = (df["game"] / (df["bb"] + df["rb"])).round(1)
df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.day
df["weekday_num"] = df["date"].dt.weekday
df["weekday"] = df["weekday_num"].map(WEEKDAY_MAP)
df["day_last"] = df["day"].astype(str).str[-1]
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%m-%d %a")


col1, col2, col3 = st.columns(3)
with col1:
    day_last_list = ["すべて表示"] + sorted(df["day_last"].unique().tolist())
    day_last = st.selectbox("末尾日を選択", day_last_list)
    if day_last != "すべて表示":
        df = df[df["day_last"] == day_last]
with col2:
    day_list = ["すべて表示"] + sorted(df["day"].unique().tolist())
    day = st.selectbox("毎月〇〇日を選択", day_list)
    if day != "すべて表示":
        df = df[df["day"] == day]
with col3:
    weekday_list = ["すべて表示", "土", "日", "月", "火", "水", "木", "金"]
    weekday = st.selectbox("曜日を選択", weekday_list)
    if weekday != "すべて表示":
        df = df[df["weekday"] == weekday]


# --- pivot_table ---
# ['game', 'BB', 'RB', 'medals', 'BB_rate', 'RB_rate', 'Total_rate']
st.text(df.columns)
target_idx = ["hall", "model", "unit_no"]
pivots = df.pivot_table(index=target_idx, columns="date", aggfunc="sum")
games = pivots["game"].iloc[:, ::-1]
medals = pivots["medal"].iloc[:, ::-1]
rb_rate = pivots["RB_rate"].iloc[:, ::-1]
total_rate = pivots["Total_rate"].iloc[:, ::-1]

medal_rate = (games * 3 + medals) / (games * 3)
sorted_medal_rate = medal_rate.iloc[:, ::-1]
game_mean = games.mean().mean()

# games.insert(0, "label", "games")
# games = games.reset_index()
st.text("games")
st.dataframe(games)
st.text("medals")
st.dataframe(medals)
st.text("RB_rate")
st.dataframe(rb_rate)
st.text("Total_rate")
st.dataframe(total_rate)


# # --- Display ---
# threshold_value = 1.02
# style_func = make_style_val(threshold_value)
# num_cols = medal_rate.select_dtypes(include="number").columns
# df_styled = medal_rate.style.map(style_func, subset=num_cols).format(
#     {col: "{:.3f}" for col in num_cols}
# )
# if len(medal_rate) > 10:
#     height = min(100 + len(medal_rate) * 30, 800)
# else:
#     height = "auto"
# st.dataframe(df_styled, height=height)


# # --- Display ---
# st.header("台番号別平均回転数履歴", divider="rainbow")
# st.text(f"平均回転数 : {game_mean:.01f}")
# threshold_value = game_mean * 1.3
# style_func = make_style_val(threshold_value)
# num_cols = games.select_dtypes(include="number").columns
# df_styled = games.style.map(style_func, subset=num_cols).format(
#     {col: "{:.1f}" for col in num_cols}
# )

# if len(games) > 10:
#     height = min(100 + len(games) * 30, 800)
# else:
#     height = "auto"
# st.dataframe(df_styled, height=height)


idx = ["hall", "model", "unit_no"]
vals = ["game", "medal", "bb", "rb"]
cols = ["day_last"]
agg = "sum"
# pt = df.pivot_table(index=idx, columns=cols, aggfunc=agg, values=vals, margins=True)
pt = df.pivot_table(index=idx, columns=cols, aggfunc=agg, values=vals)
medal_rate = ((pt["game"] * 3 + pt["medal"]) / (pt["game"] * 3)).round(3)
# medal_rate
labeled_columns = [("medal_rate", d) for d in medal_rate.columns]
medal_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)
# medal_rate
rb_rate = (pt[f"game"] / pt["rb"]).round(1)
labeled_columns = [("rb_rate", d) for d in rb_rate.columns]
rb_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)
# rb_rate
total_rate = (pt["game"] / pt["bb"] + pt["rb"]).round(1)
labeled_columns = [("total_rate", d) for d in total_rate.columns]
total_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)
# total_rate
# concat and sort columns
df_day_last = pd.concat([pt, medal_rate, rb_rate, total_rate], axis=1)
# df_day_last
sort_vals = ["game", "medal", "medal_rate", "rb_rate", "total_rate"]
interleaved_cols = [
    (i, j) for j in df_day_last.columns.get_level_values(1).unique() for i in sort_vals
]
# interleaved_cols
df_day_last = df_day_last[interleaved_cols]
# latest only
# df_day_last = df_day_last.loc[pt_latest.index]
# df_day_last = df_day_last.replace([np.inf, -np.inf], np.nan)
st.dataframe(df_day_last)
