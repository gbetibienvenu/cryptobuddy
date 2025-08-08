"""
CryptoBuddy — rule-based cryptocurrency advisor chatbot (console version)
Run: python crypto_buddy.py
"""

from typing import Dict
import sys

# --- Predefined dataset (crypto_db.py could hold this if you want modularity) ---
crypto_db: Dict[str, Dict] = {
    "Bitcoin": {
        "symbol": "BTC",
        "price_trend": "rising",
        "market_cap": "high",
        "energy_use": "high",
        "sustainability_score": 3.0
    },
    "Ethereum": {
        "symbol": "ETH",
        "price_trend": "stable",
        "market_cap": "high",
        "energy_use": "medium",
        "sustainability_score": 6.0
    },
    "Cardano": {
        "symbol": "ADA",
        "price_trend": "rising",
        "market_cap": "medium",
        "energy_use": "low",
        "sustainability_score": 8.0
    },
    "Polkadot": {
        "symbol": "DOT",
        "price_trend": "falling",
        "market_cap": "medium",
        "energy_use": "low",
        "sustainability_score": 7.0
    }
}

# --- Helper / Rules ---
def top_by_sustainability(db):
    return max(db.keys(), key=lambda x: db[x]["sustainability_score"])

def trending_coins(db):
    return [k for k, v in db.items() if v["price_trend"] == "rising"]

def profitable_coins(db):
    # Profitability rule:
    # prioritize coins with price_trend == 'rising' and market_cap == 'high'
    return [k for k, v in db.items() if v["price_trend"] == "rising" and v["market_cap"] == "high"]

def sustainable_candidates(db):
    # Sustainability rule:
    # energy_use == 'low' and sustainability_score > 7
    return [k for k, v in db.items() if v["energy_use"] == "low" and v["sustainability_score"] > 7.0]

def summarize_coin(name, db):
    v = db.get(name)
    if not v:
        return "I don't have data for that coin."
    return (f"{name} ({v['symbol']}): trend={v['price_trend']}, market_cap={v['market_cap']}, "
            f"energy_use={v['energy_use']}, sustainability={v['sustainability_score']}/10")

# --- Simple intent matching (rule-based) ---
def handle_query(user_query: str, db: Dict[str, Dict]) -> str:
    q = user_query.lower().strip()

    # greetings
    if any(w in q for w in ["hi", "hello", "hey", "good morning", "good afternoon"]):
        return "Hey! I'm CryptoBuddy — your friendly AI-powered financial sidekick. How can I help? 😊"

    # ask for trending
    if "trending" in q or "trending up" in q or "trends" in q:
        trending = trending_coins(db)
        if trending:
            return f"Coins trending up: {', '.join(trending)}. Want a recommendation for profitability or sustainability?"
        return "No coins are trending up in my dataset right now."

    # ask for most sustainable
    if "sustainab" in q or "eco" in q or "green" in q or "energy" in q:
        cand = sustainable_candidates(db)
        if cand:
            return (f"Top sustainable picks: {', '.join(cand)}. "
                    f"Most sustainable overall: {top_by_sustainability(db)} 🌱")
        return f"The most sustainable coin in my dataset is {top_by_sustainability(db)} 🌱."

    # ask for profitability / best for long-term growth
    if "long-term" in q or "long term" in q or "best for growth" in q or "profit" in q or "buy" in q:
        prof = profitable_coins(db)
        if prof:
            # recommend highest sustainability among profitable results if tie
            best = max(prof, key=lambda x: db[x]["sustainability_score"])
            return (f"For long-term growth, I'd suggest {best} — it's trending up with strong market cap. "
                    f"Here's a quick summary:\n{summarize_coin(best, db)}\n"
                    f"Note: always do your own research — crypto is risky.")
        # fallback: suggest rising coins
        rising = trending_coins(db)
        if rising:
            best = max(rising, key=lambda x: db[x]["sustainability_score"])
            return (f"No 'high market cap + rising' coins found, but {best} is trending up. "
                    f"{summarize_coin(best, db)}\nPlease DYOR.")
        return "I can't find a strong long-term pick in my data. Consider more research."

    # ask about a particular coin
    for coin in db.keys():
        if coin.lower() in q or db[coin]["symbol"].lower() in q:
            return summarize_coin(coin, db)

    # help / instructions
    if "help" in q or "what can you do" in q:
        return ("I can tell you which coins are trending, which are most sustainable, or recommend "
                "coins for profitability vs sustainability. Try: 'Which crypto is trending up?' or "
                "'What's the most sustainable coin?'")

    # fallback
    return ("Sorry, I didn't quite get that. Try asking: 'Which crypto is trending up?', "
            "'Which is most sustainable?', or 'Which should I buy for long-term growth?'")

# --- Main loop ---
def main():
    print("=== CryptoBuddy (console) ===")
    print("Type 'exit' to quit. Type 'help' to see example questions.")
    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye — CryptoBuddy signing off.")
            sys.exit(0)

        if user.lower() in ["exit", "quit"]:
            print("CryptoBuddy: Goodbye! Stay safe and always DYOR. 🚀")
            break

        response = handle_query(user, crypto_db)
        print("\nCryptoBuddy:", response)

if __name__ == "__main__":
    main()
