from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from playwright.sync_api import sync_playwright


DEFAULT_URL = "https://min-repo.com/3350338/"
TIMEOUT_MS = 30_000


def _compact(value: str, limit: int = 500) -> str:
    return " ".join(value[:limit].split())


def _fetch_json(url: str) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Slot-Data-Analysis-network-diagnostic/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        print(f"[diagnostic] helper_request_error url={url} error={exc!r}")
        return None


def _plain_http_diagnostic(target_url: str) -> None:
    print("\n=== plain HTTP diagnostic ===")
    req = urllib.request.Request(
        target_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
            )
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read()
            text = body.decode("utf-8", errors="replace")
            print(f"requested_url={target_url}")
            print(f"final_url={response.geturl()}")
            print(f"status={response.status}")
            print(f"content_type={response.headers.get('content-type')}")
            print(f"server={response.headers.get('server')}")
            print(f"content_length_header={response.headers.get('content-length')}")
            print(f"body_bytes={len(body)}")
            print(f"body_preview={_compact(text)}")
            print("response_headers=")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
    except urllib.error.HTTPError as exc:
        body = exc.read()
        text = body.decode("utf-8", errors="replace")
        print(f"requested_url={target_url}")
        print(f"final_url={exc.geturl()}")
        print(f"status={exc.code}")
        print(f"body_bytes={len(body)}")
        print(f"body_preview={_compact(text)}")
        print(f"http_error={exc!r}")
    except Exception as exc:
        print(f"requested_url={target_url}")
        print(f"request_error={exc!r}")


def _playwright_diagnostic(target_url: str) -> None:
    print("\n=== Playwright diagnostic ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        user_agent = page.evaluate("navigator.userAgent")
        print(f"user_agent={user_agent}")

        response = None
        try:
            response = page.goto(target_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
            print(f"requested_url={target_url}")
            print(f"final_url={page.url}")
            print(f"status={response.status if response else None}")

            if response:
                headers = response.headers
                print(f"content_type={headers.get('content-type')}")
                print(f"server={headers.get('server')}")
                print(f"content_length_header={headers.get('content-length')}")
                try:
                    response_body = response.body()
                    print(f"response_body_bytes={len(response_body)}")
                    print(
                        "response_body_preview="
                        f"{_compact(response_body.decode('utf-8', errors='replace'))}"
                    )
                except Exception as exc:
                    print(f"response_body_error={exc!r}")

                print("response_headers=")
                for key, value in sorted(headers.items()):
                    print(f"  {key}: {value}")

            html = page.content()
            print(f"page_title={page.title()!r}")
            print(f"page_content_chars={len(html)}")
            print(f"page_content_preview={_compact(html)}")
            print(f"table_kishu_count={page.locator('table.kishu').count()}")
            print(f"h1_count={page.locator('h1').count()}")
        except Exception as exc:
            print(f"playwright_error={exc!r}")
            try:
                html = page.content()
                print(f"final_url={page.url}")
                print(f"page_content_chars={len(html)}")
                print(f"page_content_preview={_compact(html)}")
            except Exception as content_exc:
                print(f"page_content_error={content_exc!r}")
        finally:
            browser.close()


def main() -> int:
    target_url = os.getenv("DIAGNOSTIC_URL", DEFAULT_URL).strip() or DEFAULT_URL

    print("=== runner diagnostic ===")
    for name in (
        "GITHUB_RUN_ID",
        "GITHUB_RUN_NUMBER",
        "GITHUB_SHA",
        "GITHUB_REF_NAME",
        "RUNNER_NAME",
        "RUNNER_OS",
        "RUNNER_ARCH",
        "RUNNER_ENVIRONMENT",
    ):
        print(f"{name}={os.getenv(name, '')}")

    ip_data = _fetch_json("https://api.ipify.org?format=json")
    print(f"egress_ip={ip_data.get('ip') if ip_data else None}")

    _plain_http_diagnostic(target_url)
    _playwright_diagnostic(target_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
