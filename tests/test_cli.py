from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from airco_tracker.cli import check
from airco_tracker.models import Product


class _SuccessAdapter:
    site = "Working shop"

    def __init__(self, _fetcher) -> None:
        pass

    def fetch_products(self):
        return [Product(self.site, "Airco", "https://shop.test/1", False)]


class _FailingAdapter:
    site = "Blocked shop"

    def __init__(self, _fetcher) -> None:
        pass

    def fetch_products(self):
        raise RuntimeError("403 Forbidden")


class _StateStore:
    def load(self):
        return {"version": 1, "products": {}}


class CliTests(unittest.TestCase):
    def test_partial_retailer_failure_is_successful(self) -> None:
        config = SimpleNamespace(
            request_timeout_seconds=1,
            alert_on_first_seen=True,
            max_price_eur=None,
            min_btu=None,
        )
        with (
            patch("airco_tracker.cli.CoolblueAdapter", _SuccessAdapter),
            patch("airco_tracker.cli.MediaMarktAdapter", _FailingAdapter),
            patch("airco_tracker.cli.BolAdapter", _FailingAdapter),
            patch("airco_tracker.cli.build_state_store", return_value=_StateStore()),
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(check(config, dry_run=True, show_all=False), 0)

    def test_all_retailer_failures_are_fatal(self) -> None:
        config = SimpleNamespace(request_timeout_seconds=1)
        with (
            patch("airco_tracker.cli.CoolblueAdapter", _FailingAdapter),
            patch("airco_tracker.cli.MediaMarktAdapter", _FailingAdapter),
            patch("airco_tracker.cli.BolAdapter", _FailingAdapter),
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(check(config, dry_run=True, show_all=False), 2)


if __name__ == "__main__":
    unittest.main()
