import os
from supabase import Client

from config import config
from utils.logger_setup import setup_logger

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def get_hall_id(supabase: Client, pref: str, hall: str) -> int | None:
    """既存DBから prefecture + hall に一致する hall_id を取得する。"""
    pref_res = (
        supabase.table("prefectures")
        .select("prefecture_id")
        .eq("name", pref)
        .limit(1)
        .execute()
    )
    if not pref_res.data:
        return None

    prefecture_id = pref_res.data[0]["prefecture_id"]
    hall_res = (
        supabase.table("halls")
        .select("hall_id")
        .eq("name", hall)
        .eq("prefecture_id", prefecture_id)
        .limit(1)
        .execute()
    )
    if not hall_res.data:
        return None
    return hall_res.data[0]["hall_id"]


def count_results_by_hall_date(supabase: Client, hall_id: int, date: str) -> int:
    """results の hall_id + date 単位の既存行数を取得する。"""
    res = (
        supabase.table("results")
        .select("hall_id", count="exact")
        .eq("hall_id", hall_id)
        .eq("date", date)
        .limit(1)
        .execute()
    )
    if getattr(res, "count", None) is not None:
        return int(res.count)
    return len(res.data or [])


def has_enough_results(
    supabase: Client,
    pref: str,
    hall: str,
    date: str,
    min_existing_rows: int = 10,
) -> tuple[bool, int, int | None]:
    """hall_id + date の既存件数が閾値以上なら取得済みとみなす。"""
    hall_id = get_hall_id(supabase, pref, hall)
    if hall_id is None:
        logger.info("DB未登録ホールのため取得対象にします: %s / %s / %s", pref, hall, date)
        return False, 0, None

    existing_count = count_results_by_hall_date(supabase, hall_id, date)
    should_skip = existing_count >= min_existing_rows
    return should_skip, existing_count, hall_id
