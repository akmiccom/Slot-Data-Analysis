import streamlit as st

from config.constants import KEY_MAP
from config.dates import prev_month_first
from ui.filters import filters
from ui.components import home_link
from ui.charts import charts_on_unit_no, charts_on_all_model
from logic.preprocess import preprocess_for_table, preprocess_for_rb_rate

from fetch_functions import fetch_results_by_units


# page_config（必ず最初）
page_title = "Dashboard"
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

# Title
st.title(page_title)

r1c1, r1c2 = st.columns([1, 2], gap="small")

with r1c1:
    # filters
    with st.expander("FILTER", expanded=True):
        submitted, fi = filters()
    
    # RB_RATE_LIST
    if fi["day_last_list"] is not None or fi["weekday_int_list"] is not None:
        prev_month = 3
        with st.expander(f"{fi['model']} RB確率 ({prev_month}ヶ月集計)", expanded=True):
            # st.subheader(f"RB確率 : {prev_month}ヶ月集計")
            df_for_rb = fetch_results_by_units(
                prev_month_first(prev_month),
                fi["end_date"],
                day_last=fi["day_last_list"],
                weekday=fi["weekday_int_list"],
                pref=fi["pref"],
                hall=None,
                model=fi["model"],
            )
            df_rb_rate = preprocess_for_rb_rate(df_for_rb)
            st.dataframe(df_rb_rate, height=600)
    else:
        with st.expander(f"RB確率 : 曜日もしくは末尾日を選択してください", expanded=False):
            st.write("曜日もしくは末尾日を選択してください" )
    
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

with r1c2:

    # 台別表示
    if unit_no is not None:
        # display graph
        expander_title = f"{fi['hall']}: {fi['model']}: No.{fi['unit_no']}"
        with st.expander(expander_title, expanded=True):
            chart = charts_on_unit_no(df, model)
            st.altair_chart(chart, height=500)
        # display table
        with st.expander(expander_title, expanded=True):
            df_table = preprocess_for_table(df)
            st.dataframe(df_table, hide_index=True)

    # 全台表示
    else:
        # display graph
        expander_title = f"{fi['hall']}: {fi['model']}: すべて表示"
        charts = charts_on_all_model(df, model)
        with st.expander(expander_title, expanded=True):
            for chart in charts:
                st.altair_chart(chart, height=500)
        # display table
        with st.expander(expander_title, expanded=False):
            df_table = preprocess_for_table(df)
            st.dataframe(df_table, hide_index=True)

    # 全機種表示の時


home_link(position="right")
