import streamlit as st
from crypto_db import handle_query, crypto_db


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

# --- Streamlit UI ---
st.set_page_config(page_title="CryptoBuddy", page_icon="💰")
st.title("💰 CryptoBuddy — The AI-Powered Financial Sidekick! 🌟")

# Keep track of chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input form
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask me about crypto:", key="user_input")
    submitted = st.form_submit_button("Ask")

    if submitted and user_input:
        answer = handle_query(user_input, crypto_db)
        st.session_state.messages.append(("You", user_input))
        st.session_state.messages.append(("CryptoBuddy", answer))

# Display chat history
for sender, message in st.session_state.messages:
    if sender == "You":
        st.markdown(f"**🧑 {sender}:** {message}")
    else:
        st.markdown(f"**🤖 {sender}:** {message}")
