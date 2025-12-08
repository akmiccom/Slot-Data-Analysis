from datetime import date, timedelta
import pandas as pd
import streamlit as st
import altair as alt

from fetch_functions import get_supabase_client, _fetch_all_rows
# from utils import validate_dates
from utils import calc_grape_rate, predict_setting, continuous_setting
from utils import auto_height, make_style_val
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units
from utils import validate_dates, rotate_list_by_today


INTIAL_PERIOD = 3

column_config = {
    "date": st.column_config.DateColumn(width=80),
    "hall": st.column_config.Column(width=150),
    "model": st.column_config.Column(width=70),
    "day_last": st.column_config.NumberColumn(width=30),
    "count": st.column_config.NumberColumn(width=30),
    "unit_no": st.column_config.NumberColumn(width=60),
    "rb_rate": st.column_config.NumberColumn(width=50),
    "medal_rate": st.column_config.NumberColumn(width=50),
    "win_rate": st.column_config.NumberColumn(width=50),
    "avg_madal": st.column_config.NumberColumn(width=50),
    "avg_game": st.column_config.NumberColumn(width=50),
    "grape_rate": st.column_config.NumberColumn(width=60),
    "weight_setting": st.column_config.NumberColumn(width=60),
    "pred_setting": st.column_config.NumberColumn(width=50),
    "game": st.column_config.NumberColumn(width=50),
    "medal": st.column_config.NumberColumn(width=50),
    "bb": st.column_config.NumberColumn(width=40),
    "rb": st.column_config.NumberColumn(width=40),
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
@st.cache_data
def fetch(start_date, end_date, pref=None, hall=None, model=None):
    ALL = "すべて"
    supabase = get_supabase_client()
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
n_d_ago = today - timedelta(days=INTIAL_PERIOD)

ss = st.session_state
ss.setdefault("start_date", n_d_ago)
ss.setdefault("end_date", today)

# col1, col2, col3, col4, col5 = st.columns(5)
# with col1:
#     prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
#     pref = st.selectbox("prefectures", prefectures)
# with col2:
#     halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
#     hall = st.selectbox("halls", halls)
# with col3:
#     models = fetch_models(pref=pref, hall=hall)
#     model = st.selectbox("models", models)
# with col4:
#     start_date = st.date_input(
#         "検索開始日", key="start_date", max_value=today, on_change=validate_dates
#     )
# with col5:
#     end_date = st.date_input(
#         "検索終了日", key="end_date", max_value=today, on_change=validate_dates
#     )

st.subheader("ホール別履歴")
col1, col2, col3, col4 = st.columns(4)
with col1:
    prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
    pref = st.selectbox("都道府県", prefectures)
with col2:
    ALL = "すべて"
    # day_last_list = [ALL] + [i for i in range(10)]
    # day_last = st.selectbox("day_last", day_last_list)
    day_lasts = [ALL] + rotate_list_by_today([i for i in range(10)])
    day_last = st.selectbox("末尾日", day_lasts)
with col3:
    halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
    hall = st.selectbox("halls", halls)
with col4:
    models = fetch_models(pref=pref, hall=hall)
    model = st.selectbox("models", models)
    
col5, col6 = st.columns(2)
with col5:
    start_date = st.date_input(
        "検索開始日", key="start_date", max_value=today, on_change=validate_dates
    )
with col6:
    end_date = st.date_input(
        "検索終了日", key="end_date", max_value=today, on_change=validate_dates
    )


tab1, tab2 = st.tabs(["一覧表示", "個別表示"])

with tab1:
    # --- hall history ---
    df = fetch_results_by_units(start_date, end_date, pref)
    if day_last is not ALL:
        df = df[df["day_last"] == day_last]
    idx = ["hall"]
    # vals = ["game", "medal", "bb", "rb"]
    vals = ["game", "medal"]
    cols = ["date"]
    func = "mean"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.round(0)
    pt = pt.swaplevel(0, 1, axis=1)
    pt_hall = pt

    # --- model history ---
    df = fetch_results_by_units(start_date, end_date, pref, hall)
    if day_last is not ALL:
        df = df[df["day_last"] == day_last]
    df = calc_grape_rate(df)
    df["weight_setting"] = df.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    )
    df["weight_setting"] = pd.to_numeric(df["weight_setting"], errors="coerce").round(1)
    idx = ["hall", "model"]
    # vals = ["game", "medal", "bb", "rb", "grape_rate", "weight_setting"]
    vals = ["game", "medal", "weight_setting"]
    cols = ["date"]
    func = "mean"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.round(1)
    pt = pt.swaplevel(0, 1, axis=1)
    pt_model = pt

    # --- unit history ---
    df = fetch_results_by_units(start_date, end_date, pref, hall, model)
    if day_last is not ALL:
        df = df[df["day_last"] == day_last]
    df = df.sort_values(["date", "unit_no"], ascending=[False, True])
    df = calc_grape_rate(df)
    df["weight_setting"] = df.apply(
        lambda r: continuous_setting(
            r["game"], r["rb"], r["bb"], r["grape_rate"], r["model"]
        ),
        axis=1,
    )
    df["weight_setting"] = pd.to_numeric(df["weight_setting"], errors="coerce").round(1)

    idx = ["hall", "model", "unit_no"]
    vals = ["game", "medal", "bb", "rb", "grape_rate", "weight_setting"]
    cols = ["date"]
    func = "sum"
    pt = df.pivot_table(index=idx, columns=cols, aggfunc=func, values=vals)
    pt = pt.iloc[:, ::-1]
    interleaved_cols = [
        (i, j) for j in pt.columns.get_level_values(1).unique() for i in vals
    ]
    pt = pt[interleaved_cols]
    pt = pt.swaplevel(0, 1, axis=1)    
    pt_unit = pt
    
    
    st.subheader("台番号別履歴")
    if not pt_unit.empty:
        column_config["hall"] = st.column_config.Column(width=40)
        column_config["model"] = st.column_config.Column(width=40)
        column_config["unit_no"] = st.column_config.NumberColumn(width=70)
        st.dataframe(pt_unit, column_config=column_config)
    st.subheader("モデル別履歴")
    if not pt_model.empty:
        column_config["hall"] = st.column_config.Column(width=50)
        column_config["model"] = st.column_config.Column(width=100)
        st.dataframe(pt_model, column_config=column_config)
    st.subheader("ホール別履歴")
    if not pt_hall.empty:
        column_config["hall"] = st.column_config.Column(width=150)
        st.dataframe(pt_hall, column_config=column_config)

