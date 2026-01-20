# ui/filters.py
from __future__ import annotations

import streamlit as st

from config.constants import ALL_LABEL, PRIORITY_MODELS, PRIORITY_HALLS
from config.constants import WEEKDAY_STR, WEEKDAY_STR_TO_INT
from config.constants import INITIAL_PERIOD
from config.dates import initial_day_last, n_days_ago, prev_month_first

from ui.helpers import order_by_priority
from ui.exclusive_checkboxes import exclusive_checkbox_row

# from ui.exclusive_checkboxes import exclusive_checkbox_row_for_sidebar

from fetch_functions import fetch_prefectures, fetch_halls, fetch_models, fetch_units


def validate_dates():
    ss = st.session_state
    if ss.end_date < ss.start_date:
        ss.start_date = ss.end_date


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
            halls_raw = fetch_halls(pref=pref) or []
            halls = halls_raw
            hall_sel = st.selectbox("ホール", order_by_priority(halls, PRIORITY_HALLS))
            hall = None if hall_sel == ALL_LABEL else hall_sel

        with c3:
            models_raw = fetch_models(pref=pref, hall=hall) or []
            models = models_raw
            model_sel = st.selectbox("機種", order_by_priority(models, PRIORITY_MODELS))
            model = None if model_sel == ALL_LABEL else model_sel

        with c4:
            units_raw = fetch_units(pref=pref, hall=hall, model=model) or []
            if hall is not None:
                units = units_raw + [ALL_LABEL]  # 破壊しない
                unit_sel = st.selectbox("台番号", units)
                unit_no = None if unit_sel == ALL_LABEL else unit_sel
            else:
                unit_no = None

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

    filters = {
        "pref": pref,
        "hall": hall,
        "model": model,
        "unit_no": unit_no,
        "day_last_list": day_last_list,  # None or list[int]
        "weekday_int_list": weekday_int_list,  # None or list[int]
        "start_date": start_date,
        "end_date": end_date,
        "submitted": submitted,
    }

    return filters


def filters_for_sidebar(*, state_prefix: str = "filters") -> dict:
    """
    即時反映（pref/hall/model/unit + weekday/day_last）と、
    実行時反映（start/end + submit）をまとめて返す。
    """

    pref = st.sidebar.selectbox("都道府県", fetch_prefectures())

    halls_raw = fetch_halls(pref=pref) or []
    halls = halls_raw
    hall_sel = st.sidebar.selectbox("ホール", order_by_priority(halls, PRIORITY_HALLS))
    hall = None if hall_sel == ALL_LABEL else hall_sel

    models_raw = fetch_models(pref=pref, hall=hall) or []
    models = models_raw
    model_sel = st.sidebar.selectbox("機種", order_by_priority(models, PRIORITY_MODELS))
    model = None if model_sel == ALL_LABEL else model_sel

    unit_no = None
    units_raw = fetch_units(pref=pref, hall=hall, model=model) or []
    if hall is not None:
        units = sorted(units_raw) + [ALL_LABEL]  # 破壊しない
        unit_sel = st.sidebar.selectbox("台番号", units)
        unit_no = None if unit_sel == ALL_LABEL else unit_sel

    with st.sidebar.form(f"{state_prefix}__form", border=False):
        DAY_LAST_LABELS = {f"{i}のつく日": i for i in range(10)}

        day_last_sel = st.multiselect(
            "末尾日",
            options=list(DAY_LAST_LABELS.keys()),
            default=[f"{initial_day_last}のつく日"],
        )
        day_last_list = [DAY_LAST_LABELS[label] for label in day_last_sel]

        weekday_ja_sel = st.multiselect("曜日", WEEKDAY_STR, default=[])
        weekday_int_list = [WEEKDAY_STR_TO_INT[w] for w in weekday_ja_sel]

        prev_month = 3
        start_date = st.date_input("開始日", prev_month_first(prev_month))
        end_date = st.date_input("終了日", n_days_ago(1))

        submitted = st.form_submit_button("実行", use_container_width=True)

    if not day_last_list:
        day_last_list = None
    if not weekday_int_list:
        weekday_int_list = None

    filters = {
        "pref": pref,
        "hall": hall,
        "model": model,
        "unit_no": unit_no,
        "day_last_list": day_last_list,  # None or list[int]
        "weekday_int_list": weekday_int_list,  # None or list[int]
        "start_date": start_date,
        "end_date": end_date,
        "submitted": submitted,
    }

    return filters


