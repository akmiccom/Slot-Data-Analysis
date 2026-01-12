# ui/filters.py
from __future__ import annotations

import streamlit as st

from config.constants import ALL_LABEL, PRIORITY_MODELS, PRIORITY_HALLS
from config.constants import WEEKDAY_STR, WEEKDAY_STR_TO_INT
from config.constants import INITIAL_PERIOD
from config.dates import n_days_ago

from ui.helpers import order_by_priority
from ui.exclusive_checkboxes import exclusive_checkbox_row

from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units


# --------------------------------------------------
# main UI (filters)
# --------------------------------------------------
def filters(*, state_prefix: str = "filters") -> dict:
    """
    即時反映（pref/hall/model/unit + weekday/day_last）と、
    実行時反映（start/end + submit）をまとめて返す。
    """
    with st.container(border=False):
        # -----------------------------
        # dependent selects (instant)
        # -----------------------------
        c1, c2, c3, c4 = st.columns([0.6, 1.0, 1.0, 0.7])

        with c1:
            pref = st.selectbox("都道府県", fetch_prefectures())

        with c2:
            halls = fetch_halls(pref=pref)
            hall = st.selectbox("ホール", order_by_priority(halls, PRIORITY_HALLS))

        with c3:
            models = fetch_models(pref=pref, hall=hall)
            model = st.selectbox("機種", order_by_priority(models, PRIORITY_MODELS))

        with c4:
            units_raw = fetch_units(pref=pref, hall=hall, model=model) or []
            units = units_raw + [ALL_LABEL]  # 破壊しない
            unit_sel = st.selectbox("台番号", units)
            unit_no = None if unit_sel == ALL_LABEL else unit_sel

        # -----------------------------
        # weekday (exclusive)
        # -----------------------------
        weekday_int_list = exclusive_checkbox_row(
            prefix=f"{state_prefix}__weekday",
            items=WEEKDAY_STR,
            all_label=ALL_LABEL,
            all_col_weight=2.0,
            item_col_weight=1.0,
            default_all=True,
            item_to_value=WEEKDAY_STR_TO_INT,
        )

        # -----------------------------
        # day_last (exclusive)
        # -----------------------------
        day_last_items = [str(i) for i in range(10)]
        day_last_list = exclusive_checkbox_row(
            prefix=f"{state_prefix}__day_last",
            items=day_last_items,
            all_label=ALL_LABEL,
            all_col_weight=2.8,
            item_col_weight=1.0,
            default_all=True,
            item_to_value=None,  # 数値文字列→int
        )

        # -----------------------------
        # run form (submit)
        # -----------------------------
        with st.form(f"{state_prefix}__run", border=False):
            c5, c6, c7 = st.columns([1, 1, 0.6])

            with c5:
                start_date = st.date_input("開始日", n_days_ago(INITIAL_PERIOD))
            with c6:
                end_date = st.date_input("終了日", n_days_ago(1))
            with c7:
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("実行", use_container_width=True)

    # 日付バリデーション（押下後に止める）
    if submitted and start_date > end_date:
        st.error("開始日が終了日より後になっています。日付を確認してください。")
        submitted = False

    fitlers = {
        "pref": pref,
        "hall": hall,
        "model": model,
        "unit_no": unit_no,
        "weekday_int_list": weekday_int_list,  # None or list[int]
        "day_last_list": day_last_list,  # None or list[int]
        "start_date": start_date,
        "end_date": end_date,
    }

    return submitted, fitlers
