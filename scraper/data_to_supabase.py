import os
import pandas as pd
from supabase import create_client, Client

import config

import os

SUPABASE_URL = os.environ["SUPABASE_URL"]
# SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
# SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]



# def get_supabase_client() -> Client:
#     url = os.environ.get("SUPABASE_URL")
#     key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
#     # if not url or not key:
#     #     raise RuntimeError(
#     #         "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY が設定されていません。"
#     #     )
#     return create_client(url, key)


# if __name__ == "__main__":
#     df = pd.read_csv(config.CSV_DIR / "cleaned_all_result_data.csv")
    
#     supabase = get_supabase_client()
    
