from __future__ import annotations

import unittest

from bs4 import BeautifulSoup

from airco_tracker.adapters.bol import BolAdapter
from airco_tracker.adapters.coolblue import CoolblueAdapter
from airco_tracker.adapters.mediamarkt import MediaMarktAdapter
from airco_tracker.adapters.base import parse_btu, parse_price


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class DummySession:
    def __init__(self, search_payload):
        self.search_payload = search_payload
        self.token_calls = []
        self.search_calls = []

    def post(self, url, **kwargs):
        self.token_calls.append((url, kwargs))
        return DummyResponse({"access_token": "token"})

    def get(self, url, **kwargs):
        self.search_calls.append((url, kwargs))
        return DummyResponse(self.search_payload)


class DummyFetcher:
    def __init__(self, search_payload=None):
        self.timeout = 25
        self.session = DummySession(search_payload or {})


class ParserTests(unittest.TestCase):
    def test_dutch_price_and_btu_formats(self) -> None:
        self.assertEqual(parse_price("504 ,- Tijdelijk uitverkocht"), 504.0)
        self.assertEqual(parse_price("De prijs is '499' euro en '99' cent"), 499.99)
        self.assertEqual(parse_btu("14K BTU/h"), 14000)
        self.assertEqual(parse_btu("14.000 BTU/h"), 14000)

    def test_coolblue_out_of_stock_and_available(self) -> None:
        html = """
        <main>
          <article><a href="/product/1/test.html"><img alt="Test 9000 BTU"></a>
            <p>€ 399,00</p><p>Tijdelijk uitverkocht</p></article>
          <article><a href="/product/2/good.html">Good 12000 BTU</a>
            <p>€ 499,00</p><p>Morgen bezorgd</p></article>
        </main>"""
        products = CoolblueAdapter(DummyFetcher()).parse(BeautifulSoup(html, "html.parser"), "https://www.coolblue.nl/mobiele-aircos")
        self.assertEqual([p.available for p in products], [False, True])
        self.assertEqual(products[1].price_eur, 499.0)

    def test_mediamarkt_requires_online_stock(self) -> None:
        html = """
        <article><a href="/nl/product/_one-123.html">One 7000 BTU</a><span>€ 247,00</span>
        <span>Online op voorraad</span><button>Ik wil bestellen</button></article>
        <article><a href="/nl/product/_two-456.html">Two 9000 BTU</a><span>€ 350,00</span>
        <span>Helaas geen bezorging mogelijk</span></article>"""
        products = MediaMarktAdapter(DummyFetcher()).parse(BeautifulSoup(html, "html.parser"), "https://www.mediamarkt.nl/")
        self.assertEqual([p.available for p in products], [True, False])

    def test_bol_marketing_api_excludes_aircooler_and_reads_offer(self) -> None:
        fetcher = DummyFetcher({
            "totalPages": 1,
            "results": [
                {
                    "title": "Mini Aircooler Mobiele Airco",
                    "url": "https://www.bol.com/nl/nl/p/9300000000001/",
                    "offer": {"price": 49.95, "deliveryDescription": "Op voorraad"},
                },
                {
                    "title": "Echte Mobiele Airco 7000 BTU",
                    "description": "Werkt met afvoerslang naar buiten",
                    "url": "https://www.bol.com/nl/nl/p/9300000000002/",
                    "offer": {"price": 299.0, "deliveryDescription": "Morgen in huis"},
                },
                {
                    "title": "Tweede Mobiele Airco 9000 BTU",
                    "bolProductId": 9300000000003,
                },
            ],
        })
        products = BolAdapter(fetcher, "client", "secret").fetch_products()
        self.assertEqual(len(products), 2)
        self.assertTrue(products[0].available)
        self.assertEqual(products[0].btu, 7000)
        self.assertEqual(products[0].price_eur, 299.0)
        self.assertEqual(products[0].delivery, "Morgen in huis")
        self.assertFalse(products[1].available)
        self.assertEqual(products[1].url, "https://www.bol.com/nl/nl/p/9300000000003/")
        self.assertEqual(fetcher.session.token_calls[0][1]["auth"], ("client", "secret"))
        self.assertEqual(fetcher.session.search_calls[0][1]["params"]["country-code"], "NL")


if __name__ == "__main__":
    unittest.main()
