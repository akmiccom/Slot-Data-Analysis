import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta
from dateutil import relativedelta

from utils import WEEKDAY_JA, WEEKDAY_JA_TO_INT
from utils import auto_height
from utils import today, yesterday, n_days_ago, prev_month_first
from fetch_functions import fetch_results_by_units
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models

st.set_page_config(page_title="立ち回りビュー", layout="wide")


# ---------- ユーティリティ ----------
def compute_metrics(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date")
    d["bb_rate"] = np.where(d["bb"] > 0, d["game"] / d["rb"], np.nan).round(1)
    d["rb_rate"] = np.where(d["rb"] > 0, d["game"] / d["rb"], np.nan).round(1)
    d["total_rate"] = np.where(
        (d["bb"] + d["rb"]) > 0, d["game"] / (d["bb"] + d["rb"]), np.nan
    ).round(1)
    d["medal_rate"] = np.where(
        d["game"] > 0, (d["game"] * 3 + d["medal"]) / (d["game"] * 3) * 100, np.nan
    ).round(1)
    d["date_str"] = d["date"].dt.strftime("%m/%d %a")
    d["medal_cum"] = (
        d.sort_values(["unit_no", "date"], ascending=[True, True])
        .assign(medal=lambda d: d["medal"].fillna(0))
        .groupby(["hall", "model", "unit_no"])["medal"]
        .cumsum()
    )
    d["medal_r3"] = (
        d.sort_values("date", ascending=True)
        .groupby(["hall", "model", "unit_no"], sort=False)["medal"]
        .transform(lambda s: s.rolling(3, min_periods=3).sum())
    )
    d["medal_r7"] = (
        d.sort_values("date", ascending=True)
        .groupby(["hall", "model", "unit_no"], sort=False)["medal"]
        .transform(lambda s: s.rolling(7, min_periods=7).sum())
    )

    return d


def summarize_unit(d: pd.DataFrame, rolling_days=3) -> dict:
    # 直近rolling_daysの合計/平均で“今日の判断”に寄せる
    tail = d.tail(rolling_days)
    g = float(tail["game"].sum())
    rb = float(tail["rb"].sum())
    rb_rate = (g / rb) if rb > 0 else np.nan
    medal_rate = float(tail["medal_rate"].mean())
    latest_date = tail["date"].max().strftime("%m-%d (%a)")
    return {
        "latest_date": latest_date,
        "g_sum": g,
        "rb_sum": rb,
        "rb_rate": rb_rate,
        "medal_rate": medal_rate,
    }


def auto_height(n):
    rows = n
    row_height = 30  # 1行あたりの高さ（目安）
    base_height = 100  # ヘッダ・余白ぶん
    max_height = 1000  # 上限（スクロール防止）
    height = min(base_height + rows * row_height, max_height)
    height = base_height + rows * row_height
    if height >= 750:
        height = 750
    elif height <= 480:
        height = 480
    return height


# ---------- UI ----------
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader("メダル推移", divider="rainbow")

# スマホは横幅が狭いので「フォーム→実行」型にすると操作が楽
with st.form("filters", border=True):
    ALL = "すべて表示"
    c1, c2, c3, c4 = st.columns([0.5, 1.2, 1.2, 0.7])
    with c1:
        prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
        pref = st.selectbox("都道府県", prefectures)
    with c2:
        halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
        hall = st.selectbox("ホール", halls)
    with c3:
        models = fetch_models(pref=pref, hall=hall)
        model = st.selectbox("機種", models)

    c5, c6, c7, c8 = st.columns([0.5, 0.5, 1.2, 1.2])
    with c5:
        day_last_list = [ALL] + [i for i in range(10)]
        day_last = st.selectbox("末尾日", day_last_list)
        if day_last == ALL:
            day_last = None
    with c6:
        # weekdays = [ALL] + [i for i in range(7)]
        # weekday = st.selectbox("曜日", weekdays)
        # if weekday == ALL:
        #     weekday = None
        weekdays = [ALL] + WEEKDAY_JA
        weekday_ja = st.selectbox("曜日", weekdays)
        weekday = WEEKDAY_JA_TO_INT[weekday_ja] if weekday_ja != ALL else None
    with c7:
        start_date = st.date_input("開始日", prev_month_first(1))
    with c8:
        end_date = st.date_input("終了日", yesterday)

    # ---- データ読み込み ----
    with st.spinner("データ取得中..."):
        df = fetch_results_by_units(
            start_date,
            end_date,
            day_last=day_last,
            weekday=weekday,
            pref=pref,
            hall=hall,
            model=model,
        )
    with c4:
        units = [ALL] + sorted(df["unit_no"].unique().tolist())
        unit_no = st.selectbox("台番号", units)
        if unit_no != ALL:
            df = df[df["unit_no"] == unit_no].copy()
        df = compute_metrics(df)
        df = df.sort_values(["unit_no", "date"], ascending=[True, False])

    submitted = st.form_submit_button("表示")

if not submitted:
    st.stop()


common_tooltip = [
    alt.Tooltip("date_str:N", title="日付"),
    alt.Tooltip("unit_no:Q", title="unit_no"),
    alt.Tooltip("game:Q", title="G数", format=","),
    alt.Tooltip("medal:Q", title="メダル数", format=","),
    alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
    alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
    alt.Tooltip("medal_cum:Q", title="累計", format=","),
]
# df = df.sort_values(["unit_no", "date"], ascending=[True, True])
date_order = df["date_str"].drop_duplicates().tolist()[::-1]
# st.write(date_order)
x_date = alt.X("date_str:N", title="日付", sort=date_order)
# st.write(x_date)

if unit_no == ALL:

    chunk_size = 10

    y_min = df["medal_cum"].min() - 0.2
    y_max = df["medal_cum"].max() + 0.2

    chunks = [units[i : i + chunk_size] for i in range(0, len(units), chunk_size)]
    for idx, unit_chunk in enumerate(chunks, start=1):
        df_chunk = df[df["unit_no"].isin(unit_chunk)].copy()

        sel = alt.selection_point(fields=["unit_no"], bind="legend", toggle=True)

        medal_cum = (
            alt.Chart(df_chunk)
            .mark_line(strokeWidth=0.5, point=alt.OverlayMarkDef(size=40))
            .encode(
                x=x_date,
                y=alt.Y(
                    "medal_cum:Q",
                    title="medal_cum",
                    axis=alt.Axis(tickMinStep=5000),
                    scale=alt.Scale(domain=[y_min, y_max]),
                ),
                tooltip=common_tooltip,
                color=alt.Color("unit_no:N"),
                opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
            )
            .add_params(sel)
            .properties(
                height=380
                # height=auto_height(unit_count)
            )
        )

        chart = alt.layer(medal_cum).resolve_scale(y="independent")
        # if unit_no is ALL:
        chart = chart.properties(title=f"{model} をすべて表示")
        st.altair_chart(chart)

else:
    # ---- 中段：時系列グラフ（スマホでも読める。表より強い） ----
    # df = df.sort_values(["unit_no", "date"], ascending=[True, True])

    # 日付ソートはユニークな順序を使う（重複で崩れるのを防ぐ）
    # date_order = df["date"].drop_duplicates().tolist()
    # st.write(date_order)
    # x_date = alt.X("date_str:N", title="日付", sort=date_order)

    # ツールチップは一本化（見たい情報をここへ）
    common_tooltip = [
        alt.Tooltip("date_str:N", title="日付"),
        alt.Tooltip("game:Q", title="G数", format=","),
        alt.Tooltip("medal:Q", title="メダル数", format=","),
        alt.Tooltip("bb:Q", title="BB"),
        alt.Tooltip("rb:Q", title="RB"),
        alt.Tooltip("rb_rate:Q", title="RB確率"),
        alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
        alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
        alt.Tooltip("medal_cum:Q", title="累計", format=","),
    ]

    # ① medal（棒）：背景として薄く
    medal = (
        alt.Chart(df)
        .mark_bar(opacity=0.5)
        .encode(
            x=x_date,
            y=alt.Y("medal:Q", title="メダル数"),
            color=alt.value("steelblue"),
            tooltip=common_tooltip,
        )
    )

    medal_r3 = (
        alt.Chart(df)
        .mark_line(strokeWidth=1.2, point=alt.OverlayMarkDef(size=20))
        .encode(
            x=x_date,
            y=alt.Y("medal_r3:Q", title="移動平均"),
            color=alt.value("#73a1eb"),
            tooltip=[
                alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
                alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
            ],
        )
    )

    medal_r7 = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=40))
        .encode(
            x=x_date,
            y=alt.Y("medal_r7:Q"),
            color=alt.value("#73b9c7"),
            tooltip=[
                alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
                alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
            ],
        )
    )

    medal_cum = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=60))
        .encode(
            x=x_date,
            y=alt.Y("medal_cum:Q"),
            color=alt.value("#d7abf5"),
            tooltip=[alt.Tooltip("medal_cum:Q", title="メダル累計", format=",")],
        )
    )

    # ① game（棒）：背景として薄く
    game = (
        alt.Chart(df)
        .mark_bar(opacity=0.3)
        .encode(
            x=x_date,
            y=alt.Y("game:Q", title="回転数"),
            color=alt.value("gray"),
            # color="Species:N",
            tooltip=common_tooltip,
        )
    )

    rb_rate = (
        alt.Chart(df[df["rb_rate"] <= 500])
        # alt.Chart(df)
        # .mark_line(point=alt.OverlayMarkDef(size=60))
        .mark_point(size=40, opacity=0.9).encode(
            x=x_date,
            y=alt.Y(
                "rb_rate:Q",
                title="RB確率",
                scale=alt.Scale(domain=[150, 500]),
            ),
            color=alt.value("cyan"),
            # color=alt.Color("rb_rate:Q"),
            tooltip=[alt.Tooltip("rb_rate:Q", title="RB確率", format=".1f")],
        )
    )

    # ターゲットRB確率ライン
    from utils import get_rb_rate_from_json

    threshold = get_rb_rate_from_json(model, setting=5)
    rule = (
        alt.Chart(pd.DataFrame({"y": [threshold]}))
        .mark_rule(color="red", strokeDash=[4, 4])
        .encode(y="y:Q")
    )

    lines = medal_r3 + medal_r7 + medal_cum
    chart_medal = alt.layer(medal, lines).resolve_scale(y="independent")
    chart_medal = chart_medal.properties(
        title=f"{model} {unit_no} 番台 メダル分析", height=250
    )

    rb_layer = rb_rate + rule
    chart_rb_rate = alt.layer(rb_layer, game).resolve_scale(y="independent")
    chart_rb_rate = chart_rb_rate.properties(
        title=f"{model} {unit_no} 番台 RB分析 (1/500以下は非表示)", height=250
    )

    chart = chart_medal & chart_rb_rate

    if unit_no is not ALL:
        # st.altair_chart(chart_rb_rate, height=380)
        st.altair_chart(chart)

