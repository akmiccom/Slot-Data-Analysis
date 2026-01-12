from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

"""
日付処理に関する関数など
"""

# --- 日付 ---
today = date.today()
yesterday = date.today() - timedelta(days=1)

# --- n日前を指定 ---
def n_days_ago(n):
    return date.today() - timedelta(days=n)


# --- nが月前の1日を指定 ---
def prev_month_first(n):
    return date(date.today().year, date.today().month, 1) - relativedelta(months=n)