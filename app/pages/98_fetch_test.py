import streamlit as st
import pandas as pd
import datetime
from data_from_supabase import get_supabase_client
from data_from_supabase import fetch, fetch_one_day, fetch_latest, _fetch_all_rows



title = "fetch_test"
st.set_page_config(page_title=title, layout="wide")
st.header(title)

st.subheader('supabase access test')
supabase = get_supabase_client()
query = (
    supabase.table("result_joined")
    .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
)
res = query.execute()
if hasattr(res, "error"):
    st.write("res.error:", res.error)
df = pd.DataFrame(res.data)
st.dataframe(df, width="stretch", height=100, hide_index=True)

st.subheader("func fetch")
view = "result_joined"
start = "2025-11-17"
end = "2025-11-20"
hall = "マルハン池袋店"
model = "マイジャグラーV"
day_last = 3
df_fetch = fetch(view, start, end, hall, model, day_last)
st.dataframe(df_fetch, width="stretch", height=100, hide_index=True)

st.subheader("func fetch_one_day")
target_date = "2025-11-18"
df_fetch_one_day = fetch_one_day(view, target_date)
st.dataframe(df_fetch_one_day, width="stretch", height=100, hide_index=True)

st.subheader("func fetch_latest")
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
n_d_ago = yesterday - datetime.timedelta(days=3)
df_latest = fetch(view, n_d_ago, yesterday)
df_unique = (
    df[["hall", "model", "unit_no"]]
    .drop_duplicates()
    .sort_values(["hall", "model", "unit_no"])
)
st.dataframe(df_unique, width="stretch", height=100, hide_index=True)



st.subheader("func fetch_latest 2")
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
n_d_ago = yesterday - datetime.timedelta(days=3)

query = (
    supabase.table("result_joined")
    .select("hall,model,unit_no")
    .gte("date", n_d_ago)
    .lte("date", yesterday)
)
rows = _fetch_all_rows(query)
df_latest = pd.DataFrame(rows)
df_unique = (
    df_latest[["hall", "model", "unit_no"]]
    .drop_duplicates()
    .sort_values(["hall", "model", "unit_no"])
)
st.dataframe(df_unique, width="stretch", height=500, hide_index=True)
st.text(len(df_unique))

halls  = df_unique["hall"].unique().tolist()
models = df_unique["model"].unique().tolist()
units  = df_unique["unit_no"].unique().tolist()

query = (
    supabase.table("result_joined")
    .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
    .gte("date", n_d_ago)
    .lte("date", yesterday)
    .in_("hall", halls)
    .in_("model", models)
    .in_("unit_no", units)
)
rows = _fetch_all_rows(query)
df_final = pd.DataFrame(rows).sort_values(["hall", "model", "unit_no"])
st.dataframe(df_final, width="stretch", height=500, hide_index=True)
st.text(len(df_final))
