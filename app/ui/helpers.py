# ui/helpers.py
"""
Streamlit を import しない関数
単体テスト可能な関数
UIと完全に独立している
"""


# --- 優先順位付き並び替え ---
def order_by_priority(items: list[str], priority: list[str]) -> list[str]:
    """priority にあるものを先頭に（存在しないものは無視）、残りは元の順で後ろへ。"""
    if not items:
        return []
    ordered = [x for x in priority if x in items]
    others = [x for x in items if x not in priority]
    return ordered + others