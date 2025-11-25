import streamlit as st
import pandas as pd
import datetime
from data_from_supabase import get_supabase_client, _fetch_all_rows, get_latest_data
from data_from_supabase import fetch, fetch_one_day, fetch_latest
from data_from_supabase import fetch_halls, fetch_models



title = "fetch_test"
st.set_page_config(page_title=title, layout="wide")
st.header(title, divider="rainbow")



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
start = "2025-11-01"
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
start, end = "2025-11-18", "2025-11-20"
df_unique, df_final, halls = get_latest_data(view, start, end)
st.dataframe(df_unique, width="stretch", height=100, hide_index=True)
st.text(len(df_unique))
st.dataframe(df_final, width="stretch", height="auto", hide_index=True)
st.text(len(df_final))
# st.write(halls)
# st.write(models)
