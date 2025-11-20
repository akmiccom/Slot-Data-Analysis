from supabase import create_client
import pandas as pd
import streamlit as st
import os

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(url, key)

res = (
    supabase
    .table("result_joined")
    .select("*")
    .limit(5)
    .execute()
)

st.write("res.error:", getattr(res, "error", None))
st.write("res.data first 5:", res.data)
if res.data:
    df_test = pd.DataFrame(res.data)
    st.write("df_test.columns:", df_test.columns.tolist())
