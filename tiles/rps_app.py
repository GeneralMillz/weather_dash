# tiles/rps_app.py
import random
import time

CHOICES = ["Rock", "Paper", "Scissors"]

def cpu_play():
    return random.choice(CHOICES)

def decide(p, c):
    if p == c:
        return "Tie"
    wins = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
    return "Win" if wins[p] == c else "Lose"

def render(services, st, state):
    """
    Tile entrypoint used by app.py: render(services, st, state)
    - services: dict of shared services (unused here, kept for compatibility)
    - st: Streamlit module passed from the host app
    - state: dict-like container for cross-tile state (use if available)
    """
    st.title("Rock Paper Scissors")
    st.write("Play against the CPU. Session score is kept for this browser session.")

    # Use a tile-scoped key to avoid clashing with other tiles
    key = "rps_tile"

    if key not in st.session_state:
        st.session_state[key] = {"name": "Guest", "wins":0,"losses":0,"ties":0,"games":0, "last": None, "history": []}

    s = st.session_state[key]

    name = st.text_input("Nickname", s["name"], max_chars=20, key=f"{key}_name")
    s["name"] = name.strip() or "Guest"

    cols = st.columns(3)
    if cols[0].button("🪨 Rock", key=f"{key}_rock"):
        _play_round(s, "Rock")
    if cols[1].button("📄 Paper", key=f"{key}_paper"):
        _play_round(s, "Paper")
    if cols[2].button("✂️ Scissors", key=f"{key}_scissors"):
        _play_round(s, "Scissors")

    last = s["last"]
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
    st.write(f"**{s['name']}** — Games: **{s['games']}**, Wins: **{s['wins']}**, Losses: **{s['losses']}**, Ties: **{s['ties']}**")

    # small history preview
    st.markdown("---")
    st.subheader("Recent rounds (this session)")
    if not s["history"]:
        st.write("No rounds played yet.")
    else:
        for h in s["history"][:10]:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h["time"]))
            st.write(f"{ts} — {h['player']} — {h['result']}")

def _play_round(s, player_choice):
    cpu_choice = cpu_play()
    result = decide(player_choice, cpu_choice)
    s["games"] += 1
    if result == "Win":
        s["wins"] += 1
    elif result == "Lose":
        s["losses"] += 1
    else:
        s["ties"] += 1
    s["last"] = {"player": player_choice, "cpu": cpu_choice, "result": result}
    s["history"].insert(0, {"player": s["name"], "result": result, "time": time.time()})
    s["history"] = s["history"][:50]
