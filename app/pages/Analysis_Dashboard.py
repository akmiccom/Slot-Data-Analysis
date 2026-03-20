import os
import streamlit as st

from ui.components import home_link
from ui.charts import charts_on_unit_no
from ui.filters import filters_for_rb_rate
from ui.filters import filters
from fetch_functions import fetch_results_by_units
from logic.preprocess import preprocess_for_table
from pages.rb_probability_by_unit import rb_prob_by_unit
from config.dates import n_days_ago, yesterday, prev_month_first


def reslut_by_unit(sel_rows, selected):
    if sel_rows and selected:
        day_last_list = selected["day_last_list"]
        if not selected["day_last_list"]:
            day_last_list = None
        weekday_int_list = selected["weekday_int_list"]
        if not selected["weekday_int_list"]:
            weekday_int_list = None
        # クリックした行の台を表示する
        expander_title = (
            f"{selected['hall']}: {selected['model']}: No.{selected['unit_no']}"
        )
        with st.expander(expander_title, expanded=True):
            df_unit = fetch_results_by_units(
                selected["start_date"],
                selected["end_date"],
                day_last=day_last_list,
                weekday=weekday_int_list,
                pref=selected["pref"],
                hall=selected["hall"],
                model=selected["model"],
                unit_no=[selected["unit_no"]],
            )
            if df_unit is None or df_unit.empty:
                st.info("選択した台のデータがありません。")
            else:
                chart = charts_on_unit_no(df_unit, selected["model"])
                st.altair_chart(chart, width="stretch")

        with st.expander("詳細テーブル", expanded=False):
            if df_unit is not None and not df_unit.empty:
                df_table = preprocess_for_table(df_unit)
                st.dataframe(df_table, hide_index=True, width="stretch")
        home_link(position="right")

    else:
        expander_title = f"RB確率一覧から台を選択してください"
        st.write(expander_title)
        home_link(position="right")
        st.stop()


# page_config
page_title = os.path.splitext(os.path.basename(__file__))[0]
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

home_link(position="left")

st.header(page_title)

# fi = filters_for_rb_rate()

PAST_N_DAYS = 10

ss = st.session_state
ss.setdefault("start_date", prev_month_first(3))
ss.setdefault("end_date", yesterday)

fi = filters(
    state_prefix="page_a",
    start_date_default = prev_month_first(3),
    visible_fields={
        "pref",
        # "hall",
        "model",
        # "unit_no",
        "day_last_list",
        "weekday_int_list",
        "start_date",
        "end_date",
    },
)

r1c1, r1c2 = st.columns([1, 2], gap="small")

with r1c1:
    sel_rows, selected = rb_prob_by_unit(fi)

with r1c2:
    reslut_by_unit(sel_rows, selected)