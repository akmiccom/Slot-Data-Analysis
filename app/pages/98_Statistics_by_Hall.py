import pandas as pd
import streamlit as st
import altair as alt

from fetch_functions import get_supabase_client, _fetch_all_rows
from fetch_functions import fetch_prefectures
from utils import auto_height, make_style_val


supabase = get_supabase_client()

page_title = "Statistics_by_Hall"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")

st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")

st.subheader("Medal Rate by Hall")
# query = supabase.table("medal_rate_by_hall").select("*")
# rows = _fetch_all_rows(query)
# df = pd.DataFrame(rows).round(1)
# st.dataframe(df)

col1, col2 = st.columns(2)
with col1:
    prefectures = fetch_prefectures()
    pref = st.selectbox("都道府県を選択", prefectures)

    query = (
        supabase.table("medal_rate_by_hall")
        .select("day_last,count,hall,medal_rate,prefecture,avg_game")
        .eq("prefecture", pref)
    )
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    df = df[df["prefecture"] == pref]
    pivot = df.pivot_table(index="hall", columns="day_last", values="medal_rate")


with col2:
    value_list = [100.0, 100.5, 101.0, 101.5, 102.0]
    threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
    # --- style ---
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )

# --- graph ---
df = df[df["count"] >= df["count"].quantile(0.15)]
df = df[df["medal_rate"] >= threshold_value]
df["medal_rate"] = df["medal_rate"].round(1)
df["avg_game"] = df["avg_game"].round(1)

y_min = df["medal_rate"].min() - 0.2
y_max = df["medal_rate"].max() + 0.2

sel = alt.selection_point(fields=["hall"], bind="legend", toggle=True)

line = (
    alt.Chart(df)
    # .mark_line(point=True)
    .mark_circle(size=120, opacity=0.8)
    .encode(
        x=alt.X("day_last:Q", title="末尾日", axis=alt.Axis(tickMinStep=1, format="d")),
        y=alt.Y(
            "medal_rate:Q",
            title="medal_rate",
            axis=alt.Axis(tickMinStep=0.5, format=".1f"),
            scale=alt.Scale(domain=[y_min, y_max]),
        ),
        color=alt.Color("hall:N", legend=alt.Legend(title="hall")),
        opacity=alt.condition(sel, alt.value(1.0), alt.value(0.08)),
        tooltip=["hall", "day_last", "medal_rate", "avg_game"],
    )
    .add_params(sel)
    .properties(height=500)
)


# --- display ---
st.write(f"出玉率{threshold_value}%以上(クリックでホール選択）")
st.altair_chart(line)
st.dataframe(df_styled, width="stretch", height=auto_height(pivot))