with tab2:
    column_config["hall"] = st.column_config.Column(width=40)
    column_config["model"] = st.column_config.Column(width=40)
    column_config["unit_no"] = st.column_config.NumberColumn(width=70)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("予測設定の履歴", divider="rainbow")
    with col2:
        value_list = [3, 4, 5]
        threshold_value = st.pills(
            "設定予測値を選択", value_list, default=value_list[1]
        )
        pivot = df.pivot_table(
            index=["hall", "model", "unit_no"],
            columns=["date"],
            values=["weight_setting"],
        )
        pivot = pivot.iloc[:, ::-1]
        style_func = make_style_val(threshold_value)
        num_cols = pivot.select_dtypes(include="number").columns
        df_styled = pivot.style.map(style_func, subset=num_cols).format(
            {col: "{:.1f}" for col in num_cols}
        )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("回転数の履歴", divider="rainbow")
        value_list = [3000, 4000, 5000, 6000]
    with col2:
        threshold_value = st.pills("回転数を選択", value_list, default=value_list[1])
    pivot = df.pivot_table(
        index=["hall", "model", "unit_no"], columns=["date"], values=["game"]
    )
    pivot = pivot.iloc[:, ::-1]
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("出玉数の履歴", divider="rainbow")
        value_list = [0, 100, 200, 300, 500]
    with col2:
        threshold_value = st.pills("出玉数を選択", value_list, default=value_list[1])
    pivot = df.pivot_table(
        index=["hall", "model", "unit_no"], columns=["date"], values=["medal"]
    )
    pivot = pivot.iloc[:, ::-1]
    style_func = make_style_val(threshold_value)
    num_cols = pivot.select_dtypes(include="number").columns
    df_styled = pivot.style.map(style_func, subset=num_cols).format(
        {col: "{:.1f}" for col in num_cols}
    )
    st.dataframe(
        df_styled,
        column_config=column_config,
        height=auto_height(pivot),
        width="stretch",
    )
