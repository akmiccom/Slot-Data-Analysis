from supabase import create_client
import pandas as pd
import streamlit as st
import os

import os
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    # 1. まず st.secrets を優先（Cloud / secrets.toml）
    url = None
    key = None

    if "SUPABASE_URL" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
    if "SUPABASE_ANON_KEY" in st.secrets:
        key = st.secrets["SUPABASE_ANON_KEY"]

    # 2. st.secrets に無ければ環境変数から取得（ローカル用）
    if url is None:
        url = os.environ.get("SUPABASE_URL")
    if key is None:
        key = os.environ.get("SUPABASE_ANON_KEY")

    # 3. どちらにもなければエラー
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_ANON_KEY が見つかりません。secrets か環境変数を確認してください。"
        )

    return create_client(url, key)


supabase = get_supabase_client()
res = supabase.table("result_joined").select("*").limit(5).execute()

st.write("res.error:", getattr(res, "error", None))
st.write("res.data first 5:", res.data)
if res.data:
    df_test = pd.DataFrame(res.data)
    st.write("df_test.columns:", df_test.columns.tolist())
