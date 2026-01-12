import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

from utils import WEEKDAY_JA, WEEKDAY_JA_TO_INT
from utils import PRIORITY_MODELS, PRIORITY_HALLS
from utils import n_days_ago
from utils import home_link
from utils import get_rb_rate_from_json, get_total_rate_from_json
from utils import calc_grape_rate
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units


# --------------------------------------------------
# page_config（必ず最初）
# --------------------------------------------------
page_title = "Sample UI"
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

home_link(position="right")


# --------------------------------------------------
# Title
# --------------------------------------------------
st.header(page_title)
st.markdown(
    """
    - 検索条件を入力して実行を押してください。
    - 台番号を『すべて表示』開始日と終了日を同じ日にすると日別の表示ができます。
    """
)


# --------------------------------------------------
# Filters（即時反映）
# --------------------------------------------------
ALL = "すべて表示"
with st.container(border=True):
    c1, c2, c3, c4 = st.columns([0.6, 1, 1, 0.7])

    with c1:
        pref = st.selectbox("都道府県", fetch_prefectures())

    with c2:
        halls = fetch_halls(pref=pref)
        ordered_halls = [m for m in PRIORITY_HALLS if m in halls]
        others = [m for m in halls if m not in PRIORITY_HALLS]
        final_halls = ordered_halls + others
        hall = st.selectbox("ホール", final_halls)

    with c3:
        models = fetch_models(pref=pref, hall=hall)
        ordered_models = [m for m in PRIORITY_MODELS if m in models]
        others = [m for m in models if m not in PRIORITY_MODELS]
        final_models = ordered_models + others
        model = st.selectbox("機種", final_models)

    with c4:
        units = fetch_units(pref=pref, hall=hall, model=model) + [ALL]
        unit_no = st.selectbox("台番号", units)
        unit_no = None if unit_no == ALL else unit_no

    # --------------------------------------------------
    # Filter（曜日）
    # --------------------------------------------------
    # --- コールバック ---
    def on_all_change():
        if st.session_state.weekday_all:
            # 「すべて表示」がONなら他を全部OFF
            for w in WEEKDAY_JA:
                st.session_state[f"weekday_{w}"] = False

    def on_weekday_change():
        # どれか1つでもONなら「すべて表示」をOFF
        if any(st.session_state[f"weekday_{w}"] for w in WEEKDAY_JA):
            st.session_state.weekday_all = False
        else:
            # 全部OFFなら「すべて表示」をONに戻す
            st.session_state.weekday_all = True

    # -―― 初期化 ---
    if "weekday_all" not in st.session_state:
        st.session_state.weekday_all = True

    for w in WEEKDAY_JA:
        key = f"weekday_{w}"
        if key not in st.session_state:
            st.session_state[key] = False

    # --- UI(曜日) ---
    labels = WEEKDAY_JA + [ALL]
    cols = st.columns([1] * (len(labels) - 1) + [2])

    for col, label in zip(cols, labels):
        if label == ALL:
            col.checkbox(
                label,
                key="weekday_all",
                on_change=on_all_change,
            )
        else:
            col.checkbox(
                label,
                key=f"weekday_{label}",
                on_change=on_weekday_change,
            )

    # --- 内部値 ---
    if st.session_state.weekday_all:
        weekday_int_list = None
    else:
        weekday_int_list = [
            WEEKDAY_JA_TO_INT[w] for w in WEEKDAY_JA if st.session_state[f"weekday_{w}"]
        ]

    # --------------------------------------------------
    # Filter（末尾日）
    # --------------------------------------------------
    DAY_LAST_LIST = list(range(10))

    # --- 初期化 ---
    if "day_last_all" not in st.session_state:
        st.session_state.day_last_all = True

    for d in DAY_LAST_LIST:
        st.session_state.setdefault(f"day_last_{d}", False)

    # --- コールバック ---
    def on_day_last_all_change():
        if st.session_state.day_last_all:
            for d in DAY_LAST_LIST:
                st.session_state[f"day_last_{d}"] = False

    def on_day_last_change():
        if any(st.session_state[f"day_last_{d}"] for d in DAY_LAST_LIST):
            st.session_state.day_last_all = False
        else:
            st.session_state.day_last_all = True

    # --- UI（末尾日） ---
    labels = [str(d) for d in DAY_LAST_LIST] + [ALL]
    cols = st.columns([1] * (len(labels) - 1) + [2.8])

    for col, label in zip(cols, labels):
        if label == ALL:
            col.checkbox(
                label,
                key="day_last_all",
                on_change=on_day_last_all_change,
            )
        else:
            d = int(label)
            col.checkbox(
                label,
                key=f"day_last_{d}",
                on_change=on_day_last_change,
            )

    # --- 内部値（int の list） ---
    if st.session_state.day_last_all:
        day_last_list = None
    else:
        day_last_list = [d for d in DAY_LAST_LIST if st.session_state[f"day_last_{d}"]]

    # --------------------------------------------------
    # Filters（実行時反映）
    # --------------------------------------------------
    with st.form("filters", border=False):

        c4, c5, c8 = st.columns([1, 1, 0.6])

        with c4:
            N_DAYS_AGO = 10
            start_date = st.date_input("開始日", n_days_ago(N_DAYS_AGO))

        with c5:
            end_date = st.date_input("終了日", n_days_ago(1))

        with c8:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("実行", use_container_width=True)


