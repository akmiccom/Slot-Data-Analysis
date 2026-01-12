# config/constants.py

"""
UI・ロジック横断の定数を集約
"""

# UI表示
ALL_LABEL = "すべて表示"
INITIAL_PERIOD = 11
KEY_MAP = {
    "start_date": "start_date",
    "end_date": "end_date",
    "day_last_list": "day_last",
    "weekday_int_list": "weekday",
    "pref": "pref",
    "hall": "hall",
    "model": "model",
    "unit_no": "unit_no",
}

# 曜日
WEEKDAY_STR = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKDAY_STR_TO_INT = {ja: i for i, ja in enumerate(WEEKDAY_STR)}

# 末尾日
DAY_LAST_LIST = list(range(10))

# 優先順
PRIORITY_HALLS = [
    "エスパス日拓渋谷駅前新館",
    "エスパス日拓渋谷本館",
    "楽園渋谷駅前店",
    "楽園渋谷道玄坂店",
    "楽園ハッピーロード大山",
    "大山オーシャン",
    "YASUDA5",
    "マルハン大山店",
    "マルハン池袋店",
    "YASUDA9",
    "楽園池袋店グリーンサイド",
    "楽園池袋店",
    "コンサートホールエフ成増",
    "エクサファースト",
    "マルハン青梅新町店",
]

PRIORITY_MODELS = [
    "ネオアイムジャグラーEX",
    "ゴーゴージャグラー3",
    "マイジャグラーV",
    "ジャグラーガールズ",
    "ファンキージャグラー2",
]


RB_MIN = 50
TOTAL_MIN = 50
