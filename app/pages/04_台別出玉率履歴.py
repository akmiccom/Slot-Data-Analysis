import streamlit as st
import pandas as pd
import datetime
import time
import os
import yaml
from data_from_supabase import fetch, fetch_halls
from preprocess import df_preprocess, build_mapping, cal_grape_rate
from utils import WEEKDAY_MAP
from utils import validate_dates
from utils import auto_height
from utils import style_val


PAST_N_DAYS = 5

# --- page_config ---
page_title = "台番号別の出玉率・回転数履歴"
st.set_page_config(page_title=page_title, layout="wide")

# --- Title etc. ---
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
help_text = f"過去{PAST_N_DAYS}日間のデータを表示しています。"
st.subheader(page_title, divider="rainbow", help=help_text)
st.markdown(
    f"""
    台番号別の**出玉率履歴データ**を表示します。
    - 初期設定では **{PAST_N_DAYS}** 日間を表示しています。
    - 機能は順次追加する予定です。
    """
)

# --- 日付処理 ---
today = datetime.date.today()
n_d_ago = today - datetime.timedelta(days=PAST_N_DAYS)
yesterday = today - datetime.timedelta(days=1)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", yesterday)

# --- 初期読み込み ---
df = fetch("result_joined", ss.start_date, ss.end_date, hall=None, model=None)

# -- フィルター設定 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.date_input(
        "検索開始日", key="start_date", max_value=yesterday, on_change=validate_dates
    )
with col2:
    st.date_input(
        "検索終了日", key="end_date", max_value=yesterday, on_change=validate_dates
    )
ALL = "すべて表示"
col1, col2, col3 = st.columns(3)
with col1:
    halls = sorted(df["hall"].unique().tolist())
    if len(halls) > 5:
        halls.insert(5, ALL)
    else:
        halls.append(ALL)
    hall = st.selectbox("ホールを選択", halls)
    df_hall = df if hall == ALL else df[df["hall"] == hall]
# --- 2) モデル選択（ホールに従属）---
with col2:
    models = df_hall["model"].value_counts().index.tolist()
    model = st.selectbox("モデルを選択", models)
    df_model = [ALL] + df_hall if model == ALL else df_hall[df_hall["model"] == model]
# --- 3) ユニット選択（ホール＋モデルに従属）---
with col3:
    units = [ALL] + sorted(df_model["unit_no"].dropna().unique().tolist())
    unit = st.selectbox("台番号を選択", units)
    df_unit = df_model if unit == ALL else df_model[df_model["unit_no"] == unit]

# --- 前処理関数 ---
df_filtered = df_unit
df = df_preprocess(df_filtered)

# -– フィルタリング（日付・末尾日・毎月〇〇日・曜日）---
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

# --- pivot_table 作成 ---
idx = ["hall", "model", "unit_no"]
vals = ["game", "medal", "bb", "rb", "grape_r"]
cols = ["date"]
agg = "sum"
pt = df.pivot_table(index=idx, columns=cols, aggfunc=agg, values=vals)

# medal_rate
medal_rate = ((pt["game"] * 3 + pt["medal"]) / (pt["game"] * 3)).round(3)
labeled_columns = [("medal_r", d) for d in medal_rate.columns]
medal_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)

# bb_rate
bb_rate = (pt[f"game"] / pt["bb"]).round(1)
labeled_columns = [("bb_r", d) for d in bb_rate.columns]
bb_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)

# rb_rate
rb_rate = (pt[f"game"] / pt["rb"]).round(1)
labeled_columns = [("rb_r", d) for d in rb_rate.columns]
rb_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)

# total_rate
total_rate = (pt["game"] / (pt["bb"] + pt["rb"])).round(1)
labeled_columns = [("total_r", d) for d in total_rate.columns]
total_rate.columns = pd.MultiIndex.from_tuples(labeled_columns)

# concat and sort columns
concat_list = [pt, medal_rate, bb_rate, rb_rate, total_rate]
df_history = pd.concat(concat_list, axis=1)
df_history = df_history.iloc[:, ::-1]


# 表示するカラムの選択
default_cols = ["game", "medal", "bb", "rb"]

detail_cols = [
    "game",
    "medal",
    "medal_r",
    "bb",
    "rb",
    "bb_r",
    "rb_r",
    "total_r",
    "grape_r",
]

st.divider()

disp_cols = default_cols
details = st.toggle("詳細表示に切り替える", value=False)
if details:
    disp_cols = detail_cols

interleaved_cols = [
    (i, j) for j in df_history.columns.get_level_values(1).unique() for i in disp_cols
]

# display
df_history = df_history[interleaved_cols]
df_history = df_history.reset_index()
st.markdown(
    f"""
    - 📅 検索期間: {ss.start_date} ～ {ss.end_date}
    - 📅 {df_history.hall.values[0]}
    - 📅 {df_history.model.values[0]}
    """
)
df_history = df_history.drop(columns=df_history.columns[:2])
df_history = df_history.set_index("unit_no")
df_history = df_history.swaplevel(0, 1, axis=1)
first_col = df_history.columns[0]
df_history = df_history.dropna(subset=[first_col])
# df_history.loc["mean"] = df_history.mean(numeric_only=True).round(1)
mean_row = df_history.mean(numeric_only=True).round(1)
mean_row.name = "mean"
df_history = pd.concat([pd.DataFrame([mean_row]), df_history])
st.dataframe(df_history, width="stretch", height=auto_height((df_history)))

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