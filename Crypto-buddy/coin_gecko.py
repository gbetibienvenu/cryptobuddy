# coin_gecko.py
"""
Simple CoinGecko helper utilities for CryptoBuddy.

Provides:
- symbol_to_id(symbol)
- get_simple_price(symbol_or_symbols, vs_currency='usd')
- get_market_data(symbol, vs_currency='usd')
- get_coin_info(symbol)
- bulk_prices(symbols_list, vs_currency='usd')

Uses a tiny in-memory cache with TTL and basic retry/backoff on failures.
"""

from typing import Optional, Union, List, Dict, Any
import requests
import time

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# A lightweight symbol -> CoinGecko id map for common coins.
# Add more as you need (CoinGecko IDs are lowercase and often not the same as symbol).
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "ADA": "cardano",
    "DOT": "polkadot",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "SOL": "solana",
    "LTC": "litecoin",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "ATOM": "cosmos",
    "TRX": "tron"
}

# Simple in-memory cache: key -> (timestamp, data)
_CACHE: Dict[str, Any] = {}
DEFAULT_TTL = 30  # seconds


def _now() -> float:
    return time.time()


def _cache_get(key: str, ttl: int = DEFAULT_TTL):
    rec = _CACHE.get(key)
    if not rec:
        return None
    ts, data = rec
    if _now() - ts > ttl:
        # expired
        _CACHE.pop(key, None)
        return None
    return data


def _cache_set(key: str, value: Any):
    _CACHE[key] = (_now(), value)


def _request(path: str, params: Optional[Dict] = None, retries: int = 2, backoff: float = 0.8) -> Optional[Dict]:
    url = f"{COINGECKO_BASE}{path}"
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt == retries:
                return {"error": str(e)}
            time.sleep(backoff * (attempt + 1))
    return None


def symbol_to_id(symbol_or_id: str) -> Optional[str]:
    """
    Convert a symbol (e.g. 'BTC', 'eth') to a CoinGecko id (e.g. 'bitcoin').
    If input already looks like an id present in SYMBOL_TO_ID values, it returns it.
    """
    if not symbol_or_id:
        return None
    s = symbol_or_id.strip().upper()
    # direct mapping by symbol
    if s in SYMBOL_TO_ID:
        return SYMBOL_TO_ID[s]
    # maybe user passed a lowercase id already
    candidate = symbol_or_id.strip().lower()
    if candidate in SYMBOL_TO_ID.values():
        return candidate
    # no mapping found
    return None


def get_simple_price(symbols: Union[str, List[str]], vs_currency: str = "usd", ttl: int = DEFAULT_TTL) -> Dict[str, Optional[float]]:
    """
    Get simple current prices for one or multiple symbols.
    - symbols: "BTC" or ["BTC","ETH"] or "bitcoin,ethereum"
    Returns a dict mapping original symbol -> price (float) or None/error info.
    Example:
        get_simple_price("BTC") -> {"BTC": 41234.12}
        get_simple_price(["BTC","ETH"]) -> {"BTC": 41234.12, "ETH": 3100.5}
    """
    if isinstance(symbols, str):
        symbols_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        symbols_list = symbols

    ids = []
    mapping = {}  # symbol -> id
    for sym in symbols_list:
        coin_id = symbol_to_id(sym)
        mapping[sym.upper()] = coin_id
        if coin_id:
            ids.append(coin_id)

    cache_key = f"simple_price:{','.join(sorted(ids))}:{vs_currency}"
    cached = _cache_get(cache_key, ttl=ttl)
    if cached is not None:
        # map back to requested symbols
        return {sym: (cached.get(mapping[sym.upper()], {}).get(vs_currency) if mapping[sym.upper()] else None) for sym in mapping}

    if not ids:
        return {sym: None for sym in mapping}

    params = {"ids": ",".join(ids), "vs_currencies": vs_currency}
    data = _request("/simple/price", params=params)
    if not data or "error" in data:
        return {sym: None for sym in mapping}

    _cache_set(cache_key, data)
    result = {}
    for sym, cid in mapping.items():
        if cid and data.get(cid) and vs_currency in data[cid]:
            result[sym] = data[cid][vs_currency]
        else:
            result[sym] = None
    return result


