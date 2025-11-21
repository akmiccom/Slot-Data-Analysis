import streamlit as st
import pandas as pd

from data_from_supabase import get_supabase_client


title = "fetch_test"
st.set_page_config(page_title=title, layout="wide")
st.subheader(title)

supabase = get_supabase_client()
query = (
    supabase.table("result_joined")
    .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
)
res = query.execute()
# st.write("res.data (first 5):", res.data[:5])
# エラー情報があれば
if hasattr(res, "error"):
    st.write("res.error:", res.error)

df = pd.DataFrame(res.data)
# st.write("df.columns:", df.columns.tolist())
st.dataframe(df, width="stretch", hide_index=True)