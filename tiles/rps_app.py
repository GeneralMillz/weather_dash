# rps_app.py
import streamlit as st
import random
import time
import json
from pathlib import Path

# ---------- Config ----------
GAME_NAME = "Rock Paper Scissors"
LOCAL_LEADERBOARD_FILE = Path("/tmp/rps_leaderboard.json")  # change for persistent Pi path
REMOTE_SCORE_ENDPOINT = None  # set to "https://yourapi.example.com/submit_score" to enable POST
# ----------------------------

st.set_page_config(page_title=GAME_NAME, layout="centered", initial_sidebar_state="collapsed")

st.title(GAME_NAME)
st.write("Play against the computer. Quick, fun, and safe for a public tile.")

# ----- Session state init -----
if "player" not in st.session_state:
    st.session_state.player = {"name": "Guest", "wins": 0, "losses": 0, "ties": 0, "games": 0}
if "last" not in st.session_state:
    st.session_state.last = {"player_choice": None, "cpu_choice": None, "result": None}
if "history" not in st.session_state:
    st.session_state.history = []

# ----- Helper functions -----
CHOICES = ["Rock", "Paper", "Scissors"]

def cpu_play():
    return random.choice(CHOICES)

def decide(p, c):
    if p == c:
        return "Tie"
    wins = {
        "Rock": "Scissors",
        "Paper": "Rock",
        "Scissors": "Paper",
    }
    return "Win" if wins[p] == c else "Lose"

def record_result(name, result):
    st.session_state.player["games"] += 1
    if result == "Win":
        st.session_state.player["wins"] += 1
    elif result == "Lose":
        st.session_state.player["losses"] += 1
    else:
        st.session_state.player["ties"] += 1
    st.session_state.history.insert(0, {"result": result, "player": st.session_state.player["name"], "time": time.time()})
    # keep history reasonable
    st.session_state.history = st.session_state.history[:50]

def load_local_leaderboard():
    if LOCAL_LEADERBOARD_FILE.exists():
        try:
            return json.loads(LOCAL_LEADERBOARD_FILE.read_text())
        except Exception:
            return []
    return []

def save_local_leaderboard(score_entry):
    board = load_local_leaderboard()
    board.insert(0, score_entry)
    # keep only last 100
    board = board[:100]
    try:
        LOCAL_LEADERBOARD_FILE.write_text(json.dumps(board))
    except Exception:
        pass  # ignore write errors for ephemeral platforms

def submit_remote_score(score_entry):
    # optional: post to a remote endpoint if configured
    if not REMOTE_SCORE_ENDPOINT:
        return False, "Remote endpoint not configured"
    try:
        import requests
        r = requests.post(REMOTE_SCORE_ENDPOINT, json=score_entry, timeout=6)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

# ----- UI: player name and controls -----
col1, col2 = st.columns([2, 1])
with col1:
    name = st.text_input("Nickname", st.session_state.player["name"], max_chars=20)
    st.session_state.player["name"] = name.strip() or "Guest"
with col2:
    if st.button("Reset Session Score"):
        st.session_state.player.update({"wins":0,"losses":0,"ties":0,"games":0})
        st.session_state.history = []
        st.success("Session score reset")

st.markdown("---")

# ----- Game buttons -----
st.write("Choose your move:")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🪨 Rock"):
        player_choice = "Rock"
        cpu_choice = cpu_play()
        result = decide(player_choice, cpu_choice)
        st.session_state.last = {"player_choice": player_choice, "cpu_choice": cpu_choice, "result": result}
        record_result(name, result)
with c2:
    if st.button("📄 Paper"):
        player_choice = "Paper"
        cpu_choice = cpu_play()
        result = decide(player_choice, cpu_choice)
        st.session_state.last = {"player_choice": player_choice, "cpu_choice": cpu_choice, "result": result}
        record_result(name, result)
with c3:
    if st.button("✂️ Scissors"):
        player_choice = "Scissors"
        cpu_choice = cpu_play()
        result = decide(player_choice, cpu_choice)
        st.session_state.last = {"player_choice": player_choice, "cpu_choice": cpu_choice, "result": result}
        record_result(name, result)

# ----- Result display -----
last = st.session_state.last
if last["player_choice"]:
    st.subheader("Round result")
    st.write(f"**You:** {last['player_choice']}  →  **CPU:** {last['cpu_choice']}")
    if last["result"] == "Win":
        st.success("You win 🎉")
    elif last["result"] == "Lose":
        st.error("You lose 💥")
    else:
        st.info("Tie — try again")

# ----- Session scoreboard -----
st.markdown("---")
st.subheader("Session scoreboard")
p = st.session_state.player
st.write(f"**{p['name']}** — Games: **{p['games']}**, Wins: **{p['wins']}**, Losses: **{p['losses']}**, Ties: **{p['ties']}**")

# ----- Save score locally (optional) -----
col_save_left, col_save_right = st.columns([3,2])
with col_save_left:
    if st.button("Save score locally"):
        entry = {"name": p["name"], "wins": p["wins"], "losses": p["losses"], "ties": p["ties"], "games": p["games"], "ts": time.time()}
        save_local_leaderboard(entry)
        st.success("Saved to local leaderboard file")
with col_save_right:
    ok, msg = False, ""
    if st.button("Share score (remote)"):
        entry = {"name": p["name"], "wins": p["wins"], "losses": p["losses"], "ties": p["ties"], "games": p["games"], "ts": time.time()}
        ok, msg = submit_remote_score(entry)
        if ok:
            st.success("Score submitted")
        else:
            st.warning(f"Submit failed: {msg}")

# ----- Local leaderboard preview -----
st.markdown("---")
st.subheader("Local leaderboard (recent)")
board = load_local_leaderboard()
if not board:
    st.write("No saved scores yet. Use Save score locally to persist results on the host (if supported).")
else:
    for i, row in enumerate(board[:10], start=1):
        st.write(f"{i}. **{row['name']}** — Games: {row['games']}, W/L/T: {row['wins']}/{row['losses']}/{row['ties']}")

# ----- Recent history -----
st.markdown("---")
st.subheader("Recent rounds (this session)")
if not st.session_state.history:
    st.write("No rounds played yet.")
else:
    for h in st.session_state.history[:10]:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h["time"]))
        st.write(f"{ts} — {h['player']} — {h['result']}")
