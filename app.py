import os
import json
from datetime import datetime, date
import requests
import streamlit as st

st.set_page_config(page_title="AURA // Autonomous Neural Core", page_icon="⚛️", layout="wide")

API_URL = "http://127.0.0.1:8000"

# State Initialization
for key, default in [
    ("token", None),
    ("current_user", None),
    ("nav_selection", "Home Dashboard"),
    ("chat_msgs", []),
    ("active_module", "career")
]:
    if key not in st.session_state:
        st.session_state[key] = default

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

# Cyberpunk UI Styling
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at 50% 10%, #150d2a 0%, #070312 100%); color: #f8fafc; }
    .aura-card {
        background: rgba(18, 12, 38, 0.7);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(12px);
        margin-bottom: 12px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white; border: none; border-radius: 8px; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- ACCESS PORTAL & GOVERNANCE VIEW -----------------
if not st.session_state.token:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h2 style='text-align:center; color:#c084fc;'>⚛️ AURA ACCESS GATEWAY</h2>", unsafe_allow_html=True)
        tab_login, tab_register, tab_appeal = st.tabs(["🔑 Sign In", "📝 Register Operator", "🛡️ Appeal / Ban Inquiry"])

        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Authenticate Operator ➔", use_container_width=True):
                    try:
                        res = requests.post(f"{API_URL}/auth/login", json={"username": uname.strip(), "password": pwd.strip()})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.current_user = data
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Authentication rejected."))
                    except Exception as e:
                        st.error(f"Cannot reach server: {e}")

        with tab_register:
            with st.form("reg_form", clear_on_submit=True):
                r_user = st.text_input("Username*")
                r_pass = st.text_input("Password*", type="password")
                r_email = st.text_input("Email")
                r_phone = st.text_input("Phone Number")
                r_addr = st.text_input("Station / Address")
                r_bio = st.text_area("Technical Specialization")
                r_pic = st.file_uploader("Upload Profile Image", type=["jpg", "png"])
                if st.form_submit_button("Submit Registration for Approval ➔", use_container_width=True):
                    if r_user and r_pass:
                        files = {"avatar": (r_pic.name, r_pic.getvalue(), r_pic.type)} if r_pic else None
                        data = {"username": r_user, "password": r_pass, "email": r_email, "phone": r_phone, "address": r_addr, "bio": r_bio}
                        res = requests.post(f"{API_URL}/auth/register", data=data, files=files)
                        if res.status_code == 200:
                            st.info("Registration submitted. Your account is pending Admin approval.")
                        else:
                            st.error(res.text)

        with tab_appeal:
            with st.form("appeal_form", clear_on_submit=True):
                a_user = st.text_input("Banned Username")
                a_type = st.selectbox("Inquiry Type", ["unban", "info"])
                a_msg = st.text_area("Explanation / Request Details")
                if st.form_submit_button("Transmit Appeal to Admin ➔", use_container_width=True):
                    res = requests.post(f"{API_URL}/auth/appeal", json={"username": a_user, "appeal_type": a_type, "message": a_msg})
                    if res.status_code == 200:
                        st.success("Appeal transmitted to the security desk.")
                    else:
                        st.error(res.json().get("detail", "Error submitting appeal."))
    st.stop()

# ----------------- SIDEBAR PROFILE & UNIFIED NAVIGATION -----------------
with st.sidebar:
    u = st.session_state.current_user
    col_av, col_tx = st.columns([1, 2])
    with col_av:
        if u.get("profile_pic") and os.path.exists(u["profile_pic"]):
            st.image(u["profile_pic"], width=65)
        else:
            st.markdown("<h2 style='margin:0;'>👤</h2>", unsafe_allow_html=True)
    with col_tx:
        st.markdown(f"**{u['username'].upper()}**")
        st.caption(f"Role: `{u['role'].upper()}`")

    nav_items = ["Home Dashboard", "Assistant Chat", "Goals & Streaks", "Reminders & Tasks", "Domain Modules", "Artifact Analysis", "Memory Vault"]
    if u.get("role") == "admin":
        nav_items.append("Admin Console")

    def on_nav():
        st.session_state.nav_selection = st.session_state.nav_bar_key

    st.radio("Navigation", nav_items, index=nav_items.index(st.session_state.nav_selection) if st.session_state.nav_selection in nav_items else 0, key="nav_bar_key", on_change=on_nav)
    
    if st.button("🚪 Terminate Session", use_container_width=True):
        st.session_state.token = None
        st.session_state.current_user = None
        st.rerun()

# ----------------- VIEW 1: HOME DASHBOARD -----------------
if st.session_state.nav_selection == "Home Dashboard":
    op_name = st.session_state.current_user.get("username", "Operator").capitalize()
    
    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown(f"# ⚛️ Neural Control Plane")
        st.caption(f"Operator **{op_name}** authenticated. Cognitive systems nominal.")
    with col_h2:
        st.markdown(f"""
        <div class="aura-card" style="text-align:right;">
            <small style="color:#94a3b8;">Active Session</small><br>
            <strong style="color:#38bdf8; font-size:1.2rem;">Good day, {op_name}</strong>
        </div>
        """, unsafe_allow_html=True)

    # Global Command Bar
    q_search = st.text_input("🔍 Command Matrix & Cognitive Query", placeholder="Ask AURA anything, or search goals and memories...")
    if q_search and st.button("Execute Directive ➔"):
        st.session_state.chat_msgs.append({"role": "user", "content": q_search})
        st.session_state.nav_selection = "Assistant Chat"
        st.rerun()

    # Persona Quick-Toggles
    c_m = st.columns(6)
    modules = [("💼 Career", "career"), ("💻 Coding", "coding"), ("🛡️ SecOps", "cybersecurity"), ("🪙 Finance", "finance"), ("❤️ Health", "health"), ("⚡ Productivity", "productivity")]
    for idx, (label, mkey) in enumerate(modules):
        if c_m[idx].button(label, use_container_width=True):
            st.session_state.active_module = mkey
            st.session_state.nav_selection = "Domain Modules"
            st.rerun()

    # Telemetry
    dash = requests.get(f"{API_URL}/dashboard/summary", headers=get_headers()).json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Objectives", len(dash.get("goals", [])))
    c2.metric("Directives Pending", len(dash.get("reminders", [])))
    c3.metric("Peak Streak", f"🔥 {max([g['streak'] for g in dash.get('goals', [])], default=0)}d")

# ----------------- VIEW 2: ASSISTANT CHAT -----------------
elif st.session_state.nav_selection == "Assistant Chat":
    st.markdown("### 💬 AURA Reasoning Terminal")
    art_res = requests.get(f"{API_URL}/artifacts", headers=get_headers()).json()
    art_opts = {"None (General Reasoning)": None}
    for a in art_res.get("artifacts", []):
        art_opts[f"📄 {a['filename']} ({a['size_kb']} KB)"] = a["id"]
    
    sel = st.selectbox("Attach Artifact for Local Vector Grounding:", list(art_opts.keys()))
    art_id = art_opts[sel]

    for m in st.session_state.chat_msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if user_in := st.chat_input("Input query..."):
        st.session_state.chat_msgs.append({"role": "user", "content": user_in})
        with st.chat_message("user"):
            st.markdown(user_in)
        with st.chat_message("assistant"):
            endpoint = "/chat/artifact" if art_id else "/chat"
            payload = {"message": user_in, "conversation_history": st.session_state.chat_msgs[:-1]}
            if art_id:
                payload["artifact_id"] = art_id
            res = requests.post(f"{API_URL}{endpoint}", json=payload, headers=get_headers())
            reply = res.json().get("response", "Error")
            st.markdown(reply)
            st.session_state.chat_msgs.append({"role": "assistant", "content": reply})

# ----------------- VIEW 3: GOALS & STREAKS -----------------
elif st.session_state.nav_selection == "Goals & Streaks":
    st.markdown("### 🎯 Strategic Goals & Momentum Defense")
    fz = requests.get(f"{API_URL}/goals/freeze-status", headers=get_headers()).json()
    col_fz, col_btn = st.columns([4, 1.2])
    col_fz.info(f"🛡️ **Streak Freeze Shields:** {fz.get('freeze_tokens', 0)} active.")
    if col_btn.button("➕ Claim Shield"):
        requests.post(f"{API_URL}/goals/buy-freeze", headers=get_headers())
        st.rerun()

    dash = requests.get(f"{API_URL}/dashboard/summary", headers=get_headers()).json()
    for g in dash.get("goals", []):
        if g.get("in_recovery"):
            st.warning(f"⚠️ Recovery Protocol: **{g['intention']}**")
            st.caption(f"Task: {g.get('recovery_task')}")
            note = st.text_input("Proof note:", key=f"rec_{g['id']}")
            if st.button("Solve Recovery", key=f"s_{g['id']}"):
                requests.post(f"{API_URL}/goals/{g['id']}/solve-recovery", json={"submission_note": note}, headers=get_headers())
                st.rerun()
        else:
            st.markdown(f"#### {g['intention']} — 🔥 {g['streak']} Days")
            if st.button("Check-in Today", key=f"ci_{g['id']}"):
                requests.post(f"{API_URL}/goals/{g['id']}/checkin", headers=get_headers())
                st.rerun()

# ----------------- VIEW 4: REMINDERS & TASKS -----------------
elif st.session_state.nav_selection == "Reminders & Tasks":
    st.markdown("### 🔔 Directive Execution Queue")
    dash = requests.get(f"{API_URL}/dashboard/summary", headers=get_headers()).json()
    for r in dash.get("reminders", []):
        st.markdown(f"""
        <div class="aura-card">
            <strong>{r['task']}</strong> — Priority: `{r['priority']}` | Due: `{r['due']}`
        </div>
        """, unsafe_allow_html=True)

# ----------------- VIEW 5: DOMAIN MODULES -----------------
elif st.session_state.nav_selection == "Domain Modules":
    st.markdown(f"### 🧩 Specialized Persona: `{st.session_state.active_module.upper()}`")
    st.info("Persona active. Submit queries in chat to receive responses tailored to this domain directive.")

# ----------------- VIEW 6: ARTIFACT ANALYSIS -----------------
elif st.session_state.nav_selection == "Artifact Analysis":
    st.markdown("### 📂 Ingest Documents, Codebases, & Architecture")
    f = st.file_uploader("Upload Document for Vector Search", type=["py", "txt", "md", "json", "csv"])
    if f and st.button("Ingest & Vectorize"):
        requests.post(f"{API_URL}/artifacts/upload", files={"file": (f.name, f.getvalue(), f.type)}, headers=get_headers())
        st.success("Artifact ingested and indexed.")
        st.rerun()

# ----------------- VIEW 7: MEMORY VAULT -----------------
elif st.session_state.nav_selection == "Memory Vault":
    st.markdown("### 🧠 Cognitive Knowledge Vault")
    st.info("Extracted constraints, traits, and facts are injected into system prompts during reasoning.")

# ----------------- VIEW 8: ADMIN CONSOLE -----------------
elif st.session_state.nav_selection == "Admin Console":
    st.markdown("### 🛡️ Administrative Governance & Operator Desk")
    tab_pend, tab_all, tab_app = st.tabs(["⏳ Pending Approvals", "👥 Operator Directory & Bans", "📬 Banned Appeals"])

    with tab_pend:
        pending = requests.get(f"{API_URL}/admin/pending-operators", headers=get_headers()).json().get("pending_operators", [])
        if not pending:
            st.info("No operator registrations awaiting review.")
        for p in pending:
            st.markdown(f"**Operator:** `{p['username']}` | Email: {p['email']} | Specialization: {p['bio']}")
            col_ap, col_rj = st.columns([1, 1])
            if col_ap.button("✅ Approve Access", key=f"ap_{p['id']}"):
                requests.post(f"{API_URL}/admin/operators/{p['id']}/status", json={"action": "approve"}, headers=get_headers())
                st.rerun()
            if col_rj.button("❌ Reject Request", key=f"rj_{p['id']}"):
                requests.post(f"{API_URL}/admin/operators/{p['id']}/status", json={"action": "reject"}, headers=get_headers())
                st.rerun()
            st.write("---")

    with tab_all:
        users = requests.get(f"{API_URL}/admin/users", headers=get_headers()).json().get("users", [])
        for op in users:
            col_info, col_ban = st.columns([3, 1])
            with col_info:
                st.write(f"**{op['username']}** | Role: `{op['role']}` | Status: `{op.get('status', 'active')}` | Shields: {op['freeze_tokens']}")
            with col_ban:
                if op["role"] != "admin":
                    if st.button("🚫 Ban Operator", key=f"ban_{op['id']}"):
                        requests.post(f"{API_URL}/admin/operators/{op['id']}/status", json={"action": "ban", "reason": "Administrative suspension"}, headers=get_headers())
                        st.rerun()

    with tab_app:
        appeals = requests.get(f"{API_URL}/admin/appeals", headers=get_headers()).json().get("appeals", [])
        if not appeals:
            st.info("No pending appeals.")
        for ap in appeals:
            st.markdown(f"**Operator:** `{ap['username']}` ({ap['type']})")
            st.write(f"Message: {ap['message']}")
            if st.button("Reactivate Operator", key=f"unban_{ap['id']}"):
                requests.post(f"{API_URL}/admin/operators/{ap['user_id']}/status", json={"action": "unban"}, headers=get_headers())
                st.rerun()