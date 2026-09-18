from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote, urljoin

from playwright.sync_api import Page, Response, sync_playwright

from config import config


DEFAULT_DIRECT_URL = "https://min-repo.com/3350338/"
DEFAULT_HALL = "ビックディッパー門前仲町店"
TIMEOUT_MS = 30_000
DATE_LINK_SELECTOR = "#content div table tbody tr td a"


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
                if key.lower() == "set-cookie":
                    continue
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


def _safe_response_body(response: Response | None) -> tuple[int | None, str]:
    if response is None:
        return None, ""
    try:
        body = response.body()
        return len(body), _compact(body.decode("utf-8", errors="replace"))
    except Exception as exc:
        return None, f"<response.body() failed: {exc!r}>"


def _print_page_state(label: str, page: Page, response: Response | None) -> None:
    print(f"\n=== {label} ===")
    print(f"final_url={page.url}")
    print(f"status={response.status if response else None}")

    if response:
        headers = response.headers
        print(f"content_type={headers.get('content-type')}")
        print(f"server={headers.get('server')}")
        print(f"content_length_header={headers.get('content-length')}")
        body_bytes, body_preview = _safe_response_body(response)
        print(f"response_body_bytes={body_bytes}")
        print(f"response_body_preview={body_preview}")

    try:
        html = page.content()
        print(f"page_title={page.title()!r}")
        print(f"page_content_chars={len(html)}")
        print(f"page_content_preview={_compact(html)}")
    except Exception as exc:
        print(f"page_content_error={exc!r}")

    print(f"date_link_count={page.locator(DATE_LINK_SELECTOR).count()}")
    print(f"table_kishu_count={page.locator('table.kishu').count()}")
    print(f"h1_count={page.locator('h1').count()}")

    try:
        cookies = page.context.cookies()
        print(f"cookie_count={len(cookies)}")
        cookie_meta = [
            {
                "name": cookie.get("name"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path"),
            }
            for cookie in cookies
        ]
        print(f"cookie_metadata={cookie_meta}")
    except Exception as exc:
        print(f"cookie_error={exc!r}")


def _playwright_direct_diagnostic(target_url: str) -> None:
    print("\n=== Playwright direct diagnostic ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        print(f"user_agent={page.evaluate('navigator.userAgent')}")
        try:
            response = page.goto(
                target_url,
                timeout=TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            _print_page_state("direct page result", page, response)
        except Exception as exc:
            print(f"playwright_error={exc!r}")
            _print_page_state("direct page result after error", page, None)
        finally:
            browser.close()


def _playwright_route_diagnostic(hall_name: str) -> None:
    hall_url = urljoin(config.MAIN_URL, quote(hall_name))
    print("\n=== Playwright route diagnostic ===")
    print(f"diagnostic_hall={hall_name}")
    print(f"hall_url={hall_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(TIMEOUT_MS)

        print(f"user_agent={page.evaluate('navigator.userAgent')}")

        ajax_events: list[str] = []

        def record_response(response: Response) -> None:
            if "admin-ajax.php" in response.url:
                ajax_events.append(f"{response.status} {response.url}")

        page.on("response", record_response)

        try:
            hall_response = page.goto(
                hall_url,
                timeout=TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            _print_page_state("hall page result", page, hall_response)

            try:
                page.wait_for_selector(DATE_LINK_SELECTOR, timeout=15_000)
            except Exception as exc:
                print(f"date_link_wait_error={exc!r}")

            links = page.locator(DATE_LINK_SELECTOR)
            link_count = links.count()
            print(f"date_link_count_after_wait={link_count}")

            if link_count == 0:
                print("route_result=no_date_link")
                print(f"admin_ajax_events={ajax_events}")
                return

            first_link = links.nth(0)
            date_text = first_link.inner_text().strip()
            href = first_link.get_attribute("href") or ""
            date_url = urljoin(page.url, href)

            print(f"selected_date_text={date_text!r}")
            print(f"selected_date_href={href}")
            print(f"selected_date_url={date_url}")

            date_response = page.goto(
                date_url,
                timeout=TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            _print_page_state("date page result via hall page", page, date_response)

            try:
                page.wait_for_selector("table.kishu", timeout=10_000)
                print("table_kishu_wait=found")
            except Exception as exc:
                print(f"table_kishu_wait=timeout error={exc!r}")

            print(f"table_kishu_count_after_wait={page.locator('table.kishu').count()}")
            print(f"route_result={'success' if page.locator('table.kishu').count() > 0 else 'no_table'}")
            print(f"admin_ajax_events={ajax_events}")
        except Exception as exc:
            print(f"route_diagnostic_error={exc!r}")
            _print_page_state("route page state after error", page, None)
            print(f"admin_ajax_events={ajax_events}")
        finally:
            browser.close()


def main() -> int:
    direct_url = os.getenv("DIAGNOSTIC_URL", DEFAULT_DIRECT_URL).strip() or DEFAULT_DIRECT_URL
    hall_name = os.getenv("DIAGNOSTIC_HALL", DEFAULT_HALL).strip() or DEFAULT_HALL

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

    _plain_http_diagnostic(direct_url)
    _playwright_direct_diagnostic(direct_url)
    _playwright_route_diagnostic(hall_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
