from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt

from data_from_supabase import get_supabase_client, _fetch_all_rows
from utils import calc_grape_rate, predict_setting, continuous_setting
from utils import auto_height, make_style_val


column_config = {
    "date": st.column_config.DateColumn(width=80),
    "hall": st.column_config.Column(width=80),
    "model": st.column_config.Column(width=70),
    "day_last": st.column_config.NumberColumn(width=30),
    "count": st.column_config.NumberColumn(width=30),
    "unit_no": st.column_config.NumberColumn(width=60),
    "rb_rate": st.column_config.NumberColumn(width=50),
    "medal_rate": st.column_config.NumberColumn(width=50),
    "win_rate": st.column_config.NumberColumn(width=50),
    "avg_madal": st.column_config.NumberColumn(width=50),
    "avg_game": st.column_config.NumberColumn(width=50),
    "grape_rate": st.column_config.NumberColumn(width=50),
    "weight_setting": st.column_config.NumberColumn(width=50),
    "pred_setting": st.column_config.NumberColumn(width=50),
    "bb": st.column_config.NumberColumn(width=30),
    "rb": st.column_config.NumberColumn(width=30),
}


# --- title ---
page_title = "台番号別の履歴データ"
st.set_page_config(page_title=page_title, page_icon="", layout="wide")
st.page_link("Slot_Data_Analysis.py", label="HOME", icon="🏠")
st.subheader(page_title, divider="rainbow")
st.markdown(
    """
    ページの使い方説明
            """
)


# --- fetch ---
supabase = get_supabase_client()


@st.cache_data
def fetch(start_date, end_date, pref=None, hall=None, model=None):
    ALL = "すべて"
    query = supabase.table("latest_units_results").select("*")
    query = query.gte("date", start_date)
    query = query.lte("date", end_date)
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        # query = query.eq("hall", hall)
        query = query.in_("hall", [hall])
    if model not in (None, ALL):
        # query = query.eq("model", model)
        query = query.in_("model", [model])
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    return df


today = date.today()
n_d_ago = today - timedelta(days=7)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    start = st.date_input("start date", n_d_ago)
with col2:
    end = st.date_input("end date", today)
with col3:
    query = supabase.table("latest_models").select("*")
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    prefectures = df["prefecture"].value_counts().index.tolist()
    pref = st.selectbox("都道府県を選択", prefectures)
    df = df[df["prefecture"] == pref]
with col4:
    halls = df["hall"].unique().tolist()
    hall = st.selectbox("ホールを選択", halls)
    df = df[df["hall"] == hall]
with col5:
    models = df["model"].unique().tolist()
    model = st.selectbox("機種を選択", models)
    # model = st.multiselect("機種を選択", models)
    # df = df[df["hall"] == hall]

# if st.button("Submit"):
df = fetch(start, end, pref=pref, hall=hall, model=model)
df = df.sort_values(["date", "unit_no"], ascending=[False, True])
df = calc_grape_rate(df)
df["weight_setting"] = df.apply(
    lambda r: continuous_setting(
        r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
    ),
    axis=1,
).round(1)

idx = ["hall", "model", "unit_no"]
vals = ["game", "medal", "bb", "rb", "grape_rate", "weight_setting"]
cols = ["date"]
agg = "sum"
pt = df.pivot_table(index=idx, columns=cols, aggfunc=agg, values=vals)
pt = pt.iloc[:, ::-1]
interleaved_cols = [
    (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
]
pt = pt[interleaved_cols]
pt = pt.swaplevel(0, 1, axis=1)
st.dataframe(pt, column_config=column_config)


# col1, col2 = st.columns(2)
# with col1:
#     value_list = [3, 4, 5]
#     threshold_value = st.pills("出玉率を選択", value_list, default=value_list[1])
#     pivot = df.pivot_table(index=["hall", "model", "unit_no"], columns=["date"], values=["weight_setting"])
#     pivot = pivot.iloc[:, ::-1]
#     style_func = make_style_val(threshold_value)
#     num_cols = pivot.select_dtypes(include="number").columns
#     df_styled = pivot.style.map(style_func, subset=num_cols).format(
#         {col: "{:.1f}" for col in num_cols}
#     )

# st.dataframe(df_styled, height=auto_height(pivot), width="stretch")

# with col2:
#     value_list = [3000, 4000, 5000, 6000]
#     threshold_value = st.pills("回転数を選択", value_list, default=value_list[1])
#     pivot = df.pivot_table(index=["hall", "model", "unit_no"], columns=["date"], values=["game"])
#     pivot = pivot.iloc[:, ::-1]
#     style_func = make_style_val(threshold_value)
#     num_cols = pivot.select_dtypes(include="number").columns
#     df_styled = pivot.style.map(style_func, subset=num_cols).format(
#         {col: "{:.1f}" for col in num_cols}
#     )

# st.dataframe(df_styled, height=auto_height(pivot), width="stretch")

# medal = df.pivot_table(index=["hall", "model", "unit_no"], columns=["date"], values=["medal"])
# medal = medal.iloc[:, ::-1]
# st.dataframe(medal, height=auto_height(medal), width="stretch")