# st.dataframe(df)

# # ---- 下段：詳細テーブル（スマホは折りたたみ） ----
with st.expander("グラフデータ"):
    df = df.sort_values("date", ascending=False)
    cols = [
        "unit_no",
        "date_str",
        "game",
        "medal",
        "bb",
        "rb",
        "bb_rate",
        "rb_rate",
        "total_rate",
        "medal_cum",
        "medal_r3",
        "medal_r7",
    ]
    st.dataframe(df[cols], hide_index=True)

# with st.expander("詳細"):
#     pt_medal = df.pivot_table(index=["unit_no"], columns=["date_str"], values=["medal"])
#     st.dataframe(pt_medal)
# with st.expander("Game"):
#     pt_game = df.pivot_table(index=["unit_no"], columns=["date_str"], values=["game"])
#     st.dataframe(pt_game)
# with st.expander("RB_rate"):
#     pt_rb = df.pivot_table(index=["unit_no"], columns=["date_str"], values=["rb"])
#     pt_bb = df.pivot_table(index=["unit_no"], columns=["date_str"], values=["bb"])
#     st.dataframe(pt_rb)
#     pt_rb_rate = pt_game / pt_rb
# with st.expander("RB_rate"):
#     st.dataframe(pt_rb_rate)

# # ---- 参考：全台サマリ（スマホは必要な時だけ） ----
# with st.expander("全台サマリ（直近ベース）"):
#     st.dataframe(
#         summary_df[["unit_no", "latest_date", "g_sum", "rb_rate", "medal_rate"]],
#         # use_container_width=True,
#         hide_index=True,
#     )
