# crypto_db.py

# --- Simple crypto "database" ---
crypto_db = {
    "bitcoin": {"price": "$68,000", "trend": "up", "market_cap": "1.3T"},
    "ethereum": {"price": "$3,500", "trend": "down", "market_cap": "420B"},
    "dogecoin": {"price": "$0.15", "trend": "up", "market_cap": "20B"},
    "solana": {"price": "$150", "trend": "up", "market_cap": "65B"},
}

# --- AI-like query handler ---
def handle_query(query, db):
    query = query.lower()
    for coin, info in db.items():
        if coin in query:
            return (
                f"**{coin.title()}**\n"
                f"- Price: {info['price']}\n"
                f"- Trend: {info['trend']}\n"
                f"- Market Cap: {info['market_cap']}"
            )
    if "trending up" in query:
        trending_up = [coin.title() for coin, info in db.items() if info["trend"] == "up"]
        return "📈 Coins trending up: " + ", ".join(trending_up)
    if "trending down" in query:
        trending_down = [coin.title() for coin, info in db.items() if info["trend"] == "down"]
        return "📉 Coins trending down: " + ", ".join(trending_down)
    return "Sorry, I couldn't understand your query. Try asking about a specific coin or trend."
