from supabase import create_client
import pandas as pd
import streamlit as st
import os

def get_supabase_client():
    """supabese のクライアントを取得"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    # key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY が設定されていません。")
    return create_client(url, key)

supabase = get_supabase_client()

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
