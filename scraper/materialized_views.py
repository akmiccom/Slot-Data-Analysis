import os

from supabase import Client

from config import config
from utils.logger_setup import setup_logger

filename, ext = os.path.splitext(os.path.basename(__file__))
logger = setup_logger(filename, log_file=config.LOG_PATH)


def refresh_materialized_views(supabase: Client) -> None:
    """マテリアライズドビュー更新用の枠。

    更新SQL/RPC名が確定したら、ここから Supabase RPC を呼び出す。
    既存SQL・view・materialized view はこの変更では更新しない。
    """
    logger.info("マテビュー更新は未実装です。RPC確定後にここへ実装します。")
    # TODO: supabase.rpc("refresh_xxx_materialized_views").execute()
