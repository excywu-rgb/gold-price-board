import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import fetch_gold


def record(timestamp, price):
    return {"time": timestamp, "lowest": price}


class HistorySafetyTest(unittest.TestCase):
    def test_missing_file_starts_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "missing.json")
            self.assertEqual(fetch_gold.load(path), {"history": []})

    def test_corrupt_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "history.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{broken")
            with self.assertRaises(json.JSONDecodeError):
                fetch_gold.load(path)
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "{broken")

    def test_invalid_structure_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "history.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"history": {}}, handle)
            with self.assertRaises(ValueError):
                fetch_gold.load(path)

    def test_same_hour_replaces_without_losing_other_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "history.json")
            old = [
                record("2026-08-06 09:17:00", 2.0),
                record("2026-08-06 10:17:00", 2.1),
            ]
            count = fetch_gold.save_history_atomic(
                path, old, record("2026-08-06 10:47:00", 1.9)
            )
            self.assertEqual(count, 2)
            loaded = fetch_gold.load(path)["history"]
            self.assertEqual(loaded[0], old[0])
            self.assertEqual(loaded[1]["time"], "2026-08-06 10:47:00")

    def test_new_hour_appends_and_preserves_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "history.json")
            old = [record("2026-08-06 09:17:00", 2.0)]
            count = fetch_gold.save_history_atomic(
                path, old, record("2026-08-06 10:17:00", 1.9)
            )
            self.assertEqual(count, 2)
            self.assertEqual(fetch_gold.load(path)["history"][0], old[0])


if __name__ == "__main__":
    unittest.main()
