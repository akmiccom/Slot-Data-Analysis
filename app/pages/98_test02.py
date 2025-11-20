from supabase import create_client
import pandas as pd
import streamlit as st
import os

import os
import streamlit as st
from supabase import create_client, Client
from data_from_supabase import get_supabase_client


# supabase = get_supabase_client()

# res = supabase.table("result_joined").select("*").limit(5).execute()

# st.write("res.error:", getattr(res, "error", None))
# st.write("res.data first 5:", res.data)
# if res.data:
#     df_test = pd.DataFrame(res.data)
#     st.write("df_test.columns:", df_test.columns.tolist())


supabase = get_supabase_client()
query = (
    supabase.table("result_joined")
    .select("date,hall,model,unit_no,game,bb,rb,medal,day_last")
)
res = query.execute()
st.write("res.data (first 5):", res.data[:5])
# エラー情報があれば
if hasattr(res, "error"):
    st.write("res.error:", res.error)

df = pd.DataFrame(res.data)
st.write("df.columns:", df.columns.tolist())

st.dataframe(df.head())