# --------------------------------------------------
# filters for rb_rate chart
# --------------------------------------------------
def filters_for_rb_rate(*, state_prefix: str = "filters") -> dict:
    """
    即時反映（pref/hall/model/unit + weekday/day_last）と、
    実行時反映（start/end + submit）をまとめて返す。
    """
    with st.container(border=False):
        # -----------------------------
        # dependent selects (instant)
        # -----------------------------
        c1, c2, c3, c4 = st.columns([0.5, 1, 1, 1])

        with c1:
            pref = st.selectbox("都道府県", fetch_prefectures())

        # with c2:
        #     halls_raw = fetch_halls(pref=pref) or []
        #     halls = halls_raw
        #     hall_sel = st.selectbox("ホール", order_by_priority(halls, PRIORITY_HALLS))
        #     hall = None if hall_sel == ALL_LABEL else hall_sel

        with c2:
            models_raw = fetch_models(pref=pref, hall=None) or []
            models = models_raw
            model_sel = st.selectbox("機種", order_by_priority(models, PRIORITY_MODELS))
            model = None if model_sel == ALL_LABEL else model_sel

        with c3:
            prev_month = 3
            start_date = st.date_input("開始日", prev_month_first(prev_month))
        with c4:
            end_date = st.date_input("終了日", n_days_ago(1))

        c6, c7 = st.columns(2)

        with c6:
            DAY_LAST_LABELS = {f"{i}のつく日": i for i in range(10)}
            day_last_sel = st.multiselect(
                "末尾日",
                options=list(DAY_LAST_LABELS.keys()),
                default=[f"{initial_day_last}のつく日"],
            )
            day_last_list = [DAY_LAST_LABELS[label] for label in day_last_sel]

        with c7:
            weekday_ja_sel = st.multiselect("曜日", WEEKDAY_STR, default=[])
            weekday_int_list = [WEEKDAY_STR_TO_INT[w] for w in weekday_ja_sel]

    # 日付バリデーション（押下後に止める）
    if start_date > end_date:
        st.error("開始日が終了日より後になっています。日付を確認してください。")
        start_date = end_date

    if not day_last_list:
        day_last_list = None
    if not weekday_int_list:
        weekday_int_list = None

    filters = {
        "pref": pref,
        # "hall": None,
        "model": model,
        # "unit_no": None,
        "day_last_list": day_last_list,  # None or list[int]
        "weekday_int_list": weekday_int_list,  # None or list[int]
        "start_date": start_date,
        "end_date": end_date,
        # "submitted": submitted,
    }

    return filters


# --------------------------------------------------
# filters for history chart
# --------------------------------------------------
def filters_for_history(*, state_prefix: str = "filters") -> dict:
    """
    即時反映（pref/hall/model/unit + weekday/day_last）と、
    実行時反映（start/end + submit）をまとめて返す。
    """
    ss = st.session_state
    ss.setdefault("start_date", n_days_ago(10))
    ss.setdefault("end_date", n_days_ago(1))

    with st.container(border=False):
        # -----------------------------
        # dependent selects (instant)
        # -----------------------------
        c1, c2, c3, c4, c5, c6 = st.columns([0.5, 1, 1, 1, 1, 2])

        with c1:
            pref = st.selectbox("都道府県", fetch_prefectures())

        with c2:
            halls_raw = fetch_halls(pref=pref) or []
            halls = halls_raw
            hall_sel = st.selectbox("ホール", order_by_priority(halls, PRIORITY_HALLS))
            hall = None if hall_sel == ALL_LABEL else hall_sel

        with c3:
            models_raw = fetch_models(pref=pref, hall=None) or []
            models = models_raw
            model_sel = st.selectbox("機種", order_by_priority(models, PRIORITY_MODELS))
            model = None if model_sel == ALL_LABEL else model_sel

        with c6:
            # unit_no = None
            units = fetch_units(pref=pref, hall=hall, model=model) or []
            if hall is not None:
                units = sorted(units)
                unit_list = st.multiselect("台番号", units, default=units[0])
                # if not unit_list:
                #     unit_list = units[0]
                # unit_no = None if unit_sel == ALL_LABEL else unit_sel

        with c5:
            # start_date = st.date_input("検索日", n_days_ago(10))
            start_date = st.date_input(
                "検索開始日",
                key="start_date",
                max_value=n_days_ago(1),
                on_change=validate_dates,
            )

        with c4:
            # end_date = st.date_input("終了日", n_days_ago(1))
            end_date = st.date_input(
                "全台表示日",
                key="end_date",
                max_value=n_days_ago(1),
                on_change=validate_dates,
            )

        # c6, c7 = st.columns(2)

        # with c6:
        #     DAY_LAST_LABELS = {f"{i}のつく日": i for i in range(10)}
        #     day_last_sel = st.multiselect(
        #         "末尾日",
        #         options=list(DAY_LAST_LABELS.keys()),
        #         default=[f"{initial_day_last}のつく日"],
        #     )
        #     day_last_list = [DAY_LAST_LABELS[label] for label in day_last_sel]

        # with c7:
        #     weekday_ja_sel = st.multiselect("曜日", WEEKDAY_STR, default=[])
        #     weekday_int_list = [WEEKDAY_STR_TO_INT[w] for w in weekday_ja_sel]

    # 日付バリデーション（押下後に止める）
    if start_date > end_date:
        st.error("開始日が終了日より後になっています。日付を確認してください。")
        start_date = end_date

    # if not day_last_list:
    # day_last_list = None
    # if not weekday_int_list:
    # weekday_int_list = None

    filters = {
        "pref": pref,
        "hall": hall,
        "model": model,
        # "unit_no": unit_no,
        "unit_no": unit_list,
        "day_last_list": None,
        "weekday_int_list": None,
        "start_date": start_date,
        "end_date": end_date,
    }

    return filters
