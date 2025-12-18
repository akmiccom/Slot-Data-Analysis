from datetime import date, timedelta
import streamlit as st
from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units
from utils import validate_dates
import altair as alt
import pandas as pd


if __name__ == "__main__":

    title = "fetch from supabase"
    st.set_page_config(page_title=title, layout="wide")
    st.header(title, divider="rainbow")

    st.subheader("fetch_with_filter", divider="rainbow")

    # --- prefectures ---
    prefectures = fetch_prefectures()  # latest_models から都道府県だけユニーク取得
    pref = st.selectbox("prefectures", prefectures)

    # --- halls ---
    halls = fetch_halls(pref=pref)  # 都道府県でフィルタして Supabase から取得
    hall = st.selectbox("halls", halls)

    # --- models ---
    models = fetch_models(pref=pref, hall=hall)
    model = st.selectbox("models", models)

    # --- units ---
    units = fetch_units(pref=pref, hall=hall, model=model)
    unit_no = st.selectbox("units", units)

    # --- fetch_results_by_units ---
    today = date.today()
    n_d_ago = today - timedelta(days=5)
    yesterday = today - timedelta(days=1)
    ss = st.session_state
    ss.setdefault("start_date", n_d_ago)
    ss.setdefault("end_date", yesterday)
    start_date = st.date_input(
        "start", key="start_date", max_value=yesterday, on_change=validate_dates
    )
    end_date = st.date_input(
        "end", key="end_date", max_value=yesterday, on_change=validate_dates
    )
    df_result = fetch_results_by_units(start_date, end_date, pref, hall, model, unit_no)

    if df_result.empty:
        st.text("empty")
    else:
        st.dataframe(df_result, hide_index=True, width="stretch")

    import altair as alt
    import pandas as pd
    import streamlit as st

    # df の例（date は datetime 型が望ましい）
    df_result["date"] = pd.to_datetime(df_result["date"])
    df_result["date_str"] = df_result["date"].dt.strftime("%m-%d %a")

    chart_game = (
        alt.Chart(df_result)
        .mark_bar(opacity=0.3, color="orange")  # 棒グラフ
        .encode(
            x=alt.X("date_str:N", title="Date"),
            y=alt.Y("game:Q", title="Game Count"),
            tooltip=["date", "hall", "model", "unit_no"],
        )
        .properties(width="container", height=350)
    )
    chart_medal = (
        alt.Chart(df_result)
        .mark_circle(size=80)  # 散布図
        .mark_line(point=True)  # 散布図
        .encode(
            x=alt.X("date_str:N", title="Date"),
            # y="medal:Q",  # 縦軸：数値
            y=alt.Y("medal:Q", title="Medal"),
            # tooltip=["date", "hall", "model", "unit_no"]
        )
        # .properties(width="container", height=350)
    )
    chart = alt.layer(
        chart_game, chart_medal
    ).resolve_scale(
        y="independent"  # ← 縦軸を別に扱う（重要！）
    )

    st.altair_chart(chart)

    # --- fetch ---
    st.subheader("fetch_prefectures()", divider="rainbow")
    prefectures = fetch_prefectures()
    st.dataframe(prefectures, width="content", hide_index=True)

    st.subheader("fetch_halls(pref=None)", divider="rainbow")
    halls = fetch_halls()
    # df_show = halls.drop_duplicates("hall").sort_values("prefecture")
    st.dataframe(halls, height="auto", width="content", hide_index=True)

    st.subheader("fetch_models(pref=None, hall=None)", divider="rainbow")
    models = fetch_models()
    # df_show = df.drop_duplicates("model")["model"]
    st.dataframe(models, height="auto", width="content", hide_index=True)

    st.subheader("fetch_units(pref=None, hall=None, model=None)", divider="rainbow")
    # pref, hall, model = df.loc[0, ["prefecture", "hall", "model"]]
    units = fetch_units(pref=pref, hall=hall, model=model)
    st.text(f"{pref} : {hall} : {model} の台番号を取得")
    st.dataframe(units, height="auto", width="content", hide_index=True)

    st.subheader(
        "fetch_results_by_units(start, end, pref=None, hall=None, model=None, unit=None)",
        divider="rainbow",
    )
    today = date.today()
    start = today - timedelta(days=5)
    end = today - timedelta(days=1)
    df = fetch_results_by_units(start, end, pref, hall, model, units[0])
    st.text(f"{pref} : {hall} : {model} の結果を取得")
    st.dataframe(df, width="stretch", hide_index=True)
