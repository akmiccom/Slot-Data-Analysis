# ui/exclusive_checkboxes.py
import streamlit as st
from config.constants import ALL_LABEL


def _init_exclusive_group_state(
    prefix: str, items: list[str], default_all: bool = True
) -> None:
    """排他チェックボックスの session_state 初期化"""
    all_key = f"{prefix}__all"
    st.session_state.setdefault(all_key, default_all)

    for it in items:
        st.session_state.setdefault(f"{prefix}__{it}", False)


def exclusive_checkbox_row(
    *,
    prefix: str,
    items: list[str],
    all_label: str = ALL_LABEL,
    all_col_weight: float = 2.0,
    item_col_weight: float = 1.0,
    default_all: bool = True,
    item_to_value: dict[str, int] | None = None,
) -> list[int] | None:
    """
    1行横並びの排他チェックボックス。
    - all をONにすると他がOFF
    - 他をONにすると all がOFF
    戻り値:
      - None: フィルタしない（すべて）
      - list[int]: 選択された値
    """
    if not items:
        # 項目が無いならフィルタしない（=すべて）
        return None

    _init_exclusive_group_state(prefix, items, default_all=default_all)

    all_key = f"{prefix}__all"

    # --- callbacks (closure) ---
    def on_all_change():
        if st.session_state[all_key]:
            for it in items:
                st.session_state[f"{prefix}__{it}"] = False

    def on_item_change():
        any_on = any(st.session_state[f"{prefix}__{it}"] for it in items)
        st.session_state[all_key] = not any_on

    labels = items + [all_label]
    weights = [item_col_weight] * len(items) + [all_col_weight]
    cols = st.columns(weights)

    for col, label in zip(cols, labels):
        if label == all_label:
            col.checkbox(all_label, key=all_key, on_change=on_all_change)
        else:
            col.checkbox(label, key=f"{prefix}__{label}", on_change=on_item_change)

    # --- build output ---
    if st.session_state[all_key]:
        return None

    if item_to_value is None:
        # items がすでに数値文字列なら int へ
        out: list[int] = []
        for it in items:
            if st.session_state[f"{prefix}__{it}"]:
                try:
                    out.append(int(it))
                except ValueError:
                    # 数値化できない場合は無視（ここは用途に応じて変更可）
                    pass
        return out

    # map 変換（曜日など）
    return [item_to_value[it] for it in items if st.session_state[f"{prefix}__{it}"]]


def exclusive_checkbox_row_for_sidebar(
    *,
    prefix: str,
    items: list[str],
    all_label: str = ALL_LABEL,
    all_col_weight: float = 2.0,
    item_col_weight: float = 1.0,
    default_all: bool = True,
    item_to_value: dict[str, int] | None = None,
) -> list[int] | None:
    """
    1行横並びの排他チェックボックス。
    - all をONにすると他がOFF
    - 他をONにすると all がOFF
    戻り値:
      - None: フィルタしない（すべて）
      - list[int]: 選択された値
    """
    if not items:
        # 項目が無いならフィルタしない（=すべて）
        return None

    _init_exclusive_group_state(prefix, items, default_all=default_all)

    all_key = f"{prefix}__all"

    # --- callbacks (closure) ---
    def on_all_change():
        if st.session_state[all_key]:
            for it in items:
                st.session_state[f"{prefix}__{it}"] = False

    def on_item_change():
        any_on = any(st.session_state[f"{prefix}__{it}"] for it in items)
        st.session_state[all_key] = not any_on

    labels = items + [all_label]
    weights = [item_col_weight] * len(items) + [all_col_weight]
    cols = st.columns(weights)

    for col, label in zip(cols, labels):
        if label == all_label:
            col.checkbox(all_label, key=all_key, on_change=on_all_change)
        else:
            col.checkbox(label, key=f"{prefix}__{label}", on_change=on_item_change)

    # --- build output ---
    if st.session_state[all_key]:
        return None

    if item_to_value is None:
        # items がすでに数値文字列なら int へ
        out: list[int] = []
        for it in items:
            if st.session_state[f"{prefix}__{it}"]:
                try:
                    out.append(int(it))
                except ValueError:
                    # 数値化できない場合は無視（ここは用途に応じて変更可）
                    pass
        return out

    # map 変換（曜日など）
    return [item_to_value[it] for it in items if st.session_state[f"{prefix}__{it}"]]