if not submitted:
    st.stop()


# --------------------------------------------------
# 入力バリデーション
# --------------------------------------------------
if start_date > end_date:
    st.error("開始日が終了日より後になっています。日付を確認してください。")
    home_link()
    st.stop()


# --------------------------------------------------
# Fetch（ボタン押下後に実行）
# --------------------------------------------------
df = fetch_results_by_units(
    start_date,
    end_date,
    day_last=day_last_list,
    weekday=weekday_int_list,
    pref=pref,
    hall=hall,
    model=model,
    unit_no=unit_no,
)

# dfが空のときの KeyError 防止
if df is None or df.empty:
    st.info("条件に一致するデータがありません。")
    home_link()
    st.stop()


# --------------------------------------------------
# Perprocess df 前処理
# --------------------------------------------------
df = df.sort_values(["unit_no", "date"], ascending=[True, False])
df["bb_rate"] = df["game"] / df["bb"].replace(0, np.nan)
df["rb_rate"] = df["game"] / df["rb"].replace(0, np.nan)
bb_rb = df["bb"] + df["rb"]
df["total_rate"] = df["game"] / bb_rb.replace(0, np.nan)
df = calc_grape_rate(df, cherry=True)


# --------------------------------------------------
# Perprocess df テーブル用前処理
# --------------------------------------------------
df_table = df.copy()
df_table["weekday"] = pd.to_datetime(df_table["date"]).dt.strftime("%a")
df_table = df_table.round(1)
cols = [
    "date",
    "weekday",
    "unit_no",
    "game",
    "medal",
    "bb",
    "rb",
    "bb_rate",
    "rb_rate",
    "total_rate",
    "grape_rate",
]
df_table = df_table[cols]
# --------------------------------------------------
# Display Table
# --------------------------------------------------
if unit_no is not None:
    st.markdown(f"データ : {hall} {model} {unit_no} 番台")
if unit_no is None:
    st.markdown(f"データ : {hall} {model} すべて表示")
st.dataframe(df_table, width="stretch", height="auto", hide_index=True)


# --------------------------------------------------
# Perprocess df グラフ用前処理
# --------------------------------------------------
df_plot = df.copy()
df_plot["date_str"] = pd.to_datetime(df_plot["date"]).dt.strftime("%y-%m-%d %a")

TOTAL_MIN = 50
TOTAL_MAX = get_rb_rate_from_json(model, setting=1)
df_plot["total_rate_plot"] = np.where(
    df_plot["total_rate"].between(TOTAL_MIN, TOTAL_MAX), df_plot["total_rate"], np.nan
)
RB_MIN = 150
RB_MAX = get_rb_rate_from_json(model, setting=1)
df_plot["rb_rate_plot"] = np.where(
    df_plot["rb_rate"].between(RB_MIN, RB_MAX), df_plot["rb_rate"], np.nan
)

