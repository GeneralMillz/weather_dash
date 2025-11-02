# tiles/rps_app.py
import streamlit as st
import random

CHOICES = ["Rock", "Paper", "Scissors"]

def cpu_play():
    return random.choice(CHOICES)

def decide(p, c):
    if p == c:
        return "Tie"
    wins = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    return "Win" if wins[p] == c else "Lose"

def render():
    st.title("Rock Paper Scissors")
    st.write("Play against the CPU. Session score is kept for this browser session.")

    if "rps" not in st.session_state:
        st.session_state.rps = {"name": "Guest", "wins":0,"losses":0,"ties":0,"games":0, "last": None}

    name = st.text_input("Nickname", st.session_state.rps["name"], max_chars=20)
    st.session_state.rps["name"] = name.strip() or "Guest"

    cols = st.columns(3)
    if cols[0].button("🪨 Rock"):
        _play_round("Rock")
    if cols[1].button("📄 Paper"):
        _play_round("Paper")
    if cols[2].button("✂️ Scissors"):
        _play_round("Scissors")

    last = st.session_state.rps["last"]
    if last:
        st.markdown("---")
        st.write(f"**You:** {last['player']}  →  **CPU:** {last['cpu']}")
        if last["result"] == "Win":
            st.success("You win")
        elif last["result"] == "Lose":
            st.error("You lose")
        else:
            st.info("Tie")

    st.markdown("---")
    p = st.session_state.rps
    st.write(f"**{p['name']}** — Games: **{p['games']}**, Wins: **{p['wins']}**, Losses: **{p['losses']}**, Ties: **{p['ties']}**")

def _play_round(player_choice):
    cpu_choice = cpu_play()
    result = decide(player_choice, cpu_choice)
    s = st.session_state.rps
    s["games"] += 1
    if result == "Win":
        s["wins"] += 1
    elif result == "Lose":
        s["losses"] += 1
    else:
        s["ties"] += 1
    s["last"] = {"player": player_choice, "cpu": cpu_choice, "result": result}
