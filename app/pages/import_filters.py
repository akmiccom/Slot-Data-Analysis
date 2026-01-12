import streamlit as st

from ui.filters import filters
from ui.components import home_link
from ui.charts import charts_on_unit_no, charts_on_all_model

from logic.preprocess import preprocess_for_table, preprocess_for_chart

from config.constants import KEY_MAP

from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units
from fetch_functions import fetch_results_by_units


# page_config（必ず最初）
page_title = "Sample UI"
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")
home_link(position="right")

# Title
st.subheader(page_title, divider="rainbow")

# filters
with st.expander("FILTER", expanded=True):
    submitted, fi = filters()
if not submitted:
    st.stop()
# st.write(filter_info)

# Fetch（ボタン押下後に実行） KEY_MAP from config
fetch_kwargs = {dst: fi[src] for src, dst in KEY_MAP.items()}

df = fetch_results_by_units(**fetch_kwargs)
if df is None or df.empty:
    st.info("条件に一致するデータがありません。")
    home_link()
    st.stop()


model = fi["model"]
unit_no = fi["unit_no"]

if unit_no is not None:
    # display graph
    expander_title = f"{fi['hall']}: {fi['model']}: No.{fi['unit_no']}"
    with st.expander(expander_title, expanded=True):
        df_chart = preprocess_for_chart(df, model)
        # st.dataframe(df_chart, hide_index=True)
        chart = charts_on_unit_no(df_chart, model)
        st.altair_chart(chart, height=500)

    # display table
    with st.expander(expander_title, expanded=False):
        df_table = preprocess_for_table(df)
        st.dataframe(df_table, hide_index=True)
        
else:
    expander_title = f"{fi['hall']}: {fi['model']}: すべて表示"
    charts = charts_on_all_model(df, model)
    with st.expander(expander_title, expanded=True):
        for chart in charts:
            st.altair_chart(chart, height=500)


home_link(position="right")