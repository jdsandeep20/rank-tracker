#!/usr/bin/env python3
"""Export actual Google Melbourne organic rankings for one domain via DataForSEO."""

from __future__ import annotations

import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

LABS_URL = "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live"
SERP_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
AUSTRALIA_LOCATION_CODE = 2036
MELBOURNE_LOCATION_NAME = "Melbourne,Victoria,Australia"
LANGUAGE_CODE = "en"
DISCOVERY_PAGE_SIZE = 1000
MAX_POSITION = 100
WORKERS = 8
MAX_SERP_RETRIES = 5
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "melbournelandscape.com.au").strip().lower()
OUTPUT_DIR = Path("results")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def task_result(task: dict[str, Any]) -> list[dict[str, Any]]:
    if task.get("status_code") != 20000:
        raise RuntimeError(
            f"DataForSEO task failed ({task.get('status_code')}): {task.get('status_message')}"
        )
    return task.get("result") or []


def request_json(
    session: requests.Session, url: str, login: str, password: str, payload: list[dict[str, Any]]
) -> dict[str, Any]:
    for attempt in range(3):
        response = session.post(url, auth=(login, password), json=payload, timeout=90)
        if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("DataForSEO request failed after retries")


def discover_keywords(
    session: requests.Session, login: str, password: str
) -> dict[str, int | str]:
    """Find the site's existing Australian ranking keywords and their AU volumes."""
    keywords: dict[str, int | str] = {}
    offset = 0

    while True:
        payload = [{
            "target": TARGET_DOMAIN,
            "location_code": AUSTRALIA_LOCATION_CODE,
            "language_code": LANGUAGE_CODE,
            "limit": DISCOVERY_PAGE_SIZE,
            "offset": offset,
            "include_serp_info": False,
            "filters": [[
                "ranked_serp_element.serp_item.rank_group",
                "<=",
                MAX_POSITION,
            ]],
        }]
        body = request_json(session, LABS_URL, login, password, payload)
        tasks = body.get("tasks") or []
        if len(tasks) != 1:
            raise RuntimeError(f"Unexpected DataForSEO Labs response: {body}")
        result = task_result(tasks[0])
        items = result[0].get("items") if result else []

        for item in items or []:
            keyword_data = item.get("keyword_data") or {}
            keyword_info = keyword_data.get("keyword_info") or {}
            keyword = keyword_data.get("keyword")
            if keyword:
                keywords[keyword] = keyword_info.get("search_volume") or ""

        if len(items or []) < DISCOVERY_PAGE_SIZE:
            break
        offset += DISCOVERY_PAGE_SIZE

    return keywords


def is_target_domain(domain: str | None) -> bool:
    if not domain:
        return False
    domain = domain.lower().rstrip(".")
    return domain == TARGET_DOMAIN or domain.endswith(f".{TARGET_DOMAIN}")


def check_melbourne_keyword(
    keyword: str, volume: int | str, login: str, password: str
) -> dict[str, Any] | None:
    """Run a live Google query from Melbourne and return the site's organic position."""
    payload = [{
        "keyword": keyword,
        "location_name": MELBOURNE_LOCATION_NAME,
        "language_code": LANGUAGE_CODE,
        "device": "desktop",
        "os": "windows",
        "depth": MAX_POSITION,
    }]
    last_error: RuntimeError | None = None

    for attempt in range(MAX_SERP_RETRIES):
        with requests.Session() as session:
            body = request_json(session, SERP_URL, login, password, payload)
        tasks = body.get("tasks") or []
        if len(tasks) != 1:
            raise RuntimeError(f"Unexpected DataForSEO SERP response for {keyword!r}")

        task = tasks[0]
        if task.get("status_code") == 40101:
            last_error = RuntimeError(
                f"DataForSEO temporary server error after {attempt + 1} attempt(s)"
            )
            if attempt < MAX_SERP_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            raise last_error

        result = task_result(task)
        items = result[0].get("items") if result else []
        for item in items or []:
            if item.get("type") == "organic" and is_target_domain(item.get("domain")):
                return {
                    "keyword": keyword,
                    "ranking_position": item.get("rank_absolute"),
                    "monthly_search_volume": volume,
                }
        return None

    raise last_error or RuntimeError("Unexpected SERP retry failure")


def fetch_melbourne_rankings(login: str, password: str) -> list[dict[str, Any]]:
    with requests.Session() as session:
        candidates = discover_keywords(session, login, password)

    print(f"Checking {len(candidates)} discovered keywords in Melbourne...")
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(check_melbourne_keyword, keyword, volume, login, password): keyword
            for keyword, volume in candidates.items()
        }
        for future in as_completed(futures):
            keyword = futures[future]
            try:
                row = future.result()
                if row:
                    rows.append(row)
            except Exception as error:
                failures.append(f"{keyword}: {error}")

    if failures:
        print(
            f"WARNING: skipped {len(failures)} temporary/failed keyword check(s). "
            f"First: {failures[0]}",
            file=sys.stderr,
        )
    if candidates and len(failures) == len(candidates):
        raise RuntimeError("Every Melbourne keyword check failed; no CSV was saved.")

    return sorted(rows, key=lambda row: (int(row["ranking_position"]), row["keyword"].lower()))


def write_csv(rows: list[dict[str, Any]]) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / "melbourne_rankings.csv"
    columns = ["keyword", "ranking_position", "monthly_search_volume"]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    return path


def main() -> None:
    login = require_env("DFS_LOGIN")
    password = require_env("DFS_PASSWORD")
    rows = fetch_melbourne_rankings(login, password)
    created = write_csv(rows)
    print(f"Saved {len(rows)} Melbourne rankings to {created}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