# --------------------------------------------------
# Display graph (台番号指定時)
# --------------------------------------------------
# 共通ツールチップ
common_tooltip = [
    alt.Tooltip("game:Q", title="回転数", format=","),
    alt.Tooltip("medal:Q", title="出玉数", format=","),
    alt.Tooltip("bb_rate:Q", title="BB確率", format=".1f"),
    alt.Tooltip("rb_rate:Q", title="RB確率", format=".1f"),
    alt.Tooltip("total_rate:Q", title="TOTAL", format=".1f"),
    alt.Tooltip("grape_rate:Q", title="GRAPE", format=".2f"),
]
# x軸(日付)
base = alt.Chart(df_plot).encode(x=alt.X("date_str:N", title="日付"))

# y軸(グラフ)
chart_game = base.mark_bar().encode(
    y=alt.Y("game:Q", title="回転数", scale=alt.Scale(domain=[0, 10000])),
    color=alt.Color(
        "medal:Q",
        title="メダル数",
        scale=alt.Scale(scheme="greys", domain=[-2000, 5000], reverse=True),
        legend=alt.Legend(orient="top", direction="horizontal", titleOrient="left"),
    ),
    tooltip=common_tooltip,
)

chart_rb = base.mark_point(size=40, opacity=0.9, color="cyan").encode(
    y=alt.Y(
        "rb_rate_plot:Q",
        title="RB確率",
        scale=alt.Scale(domain=[RB_MIN, RB_MAX]),
        axis=alt.Axis(format=".1f"),
    )
)

chart_total = base.mark_point(size=40, opacity=0.9, color="magenta").encode(
    y=alt.Y(
        "total_rate_plot:Q",
        title="TOTAL確率",
        axis=alt.Axis(format=".1f"),
    )
)

# 基準線
threshold = get_rb_rate_from_json(model, setting=5)
rb_rule = (
    alt.Chart(pd.DataFrame({"y": [threshold]}))
    .mark_rule(color="cyan", strokeDash=[4, 4])
    .encode(y="y:Q")
)
threshold = get_total_rate_from_json(model, setting=5)
total_rule = (
    alt.Chart(pd.DataFrame({"y": [threshold]}))
    .mark_rule(color="magenta", strokeDash=[4, 4])
    .encode(y="y:Q")
)

# 重ね合わせ
charts = chart_total + chart_rb + rb_rule + total_rule
chart = alt.layer(chart_game, charts).resolve_scale(y="independent")

if unit_no is not None:
    st.markdown(f"グラフ : {hall} {model} {unit_no} 番台")
    st.altair_chart(chart, width="stretch", height=500)


# --------------------------------------------------
# Perprocess df グラフ用前処理
# --------------------------------------------------
df_plot_all = df.copy()
df_plot_all["date_str"] = pd.to_datetime(df_plot_all["date"]).dt.strftime("%y-%m-%d %a")

# --------------------------------------------------
# Display graph (台番号すべて表示時)
# --------------------------------------------------
# y軸(グラフ)
x_date = alt.X("date_str:N", title="日付")
if unit_no is None:
    
    chunk_size = 15

    y_min = df["medal"].min()
    y_max = df["medal"].max()

    chunks = [units[i : i + chunk_size] for i in range(0, len(units), chunk_size)]
    for idx, unit_chunk in enumerate(chunks, start=1):
        df_chunk = df_plot_all[df_plot_all["unit_no"].isin(unit_chunk)].copy()

        sel = alt.selection_point(fields=["unit_no"], bind="legend", toggle=True)

        chart_medal = (
            alt.Chart(df_chunk)
            .mark_line(strokeWidth=0.5, point=alt.OverlayMarkDef(size=40))
            .encode(
                x=x_date,
                y=alt.Y(
                    "medal:Q",
                    title="medal",
                    axis=alt.Axis(tickMinStep=1000),
                    scale=alt.Scale(domain=[y_min, y_max]),
                ),
                tooltip=common_tooltip,
                color=alt.Color("unit_no:N"),
                opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
            )
            .add_params(sel)
            .properties(
                height=430
                # height=auto_height(unit_count)
            )
        )

        # chart_medal = chart_medal.properties(title=f"グラフ : {hall} {model} {unit_chunk[0]} を表示")
        unit_chunk_end = unit_chunk[-1]
        if unit_chunk[-1] == "すべて表示":
            unit_chunk_end = unit_chunk[-2]
        st.markdown(f"グラフ : {hall} {model} {unit_chunk[0]}～{unit_chunk_end} を表示")
        st.altair_chart(chart_medal)


home_link(position="right")
