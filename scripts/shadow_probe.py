#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""12 小时影子测试探针：真实抓取数据源，但绝不修改正式数据文件。"""
import argparse
import json
import os
import tempfile
import time
import traceback
from datetime import datetime, timezone, timedelta

import fetch_gold


CST = timezone(timedelta(hours=8))


def iso_now(tz=timezone.utc):
    return datetime.now(tz).isoformat(timespec="seconds")


def write_atomic(path, payload):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="shadow-probe-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    started_monotonic = time.monotonic()
    payload = {
        "schema": "gold-price-shadow-probe/v1",
        "success": False,
        "started_at_utc": iso_now(),
        "started_at_cst": iso_now(CST),
        "source": {
            "site": "DD373",
            "url": fetch_gold.URL,
            "target": "冒险岛怀旧服 / 国服 / 漂漂猪 / 游戏币",
        },
        "github": {
            "run_id": os.environ.get("GITHUB_RUN_ID"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "sha": os.environ.get("GITHUB_SHA"),
        },
    }

    try:
        items, server_time, pages, reported_total = fetch_gold.fetch_all_items()
        statistics = fetch_gold.stats(items)
        coverage_complete = reported_total is None or len(items) >= reported_total
        validations = {
            "non_empty": len(items) > 0,
            "all_pages_covered": coverage_complete,
            "reported_matches_parsed": reported_total is None or len(items) == reported_total,
            "quantities_non_negative": all(
                item["qty_min"] >= 0 and item["qty_max"] >= item["qty_min"]
                for item in items
            ),
        }
        payload.update({
            "success": all(validations.values()),
            "server_time_cst": server_time.isoformat(timespec="seconds"),
            "source_pages": pages,
            "source_reported_total": reported_total,
            "parsed_total": len(items),
            "coverage_complete": coverage_complete,
            "validations": validations,
            "statistics": statistics,
            "items": items,
        })
        if not payload["success"]:
            payload["error"] = {
                "type": "ValidationError",
                "message": "真实抓取完成，但完整性校验未全部通过",
            }
    except Exception as exc:
        payload["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback_tail": traceback.format_exc().splitlines()[-8:],
        }
    finally:
        payload["finished_at_utc"] = iso_now()
        payload["finished_at_cst"] = iso_now(CST)
        payload["duration_seconds"] = round(time.monotonic() - started_monotonic, 3)
        write_atomic(args.out, payload)

    print(json.dumps({
        "success": payload["success"],
        "duration_seconds": payload["duration_seconds"],
        "parsed_total": payload.get("parsed_total"),
        "reported_total": payload.get("source_reported_total"),
        "pages": payload.get("source_pages"),
        "error": payload.get("error"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
