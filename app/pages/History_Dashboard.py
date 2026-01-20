import os
import pandas as pd
import altair as alt
import streamlit as st

from config.constants import KEY_MAP
from config.dates import n_days_ago
from ui.filters import filters_for_history
from ui.components import home_link
from ui.charts import charts_on_unit_no
from logic.preprocess import preprocess, preprocess_for_chart

from fetch_functions import fetch_results_by_units

from pages.rb_probability_by_unit import rb_prob_by_unit

from config.constants import RB_MIN
from logic.cal_rates import get_rb_rate, get_total_rate

from ui.helpers import order_by_priority
from config.constants import ALL_LABEL, PRIORITY_MODELS, PRIORITY_HALLS


# page_config
# page_title = "Analysis Dashboard"
page_title = os.path.splitext(os.path.basename(__file__))[0]
st.set_page_config(page_title=page_title, page_icon="📊", layout="wide")

# filters
fi = filters_for_history()

c1, c2 = st.columns(2, gap="small")

with c1:
    st.subheader("単日 ✕ 全台", divider="rainbow")
    df = fetch_results_by_units(
        fi["end_date"],
        fi["end_date"],
        pref=fi["pref"],
        hall=fi["hall"],
    )
    if df is None or df.empty:
        st.info("選択した条件のデータがありません。")
        home_link(position="left")
        st.stop()

    models = df["model"].unique().tolist()
    models = order_by_priority(models, PRIORITY_MODELS)

    for model in models:
        df_model = df[df["model"] == model]
        count = df_model["unit_no"].nunique()
        expander_title = f"{fi['hall']}: {model}: {count}台: {fi['end_date']}"
        with st.expander(expander_title, expanded=True):
            charts = charts_on_unit_no(df_model, model, single_day=True)
            st.altair_chart(charts, width="stretch")
    home_link(position="left")


with c2:
    st.subheader("複数日 ✕ 台番号", divider="rainbow")
    if fi["start_date"] == fi["end_date"]:
        st.info("開始日と終了日を異なる日にすると複数日履歴表示が可能です。")
    else:
        df = fetch_results_by_units(
            fi["start_date"],
            n_days_ago(1),
            pref=fi["pref"],
            hall=fi["hall"],
            model=fi["model"],
            unit_no=fi["unit_no"],
        )
        if df is None or df.empty:
            st.info("台番号を選択してください。")
            # st.stop()
        else:
            for unit_no in fi["unit_no"]:
                df_unit = df[df["unit_no"] == unit_no]
                if df_unit is None or df_unit.empty:
                    st.info(f"台番号 {unit_no} のデータがありません。")
                    continue
                else:
                    expander_title = f"{fi['hall']}: {fi['model']}: {unit_no}"
                    with st.expander(expander_title, expanded=True):
                        charts = charts_on_unit_no(df_unit, fi['model'], single_day=False)
                        st.altair_chart(charts, width="stretch")

    home_link(position="right")
