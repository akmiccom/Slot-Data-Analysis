# --- 表示 ---
def auto_height(df):
    rows = len(df)
    row_height = 30  # 1行あたりの高さ（目安）
    base_height = 100  # ヘッダ・余白ぶん
    max_height = 800  # 上限（スクロール防止）
    height = min(base_height + rows * row_height, max_height)
    return height


# --- 条件付き書式設定 ---
def style_val(val):
    if isinstance(val, (int, float)) and val >= 1.02:
        # return "background-color: #ff3366; color: white; font-weight: bold;"   # 赤ピンク系（上位）
        # return "background-color: #ff9933; color: black; font-weight: bold;"   # オレンジ（良い）
        # return "background-color: #ffcc00; color: black; font-weight: bold;"   # 黄色（平均より上）
        # return "background-color: #33cc33; color: black; font-weight: bold;"   # 緑（標準）
        # return "background-color: #66ccff; color: black; font-weight: bold;"  # 水色（やや弱）
        return "background-color: #999999; color: white; font-weight: bold;"   # グレー（低調）
    else:
        return ""


def style_val(val):
    if isinstance(val, (int, float)) and val >= 1.02:
        return "background-color: #66ccff; color: black; font-weight: bold;"  # 水色（やや弱）
    else:
        return ""
    
    
def make_style_val(threshold=1.02):
    def style_val(val):
        if isinstance(val, (int, float)) and val >= threshold:
            return "background-color: #999999; color: white; font-weight: bold;"
        return ""
    return style_val