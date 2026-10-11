#!/usr/bin/env python3
"""Export Google Melbourne organic rankings for one domain via DataForSEO Labs."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

import requests

API_URL = "https://api.dataforseo.com/v3/dataforseo_labs/google/ranked_keywords/live"
LOCATION_NAME = os.getenv("LOCATION_NAME", "Melbourne,Victoria,Australia").strip()
LANGUAGE_CODE = "en"
PAGE_SIZE = 1000
MAX_POSITION = 100
TARGET_DOMAIN = os.getenv("TARGET_DOMAIN", "melbournelandscape.com.au").strip().lower()
OUTPUT_DIR = Path("results")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def unwrap(task: dict[str, Any]) -> list[dict[str, Any]]:
    if task.get("status_code") != 20000:
        raise RuntimeError(
            f"DataForSEO task failed ({task.get('status_code')}): {task.get('status_message')}"
        )
    result = task.get("result") or []
    if not result:
        return []
    return result[0].get("items") or []


def get_value(data: dict[str, Any], *path: str) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def fetch_rankings(login: str, password: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0

    while True:
        payload = [{
            "target": TARGET_DOMAIN,
            "location_name": LOCATION_NAME,
            "language_code": LANGUAGE_CODE,
            "limit": PAGE_SIZE,
            "offset": offset,
            "include_serp_info": False,
            "filters": [[
                "ranked_serp_element.serp_item.rank_group",
                "<=",
                MAX_POSITION,
            ]],
        }]

        response = requests.post(
            API_URL,
            auth=(login, password),
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        body = response.json()
        tasks = body.get("tasks") or []
        if len(tasks) != 1:
            raise RuntimeError(f"Unexpected DataForSEO response: {body}")
        items = unwrap(tasks[0])

        for item in items:
            keyword_data = item.get("keyword_data") or {}
            keyword_info = keyword_data.get("keyword_info") or {}
            serp_item = get_value(item, "ranked_serp_element", "serp_item") or {}
            keyword = keyword_data.get("keyword")
            position = serp_item.get("rank_group")
            volume = keyword_info.get("search_volume")

            if keyword and position is not None:
                rows.append({
                    "keyword": keyword,
                    "ranking_position": position,
                    "monthly_search_volume": volume if volume is not None else "",
                })

        if len(items) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

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
    rows = fetch_rankings(login, password)
    created = write_csv(rows)
    print(f"Saved {len(rows)} Melbourne rankings to {created}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
