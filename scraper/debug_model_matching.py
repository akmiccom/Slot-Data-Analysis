from __future__ import annotations

import sys

from utils.target_models import build_alias_to_canonical, match_target_model_detail

SAMPLES = {
    "ネオアイムジャグラーEX": "ネオアイムジャグラーEX",
    "SネオアイムジャグラーEX": "ネオアイムジャグラーEX",
    "SアイムジャグラーEX": "アイムジャグラーEX-TP",
    "アイムジャグラーEX": "アイムジャグラーEX-TP",
    "ゴーゴージャグラー３": "ゴーゴージャグラー3",
    "ファンキージャグラー２ＫＴ": "ファンキージャグラー2",
    "ハッピージャグラーＶＩＩＩ": "ハッピージャグラーVIII",
    "マイジャグラーV": "マイジャグラーV",
}


def main() -> int:
    alias_to_canonical = build_alias_to_canonical()
    failed = False

    for raw_model_name, expected in SAMPLES.items():
        match = match_target_model_detail(raw_model_name, alias_to_canonical)
        actual = match.canonical_name if match else None
        status = "OK" if actual == expected else "NG"
        details = (
            f"normalized_model_name={match.normalized_model_name}, "
            f"match_type={match.match_type}, matched_alias={match.matched_alias}"
            if match
            else "no_match"
        )
        print(
            f"[{status}] raw_model_name={raw_model_name}, expected={expected}, "
            f"actual={actual}, {details}"
        )
        if actual != expected:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
