import json
import os
import sys
import tempfile
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import generate_html


def snapshot(timestamp, quantity, coverage_complete):
    return {
        "time": timestamp,
        "lowest": 1.8,
        "weighted_avg": 2.0,
        "main_low": 1.9,
        "main_high": 2.1,
        "n_listings": 1,
        "total_qty": quantity,
        "total_amount": quantity * 2.0,
        "source_pages": 1,
        "source_reported_total": 1,
        "coverage_complete": coverage_complete,
        "items": [
            {
                "price_per_wan": 2.0,
                "qty_min": quantity,
                "qty_max": quantity,
            }
        ],
    }


class GenerateHtmlTest(unittest.TestCase):
    def test_renders_inventory_trend_and_data_quality_markers(self):
        history = [
            snapshot("2026-08-05 10:00:00", 20, False),
            snapshot("2026-08-06 10:00:00", 60000, True),
        ]
        with tempfile.TemporaryDirectory() as directory:
            data_path = os.path.join(directory, "history.json")
            output_path = os.path.join(directory, "index.html")
            with open(data_path, "w", encoding="utf-8") as handle:
                json.dump({"history": history}, handle)

            generate_html.render(data_path, output_path)

            with open(output_path, encoding="utf-8") as handle:
                page = handle.read()
            self.assertIn('id="volumeTrend"', page)
            self.assertIn("港口货量潮汐", page)
            self.assertIn("灰色虚线为早期 1 个非全量样本", page)
            self.assertIn('"max_order_qty": 60000', page)
            self.assertIn('"coverage_complete": false', page)
            self.assertIn('"coverage_complete": true', page)
            self.assertIn('"is_large_order": true', page)


if __name__ == "__main__":
    unittest.main()
