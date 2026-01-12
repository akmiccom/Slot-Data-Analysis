import pandas as pd
import altair as alt

from logic.preprocess import preprocess_for_chart
from logic.cal_rates import get_rb_rate, get_total_rate

from config.constants import RB_MIN


# 共通ツールチップ
common_tooltip = [
    alt.Tooltip("date_str:N", title="日付"),
    alt.Tooltip("unit_no:N", title="台番号"),
    alt.Tooltip("game:Q", title="回転数", format=","),
    alt.Tooltip("medal:Q", title="出玉数", format=","),
    alt.Tooltip("bb_rate:Q", title="BB確率", format=".1f"),
    alt.Tooltip("rb_rate:Q", title="RB確率", format=".1f"),
    alt.Tooltip("total_rate:Q", title="TOTAL", format=".1f"),
    alt.Tooltip("grape_rate:Q", title="GRAPE", format=".2f"),
]


def charts_on_unit_no(df, model):

    df = preprocess_for_chart(df, model)

    # x軸(日付)
    base = alt.Chart(df).encode(x=alt.X("date_str:N", title="日付"))

    # y軸(グラフ)
    chart_game = base.mark_bar().encode(
        y=alt.Y("game:Q", title="GAME", scale=alt.Scale(domain=[0, 10000])),
        color=alt.Color(
            "medal:Q",
            title="MEDAL",
            scale=alt.Scale(scheme="greys", domain=[-2000, 5000], reverse=True),
            legend=alt.Legend(orient="top", direction="horizontal", titleOrient="left"),
        ),
        tooltip=common_tooltip,
    )

    RB_MAX = get_rb_rate(model, setting=1)
    chart_rb = base.mark_point(size=40, opacity=0.9, color="cyan").encode(
        y=alt.Y(
            "rb_rate_plot:Q",
            title="RB_RATE",
            scale=alt.Scale(domain=[RB_MIN, RB_MAX]),
            axis=alt.Axis(format=".1f"),
        )
    )

    chart_total = base.mark_point(size=40, opacity=0.9, color="magenta").encode(
        y=alt.Y(
            "total_rate_plot:Q",
            title="TOTAL_RATE",
            axis=alt.Axis(format=".1f"),
        )
    )

    # 基準線
    threshold = get_rb_rate(model, setting=5)
    rb_rule = (
        alt.Chart(pd.DataFrame({"y": [threshold]}))
        .mark_rule(color="cyan", strokeDash=[4, 4])
        .encode(y="y:Q")
    )
    threshold = get_total_rate(model, setting=5)
    total_rule = (
        alt.Chart(pd.DataFrame({"y": [threshold]}))
        .mark_rule(color="magenta", strokeDash=[4, 4])
        .encode(y="y:Q")
    )

    # 重ね合わせ
    charts = chart_rb + chart_total + rb_rule + total_rule
    chart = alt.layer(chart_game, charts).resolve_scale(y="independent")

    return chart


def charts_on_all_model(df, model):

    df = preprocess_for_chart(df, model)

    # x軸(日付)
    x_date = alt.X("date_str:N", title="日付")

    chunk_size = 20

    y_min = df["medal"].min()
    y_max = df["medal"].max()

    units = sorted(df["unit_no"].unique().tolist())
    chunks = [units[i : i + chunk_size] for i in range(0, len(units), chunk_size)]

    charts = []
    for idx, unit_chunk in enumerate(chunks, start=1):
        df_chunk = df[df["unit_no"].isin(unit_chunk)].copy()

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
        )
        charts.append(chart_medal)

    return charts
