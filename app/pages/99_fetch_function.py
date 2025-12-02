import streamlit as st
import pandas as pd
from datetime import date, timedelta
from data_from_supabase import get_supabase_client, _fetch_all_rows


@st.cache_data
def get_prefectures():
    query = supabase.table("prefectures").select("name")
    rows = _fetch_all_rows(query)
    prefectures = [row["name"] for row in rows]
    return prefectures


@st.cache_data
def get_halls(pref=None):
    ALL = "すべて"
    query = supabase.table("latest_models").select("prefecture,hall")
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    halls = df["hall"].value_counts().index.tolist()
    return halls


@st.cache_data
def get_model(pref=None, hall=None):
    ALL = "すべて"
    query = supabase.table("latest_models").select("prefecture,hall,model")
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    models = df["model"].value_counts().index.tolist()
    return models


@st.cache_data
def get_units(pref=None, hall=None, model=None):
    ALL = "すべて"
    query = supabase.table("latest_units_per_hall").select("*")
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    if model not in (None, ALL):
        query = query.eq("model", model)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    units = df["unit_no"].unique().tolist()
    return units


@st.cache_data
def get_results_by_units(pref=None, hall=None, model=None, unit_no=None, period=5):
    ALL = "すべて"
    start_date = date.today() - timedelta(days=period + 1)
    end_date = date.today() - timedelta(days=1)
    query = supabase.table("latest_units_results").select("*")
    query = query.gte("date", start_date)
    query = query.lte("date", end_date)
    if pref not in (None, ALL):
        query = query.eq("prefecture", pref)
    if hall not in (None, ALL):
        query = query.eq("hall", hall)
    if model not in (None, ALL):
        query = query.eq("model", model)
    if unit_no not in (None, ALL):
        query = query.eq("unit_no", unit_no)
    rows = _fetch_all_rows(query)
    df = pd.DataFrame(rows)
    df = df.drop("day_last", axis=1)
    results = df[df["unit_no"] == unit_no]
    return results


if __name__ == "__main__":

    title = "fetch from supabase"
    st.set_page_config(page_title=title, layout="wide")
    st.header(title, divider="rainbow")

    # --- fetch ---
    supabase = get_supabase_client()

    st.subheader("get_prefectures()", divider="rainbow")

    prefectures = get_prefectures()
    st.write(prefectures)

    st.subheader("get_halls(pref=None)", divider="rainbow")

    halls = get_halls(pref=prefectures[0])
    st.text(f"{prefectures[0]} のホールを取得")
    st.write(halls)

    st.subheader("get_model(pref=None, hall=None)", divider="rainbow")

    models = get_model(pref=prefectures[0], hall=halls[0])
    st.text(f"{prefectures[0]} : {halls[0]} のモデルを取得")
    st.write(models)

    st.subheader("get_units(pref=None, hall=None, model=None)", divider="rainbow")

    units = get_units(pref=prefectures[0], hall=halls[0], model=models[0])
    st.text(f"{prefectures[0]} : {halls[0]} : {models[2]} の最新台番号を取得")
    st.write(units)

    st.subheader(
        "get_results_by_units(pref=None, hall=None, model=None, unit_no=None, period=5)",
        divider="rainbow",
    )

    df = get_results_by_units(prefectures[0], halls[0], models[0], units[0], 5)
    st.text(f"{prefectures[0]} : {halls[0]} : {models[2]} の結果を取得")
    st.dataframe(df, width="stretch", hide_index=True)