def bulk_prices(symbols: List[str], vs_currency: str = "usd", ttl: int = DEFAULT_TTL) -> Dict[str, Optional[float]]:
    """
    Convenience wrapper for get_simple_price with list input.
    """
    return get_simple_price(symbols, vs_currency=vs_currency, ttl=ttl)


def get_market_data(symbol: str, vs_currency: str = "usd", ttl: int = DEFAULT_TTL) -> Dict[str, Any]:
    """
    Fetch richer market data for a single coin using /coins/markets endpoint.
    Returns a dict like {'current_price': ..., 'market_cap': ..., 'price_change_percentage_24h': ...}
    If symbol not recognized, returns {'error': 'unknown symbol'}.
    """
    coin_id = symbol_to_id(symbol)
    if not coin_id:
        return {"error": "unknown symbol or id mapping not available"}

    cache_key = f"market_data:{coin_id}:{vs_currency}"
    cached = _cache_get(cache_key, ttl=ttl)
    if cached:
        return cached

    params = {"vs_currency": vs_currency, "ids": coin_id, "order": "market_cap_desc", "per_page": 1, "page": 1, "sparkline": False}
    data = _request("/coins/markets", params=params)
    if not data or "error" in data:
        return {"error": data.get("error") if isinstance(data, dict) else "request failed"}

    if isinstance(data, list) and data:
        record = data[0]
        out = {
            "id": record.get("id"),
            "symbol": record.get("symbol"),
            "name": record.get("name"),
            "current_price": record.get("current_price"),
            "market_cap": record.get("market_cap"),
            "price_change_percentage_24h": record.get("price_change_percentage_24h"),
            "total_volume": record.get("total_volume")
        }
        _cache_set(cache_key, out)
        return out

    return {"error": "no data returned"}


def get_coin_info(symbol: str, ttl: int = DEFAULT_TTL) -> Dict[str, Any]:
    """
    Get descriptive info about a coin via /coins/{id}.
    Returns basic fields (id, name, description (en), homepage list).
    """
    coin_id = symbol_to_id(symbol)
    if not coin_id:
        return {"error": "unknown symbol"}

    cache_key = f"coin_info:{coin_id}"
    cached = _cache_get(cache_key, ttl=ttl)
    if cached:
        return cached

    data = _request(f"/coins/{coin_id}", params={"localization": "false", "tickers": "false", "market_data": "false", "community_data": "false", "developer_data": "false", "sparkline": "false"})
    if not data or "error" in data:
        return {"error": data.get("error") if isinstance(data, dict) else "request failed"}

    out = {
        "id": data.get("id"),
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "description": (data.get("description") or {}).get("en", "")[:800],  # trim description
        "homepage": (data.get("links") or {}).get("homepage", [])[:3]
    }
    _cache_set(cache_key, out)
    return out


def search_coin(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Use the CoinGecko /search endpoint to find matching coins.
    Returns the raw CoinGecko search response (limited).
    """
    if not query:
        return {"error": "empty query"}
    cache_key = f"search:{query.lower()}:{limit}"
    cached = _cache_get(cache_key, ttl=DEFAULT_TTL)
    if cached:
        return cached

    data = _request("/search", params={"query": query})
    if not data or "error" in data:
        return {"error": data.get("error") if isinstance(data, dict) else "request failed"}

    # Restrict to first `limit` coin matches
    coins = data.get("coins", [])[:limit]
    result = {"coins": coins}
    _cache_set(cache_key, result)
    return result


# -----------------
# Example usage (for interactive testing)
# -----------------
if __name__ == "__main__":
    print("Testing coin_gecko helper...")
    print("BTC price:", get_simple_price("BTC"))
    print("BTC market data:", get_market_data("BTC"))
    print("ETH coin info snippet:", get_coin_info("ETH")["description"][:200] if get_coin_info("ETH").get("description") else "no desc")
