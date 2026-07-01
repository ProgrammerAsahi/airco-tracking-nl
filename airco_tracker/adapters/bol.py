from __future__ import annotations

from typing import Any

from .base import parse_btu
from ..fetch import Fetcher
from ..models import Product


class BolAdapter:
    """bol.com adapter backed by the official Marketing Catalog API."""

    site = "bol.com"
    token_url = "https://login.bol.com/token"
    search_url = "https://api.bol.com/marketing/catalog/v1/products/search"
    _excluded = (
        "aircooler",
        "ventilator",
        "raamafdichting",
        "raamkit",
        "afvoerslang",
        "beschermhoes",
        "add-on battery",
        "onderdeel",
    )

    def __init__(
        self,
        fetcher: Fetcher,
        client_id: str,
        client_secret: str,
        *,
        search_term: str = "mobiele airco",
        max_pages: int = 5,
    ) -> None:
        self.fetcher = fetcher
        self.client_id = client_id
        self.client_secret = client_secret
        self.search_term = search_term
        self.max_pages = max(1, max_pages)

    def fetch_products(self) -> list[Product]:
        token = self._access_token()
        products: dict[str, Product] = {}
        page = 1
        while page <= self.max_pages:
            response = self.fetcher.session.get(
                self.search_url,
                params={
                    "search-term": self.search_term,
                    "country-code": "NL",
                    "page": page,
                    "page-size": 50,
                    "include-offer": "true",
                },
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "nl-NL",
                    "Authorization": f"Bearer {token}",
                },
                timeout=self.fetcher.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results", [])
            if not isinstance(results, list):
                raise RuntimeError("bol.com API returned an invalid search response")
            for item in results:
                product = self._parse_product(item)
                if product is not None:
                    products[product.url] = product

            total_pages = _positive_int(payload.get("totalPages"), default=page)
            if not results or page >= total_pages:
                break
            page += 1
        return list(products.values())

    def _access_token(self) -> str:
        response = self.fetcher.session.post(
            self.token_url,
            params={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            headers={"Accept": "application/json", "Content-Length": "0"},
            timeout=self.fetcher.timeout,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("bol.com authentication response did not contain an access token")
        return token

    def _parse_product(self, item: Any) -> Product | None:
        if not isinstance(item, dict):
            return None
        name = str(item.get("title", "")).strip()
        description = str(item.get("description", "")).strip()
        text = f"{name} {description}".strip()
        btu = parse_btu(text)
        if not self._is_real_airco(name, text, btu):
            return None

        url = str(item.get("url", "")).strip()
        if not url:
            product_id = str(item.get("bolProductId", "")).strip()
            if not product_id:
                return None
            url = f"https://www.bol.com/nl/nl/p/{product_id}/"

        offer = item.get("offer")
        available = isinstance(offer, dict)
        price = _optional_float(offer.get("price")) if available else None
        delivery = str(offer.get("deliveryDescription", "")).strip() if available else None
        return Product(
            site=self.site,
            name=name or "Onbekende mobiele airco",
            url=url,
            available=available,
            price_eur=price,
            delivery=delivery or None,
            btu=btu,
        )

    def _is_real_airco(self, name: str, text: str, btu: int | None) -> bool:
        lower_name = name.lower()
        if any(term in lower_name for term in self._excluded):
            return False
        named_as_airco = any(
            term in lower_name
            for term in ("mobiele airco", "mobiele airconditioner", "portable airco", "air conditioner")
        )
        has_exhaust = "afvoerslang" in text.lower()
        return named_as_airco and (has_exhaust or (btu is not None and btu >= 2000))


def _positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
