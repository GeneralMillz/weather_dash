def render(services, st, state):
    role = state.get("role", "viewer")
    st.info(f"🔐 You are logged in as **{state['user']}** with role: **{role}**")
