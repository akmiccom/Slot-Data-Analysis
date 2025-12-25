import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date, timedelta

from fetch_functions import fetch_results_by_units
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models

st.set_page_config(page_title="立ち回りビュー", layout="wide")


# ---------- ユーティリティ ----------
def compute_metrics(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date")
    d["rb_rate"] = np.where(d["rb"] > 0, d["game"] / d["rb"], np.nan).round(1)
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


# ---------- UI ----------
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
        hall = st.selectbox("halls", halls)
    with c3:
        models = fetch_models(pref=pref, hall=hall)
        model = st.selectbox("models", models)

    c5, c6, c7, c8 = st.columns([0.5, 0.5, 1.2, 1.2])
    with c5:
        day_last_list = [ALL] + [i for i in range(10)]
        day_last = st.selectbox("末尾日", day_last_list)
        if day_last == ALL:
            day_last = None
    with c6:
        weekdays = [ALL] + [i for i in range(7)]
        weekday = st.selectbox("曜日", weekdays)
        if weekday == ALL:
            weekday = None
    with c7:
        start_date = st.date_input("開始日", date.today() - timedelta(days=31))
    with c8:
        end_date = st.date_input("終了日", date.today())

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


# ---- 中段：時系列グラフ ----
common_tooltip = [
    alt.Tooltip("date_str:N", title="日付"),
    alt.Tooltip("unit_no:Q", title="unit_no"),
    alt.Tooltip("game:Q", title="G数", format=","),
    alt.Tooltip("medal:Q", title="メダル数", format=","),
    alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
    alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
    alt.Tooltip("medal_cum:Q", title="累計", format=","),
]
df = df.sort_values(["unit_no", "date"], ascending=[True, True])
x_date = alt.X("date_str:N", title="日付")

sel = alt.selection_point(fields=["unit_no"], bind="legend", toggle=True)

medal_cum = (
    alt.Chart(df)
    .mark_line(strokeWidth=0.5, point=alt.OverlayMarkDef(size=40))
    .encode(
        x=x_date,
        y=alt.Y(
            "medal_cum:Q",
            title="medal_cum",
            axis=alt.Axis(tickMinStep=5000),
        ),
        # color=alt.value("#d7abf5"),
        tooltip=common_tooltip,
        color=alt.Color("unit_no:N"),
        # legend=alt.Legend(title=f"unit_no",)
        opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
        # ),
    )
    .add_params(sel)
    .properties(
        height=500
        # title=f"{start_date}-{end_date}, {hall}, {model} 設定予測値（{idx}/{len(chunks)}）",
    )
)

chart = alt.layer(medal_cum).resolve_scale(y="independent")
if unit_no is ALL:
    chart = chart.properties(title=f"{model} をすべて表示")
    st.altair_chart(chart)


# ---- 中段：時系列グラフ（スマホでも読める。表より強い） ----
df = df.sort_values(["unit_no", "date"], ascending=[True, True])

# 日付ソートはユニークな順序を使う（重複で崩れるのを防ぐ）
date_order = df["date_str"].drop_duplicates().tolist()
x_date = alt.X("date_str:N", title="日付", sort=date_order)

# ツールチップは一本化（見たい情報をここへ）
common_tooltip = [
    alt.Tooltip("date_str:N", title="日付"),
    alt.Tooltip("game:Q", title="G数", format=","),
    alt.Tooltip("medal:Q", title="メダル数", format=","),
    alt.Tooltip("bb:Q", title="BB"),
    alt.Tooltip("rb:Q", title="RB"),
    alt.Tooltip("rb_rate:Q", title="RB確率"),
    # alt.Tooltip("medal_r3:Q", title="3日平均", format=","),
    # alt.Tooltip("medal_r7:Q", title="7日平均", format=","),
    # alt.Tooltip("medal_cum:Q", title="累計", format=","),
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

chart = alt.layer(medal, medal_r3 + medal_r7 + medal_cum).resolve_scale(y="independent")
if unit_no is not ALL:
    chart = chart.properties(title=f"台番号 : {unit_no}")
    st.altair_chart(chart, height=500)

# # ---- 下段：詳細テーブル（スマホは折りたたみ） ----
with st.expander("詳細（テーブル）"):
    pt = df.pivot_table(index=["unit_no"], columns=["date_str"], values=["medal"])
    st.dataframe(pt)

# # ---- 参考：全台サマリ（スマホは必要な時だけ） ----
# with st.expander("全台サマリ（直近ベース）"):
#     st.dataframe(
#         summary_df[["unit_no", "latest_date", "g_sum", "rb_rate", "medal_rate"]],
#         # use_container_width=True,
#         hide_index=True,
#     )
