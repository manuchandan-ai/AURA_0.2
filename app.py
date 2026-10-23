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

import streamlit.components.v1 as components

def render_aura_voice_core(token, username, height=520):
    html_template = r"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #040914;
      color: #e0f7fa;
      font-family: 'Rajdhani', sans-serif;
      overflow: hidden;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .hud-container {
      border: 1px solid rgba(0, 243, 255, 0.35);
      background: rgba(8, 20, 44, 0.88);
      border-radius: 14px;
      padding: 16px;
      margin: 4px;
      box-shadow: 0 0 30px rgba(0, 243, 255, 0.15);
      display: flex;
      flex-direction: column;
      flex: 1;
      min-height: 0;
    }
    .hud-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .hud-title {
      font-family: 'Orbitron', monospace;
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: 2px;
      color: #00f3ff;
      text-shadow: 0 0 12px rgba(0, 243, 255, 0.7);
    }
    .badge-status {
      font-family: 'Orbitron', monospace;
      font-size: 0.72rem;
      letter-spacing: 1px;
      padding: 5px 12px;
      border-radius: 20px;
      background: rgba(0, 243, 255, 0.15);
      border: 1px solid #00f3ff;
      color: #00f3ff;
      box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
      transition: all 0.3s ease;
    }
    .badge-status.listening {
      background: rgba(0, 243, 255, 0.25);
      border-color: #00f3ff;
      color: #00f3ff;
      box-shadow: 0 0 16px #00f3ff;
    }
    .badge-status.thinking {
      background: rgba(255, 170, 0, 0.25);
      border-color: #ffaa00;
      color: #ffaa00;
      box-shadow: 0 0 16px #ffaa00;
    }
    .badge-status.speaking {
      background: rgba(157, 78, 221, 0.25);
      border-color: #9d4edd;
      color: #9d4edd;
      box-shadow: 0 0 16px #9d4edd;
    }
    .badge-status.muted {
      background: rgba(100, 116, 139, 0.2);
      border-color: #64748b;
      color: #94a3b8;
    }
    #reactor-stage {
      width: 100%;
      height: 180px;
      position: relative;
      overflow: hidden;
      border-radius: 8px;
      margin-bottom: 8px;
      background: radial-gradient(circle at center, rgba(0, 243, 255, 0.08) 0%, transparent 70%);
    }
    #reactor-canvas {
      width: 100%;
      height: 100%;
      display: block;
    }
    .log-stream {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 10px;
      background: rgba(0, 10, 25, 0.7);
      border-radius: 8px;
      border: 1px solid rgba(0, 243, 255, 0.18);
      font-size: 0.95rem;
      min-height: 100px;
    }
    .log-msg {
      padding: 6px 12px;
      border-radius: 6px;
      line-height: 1.4;
    }
    .log-msg.user {
      background: rgba(255, 170, 0, 0.12);
      border-left: 3px solid #ffaa00;
      color: #ffedd5;
    }
    .log-msg.aura {
      background: rgba(0, 243, 255, 0.1);
      border-left: 3px solid #00f3ff;
      color: #e0f7fa;
    }
    .controls-row {
      display: flex;
      gap: 10px;
      margin-top: 10px;
      align-items: center;
    }
    .toggle-btn {
      font-family: 'Orbitron', monospace;
      font-size: 0.75rem;
      padding: 10px 18px;
      border-radius: 6px;
      border: 1px solid #00f3ff;
      background: rgba(0, 243, 255, 0.18);
      color: #fff;
      cursor: pointer;
      letter-spacing: 1px;
      transition: all 0.2s;
      white-space: nowrap;
    }
    .toggle-btn:hover {
      background: #00f3ff;
      color: #000;
      box-shadow: 0 0 15px #00f3ff;
    }
    .toggle-btn.off {
      border-color: #64748b;
      background: rgba(100, 116, 139, 0.15);
      color: #94a3b8;
    }
    .cmd-input {
      flex: 1;
      background: rgba(0, 15, 35, 0.85);
      border: 1px solid rgba(0, 243, 255, 0.3);
      border-radius: 6px;
      padding: 10px 14px;
      color: #fff;
      font-family: 'Rajdhani', sans-serif;
      font-size: 1rem;
      outline: none;
    }
    .cmd-input:focus {
      border-color: #00f3ff;
      box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }
    .cmd-btn {
      font-family: 'Orbitron', monospace;
      font-size: 0.75rem;
      padding: 10px 18px;
      border-radius: 6px;
      border: none;
      background: linear-gradient(90deg, #0066ff, #00f3ff);
      color: #000;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s;
    }
    .cmd-btn:hover {
      box-shadow: 0 0 15px #00f3ff;
      transform: translateY(-1px);
    }
  </style>
</head>
<body>
  <div class="hud-container">
    <div class="hud-header">
      <div class="hud-title">⚛️ AURA NEURAL CORE // HANDS-FREE VOICE</div>
      <div id="status-badge" class="badge-status listening">● VOICE ACTIVATED (SPEAK FREELY)</div>
    </div>

    <div id="reactor-stage">
      <div id="reactor-canvas"></div>
    </div>

    <div class="log-stream" id="log-stream">
      <div class="log-msg aura">
        <strong>AURA:</strong> Ready, __CAP_USER__. Voice activation is active. Simply speak your directive aloud at any time and I will answer vocally.
      </div>
    </div>

    <div class="controls-row">
      <button id="toggle-voice-btn" class="toggle-btn">🎙️ MIC: ACTIVE</button>
      <input type="text" id="cmd-input" class="cmd-input" placeholder="Speak hands-free with your microphone or type a directive here..." autocomplete="off">
      <button id="cmd-send-btn" class="cmd-btn">TRANSMIT ➔</button>
    </div>
  </div>

  <script>
    const API_URL = "http://127.0.0.1:8000";
    const TOKEN = "__TOKEN__";
    const OPERATOR = "__UPPER_USER__";

    const container = document.getElementById("reactor-canvas");
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const reactorGroup = new THREE.Group();
    const coreGeom = new THREE.IcosahedronGeometry(1.6, 2);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, wireframe: true, transparent: true, opacity: 0.85 });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    reactorGroup.add(coreMesh);

    const ringGeom = new THREE.TorusGeometry(2.7, 0.05, 16, 80);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x0066ff, transparent: true, opacity: 0.6 });
    const ringMesh = new THREE.Mesh(ringGeom, ringMat);
    reactorGroup.add(ringMesh);

    const ring2Geom = new THREE.TorusGeometry(2.3, 0.035, 16, 80);
    const ring2Mat = new THREE.MeshBasicMaterial({ color: 0x9d4edd, transparent: true, opacity: 0.5 });
    const ring2Mesh = new THREE.Mesh(ring2Geom, ring2Mat);
    ring2Mesh.rotation.x = Math.PI / 3;
    reactorGroup.add(ring2Mesh);

    scene.add(reactorGroup);
    camera.position.z = 6.5;

    let reactorState = 'listening';

    function animate() {
      requestAnimationFrame(animate);
      let speed = 0.01;
      if (reactorState === 'thinking') speed = 0.04;
      if (reactorState === 'speaking') speed = 0.025;

      coreMesh.rotation.x += speed;
      coreMesh.rotation.y += speed * 1.4;
      ringMesh.rotation.z += 0.012;
      ring2Mesh.rotation.y -= 0.014;

      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
      if (!container.clientHeight) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    });

    function setStatus(state, text) {
      reactorState = state;
      const badge = document.getElementById("status-badge");
      badge.className = "badge-status " + state;
      badge.innerText = text;

      if (state === 'listening') {
        coreMat.color.setHex(0x00f3ff);
        ringMat.color.setHex(0x0066ff);
      } else if (state === 'thinking') {
        coreMat.color.setHex(0xffaa00);
        ringMat.color.setHex(0xffaa00);
      } else if (state === 'speaking') {
        coreMat.color.setHex(0x9d4edd);
        ringMat.color.setHex(0x9d4edd);
      } else if (state === 'muted') {
        coreMat.color.setHex(0x64748b);
        ringMat.color.setHex(0x475569);
      }
    }

    const logStream = document.getElementById("log-stream");
    function addLog(sender, text) {
      const div = document.createElement("div");
      div.className = "log-msg " + (sender === 'user' ? 'user' : 'aura');
      div.innerHTML = `<strong>${sender === 'user' ? OPERATOR : 'AURA'}:</strong> ${text}`;
      logStream.appendChild(div);
      logStream.scrollTop = logStream.scrollHeight;
    }

    let isHandsFree = true;
    let isSpeaking = false;
    let isProcessing = false;
    let recognition = null;

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    function startListening() {
      if (!isHandsFree || isSpeaking || isProcessing || !recognition) return;
      try {
        recognition.start();
      } catch(e) {}
    }

    if (SpeechRec) {
      recognition = new SpeechRec();
      recognition.continuous = true;      // Keep mic open like Jarvis/Alexa
      recognition.interimResults = true;  // Read words as they are spoken
      recognition.lang = 'en-US';

      let silenceTimer = null;

      recognition.onstart = () => {
        if (!isSpeaking && !isProcessing) {
          setStatus('listening', '● AURA LISTENING (SPEAK FREELY)');
        }
      };

      recognition.onresult = async (event) => {
        // Clear the send timer every time a new word is detected
        clearTimeout(silenceTimer);
        
        let interim = "";
        let finalTxt = "";
        
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTxt += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        const currentSpeech = finalTxt || interim;
        if (currentSpeech.trim()) {
           setStatus('thinking', `● HEARING: "${currentSpeech}..."`);
           cmdInput.value = currentSpeech;
        }

        // JARVIS BEHAVIOR: Wait for 1.5 seconds of silence, then auto-send
        silenceTimer = setTimeout(() => {
          if (cmdInput.value.trim() && !isProcessing) {
            sendManual(); 
          }
        }, 1500);
      };

      recognition.onerror = (e) => {
        setTimeout(() => {
          if (isHandsFree && !isSpeaking && !isProcessing) startListening();
        }, 1200);
      };

      recognition.onend = () => {
        // Auto-restart mic immediately if hands-free mode is active
        if (isHandsFree && !isSpeaking && !isProcessing) {
          setTimeout(startListening, 300);
        }
      };
    } else {
      setStatus('muted', '● SPEECH API NOT SUPPORTED (USE CHROME/EDGE)');
    }

        function speakResponse(text) {
          if (!('speechSynthesis' in window)) {
            isProcessing = false;
            return;
          }
          window.speechSynthesis.cancel();
          if (recognition) {
            try { recognition.abort(); } catch(e) {}
          }
          isSpeaking = true;
          setStatus('speaking', '● AURA RESPONDING VOCALLY...');

          const cleanSpeech = text.replace(/[*#`_\[\]()]/g, "").replace(/\(Engine:[^)]*\)/g, "").trim();
          const utter = new SpeechSynthesisUtterance(cleanSpeech);
          utter.pitch = 1.0;
          utter.rate = 1.05;

          const voices = window.speechSynthesis.getVoices();
          const auraVoice = voices.find(v => v.lang.includes("en-US") || v.lang.includes("en-GB") || v.name.includes("Natural"));
          if (auraVoice) utter.voice = auraVoice;

          utter.onend = () => {
            isSpeaking = false;
            isProcessing = false;
            setStatus('muted', '● READY (CLICK MIC OR PRESS SPACE TO SPEAK)');
          };
          utter.onerror = () => {
            isSpeaking = false;
            isProcessing = false;
            setStatus('muted', '● READY (CLICK MIC OR PRESS SPACE TO SPEAK)');
          };

          window.speechSynthesis.speak(utter);
        }

        // Default to Muted so it NEVER creates an audio echo feedback loop
        isHandsFree = false;
        setStatus('muted', '● CLICK MIC OR TAP SPACEBAR TO TALK');

        const toggleBtn = document.getElementById("toggle-voice-btn");
        toggleBtn.className = "toggle-btn off";
        toggleBtn.innerText = "🔇 MIC: OFF";

        toggleBtn.onclick = () => {
          isHandsFree = !isHandsFree;
          if (isHandsFree) {
            window.speechSynthesis.cancel();
            toggleBtn.className = "toggle-btn";
            toggleBtn.innerText = "🎙️ MIC: LISTENING";
            setStatus('listening', '● LISTENING (SPEAK NOW)...');
            startListening();
          } else {
            toggleBtn.className = "toggle-btn off";
            toggleBtn.innerText = "🔇 MIC: OFF";
            setStatus('muted', '● MIC MUTED (CLICK TO TALK)');
            if (recognition) {
              try { recognition.abort(); } catch(e) {}
            }
            window.speechSynthesis.cancel();
          }
        };

        // Spacebar quick-tap trigger
        window.addEventListener('keydown', (e) => {
          if (e.code === 'Space' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            toggleBtn.click();
          }
        });

    const cmdInput = document.getElementById("cmd-input");
    const cmdBtn = document.getElementById("cmd-send-btn");

    async function sendManual() {
      const val = cmdInput.value.trim();
      if (!val) return;
      cmdInput.value = "";
      
      isProcessing = true;
      setStatus('thinking', `● THINKING: "${val.substring(0, 30)}..."`);
      addLog('user', val);

      try {
        const res = await fetch(`${API_URL}/aura/directive`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + TOKEN
          },
          body: JSON.stringify({ transcript: val })
        });
        if (res.ok) {
          const data = await res.json();
          addLog('aura', data.response_text);
          speakResponse(data.response_text);
        } else {
          const err = await res.json();
          addLog('aura', "Error: " + (err.detail || "Failed."));
          isProcessing = false;
          startListening();
        }
      } catch(e) {
        addLog('aura', "Neural Engine unreachable on port 8000.");
        isProcessing = false;
        startListening();
      }
    }

    cmdBtn.onclick = sendManual;
    cmdInput.onkeydown = (e) => { if (e.key === 'Enter') sendManual(); };
  </script>
</body>
</html>"""
    html_template = html_template.replace("__TOKEN__", str(token or ""))
    html_template = html_template.replace("__USERNAME__", str(username or "Operator"))
    html_template = html_template.replace("__UPPER_USER__", str(username or "Operator").upper())
    html_template = html_template.replace("__CAP_USER__", str(username or "Operator").capitalize())
    components.html(html_template, height=height)

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
        
        banned_user = st.session_state.get("banned_username")
        if banned_user:
            tab_login, tab_appeal = st.tabs(["🔑 Sign In", "🛡️ Appeal / Ban Inquiry"])
        else:
            tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Register Operator"])

        with tab_login:
            with st.form("login_form"):
                uname = st.text_input("Username", value=banned_user if banned_user else "")
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

        if not banned_user:
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

        if banned_user:
            with tab_appeal:
                with st.form("appeal_form", clear_on_submit=True):
                    a_user = st.text_input("Banned Username", value=banned_user)
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

    nav_items = ["Home Dashboard", "🎙️ AURA Voice Core", "Assistant Chat", "Goals & Streaks", "Reminders & Tasks", "Domain Modules", "Artifact Analysis"]
    if u.get("role") == "admin":
        nav_items.append("Admin Console")

    def on_nav():
        st.session_state.nav_selection = st.session_state.nav_bar_key

    st.radio("Navigation", nav_items, index=nav_items.index(st.session_state.nav_selection) if st.session_state.nav_selection in nav_items else 0, key="nav_bar_key", on_change=on_nav)
    
    st.markdown("---")
    st.markdown("### 💬 Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        import uuid
        st.session_state.chat_msgs = []
        st.session_state.chat_session_id = str(uuid.uuid4())
        st.session_state.nav_selection = "Assistant Chat"
        st.rerun()

    hist_req = requests.get(f"{API_URL}/chat/history", headers=get_headers())
    if hist_req.status_code == 200:
        history = hist_req.json().get("history", [])
        for sess in history:
            if st.button(f"{sess['preview']}", key=f"hist_{sess['session_id']}", use_container_width=True):
                st.session_state.chat_session_id = sess["session_id"]
                # Exclude system prompts from UI view if they exist, but normally history only saves user/assistant
                st.session_state.chat_msgs = sess["messages"]
                st.session_state.nav_selection = "Assistant Chat"
                st.rerun()

    st.markdown("---")
    if st.button("🚪 Terminate Session", use_container_width=True):
        st.session_state.token = None
        st.session_state.current_user = None
        st.rerun()

# ----------------- VIEW 1: HOME DASHBOARD -----------------
if st.session_state.nav_selection == "Home Dashboard":
    op_name = st.session_state.current_user.get("username", "Operator").capitalize()
    dash = requests.get(f"{API_URL}/dashboard/summary", headers=get_headers()).json()
    
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
        
        # Display Goals and Reminders
        if dash.get("goals"):
            st.markdown("##### 🎯 Daily Goals")
            for g in dash.get("goals")[:3]:
                st.caption(f"- {g['intention']}")
        if dash.get("reminders"):
            st.markdown("##### 🔔 Daily Tasks & Reminders")
            for r in dash.get("reminders")[:5]:
                st.caption(f"- {r['task']}")
                
        # Audio Briefing Option
        if st.button("🎧 Listen to Daily Briefing"):
            with st.spinner("Compiling tactical briefing..."):
                audio_res = requests.get(f"{API_URL}/briefing/speak", headers=get_headers())
                if audio_res.status_code == 200:
                    st.audio(audio_res.content, format="audio/wav")
                else:
                    st.error("Failed to generate audio.")

    # AURA Hands-Free Voice Neural Core Component
    with st.expander("🎙️ AURA Hands-Free Neural Voice Core (Speak Freely)", expanded=True):
        render_aura_voice_core(st.session_state.token, op_name, height=490)

    # Global Command Bar with Upload
    col_s1, col_s2 = st.columns([6, 1])
    with col_s1:
        q_search = st.text_input("🔍 Command Matrix & Cognitive Query", placeholder="Ask AURA anything, or search goals and memories...", label_visibility="collapsed")
    with col_s2:
        f_upload = st.file_uploader("Upload (AI Input)", type=["jpg", "png", "pdf", "txt", "csv", "md"], label_visibility="collapsed")
        
    if st.button("Execute Directive ➔"):
        if f_upload:
            requests.post(f"{API_URL}/artifacts/upload", files={"file": (f_upload.name, f_upload.getvalue(), f_upload.type)}, data={"prompt": q_search or "Analyze this file"}, headers=get_headers())
            st.success("Artifact ingested successfully.")
        if q_search:
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

# ----------------- VIEW: AURA VOICE CORE -----------------
elif st.session_state.nav_selection == "🎙️ AURA Voice Core":
    st.markdown("### 🎙️ AURA Hands-Free Neural Voice Core")
    st.caption("Continuous hands-free voice activation and automatic vocal responses powered by AURA's neural failover engine.")
    render_aura_voice_core(st.session_state.token, st.session_state.current_user.get("username", "Operator"), height=580)

# ----------------- VIEW 2: ASSISTANT CHAT -----------------
elif st.session_state.nav_selection == "Assistant Chat":
    if "chat_session_id" not in st.session_state:
        import uuid
        st.session_state.chat_session_id = str(uuid.uuid4())
        
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
            endpoint = "/chat/stream" if not art_id else "/chat/artifact"
            payload = {
                "message": user_in, 
                "conversation_history": st.session_state.chat_msgs[:-1], 
                "session_id": st.session_state.chat_session_id
            }
            if art_id:
                payload["artifact_id"] = art_id
            
            # Generator to parse Server-Sent Events (SSE) live
            def parse_sse_stream():
                res = requests.post(f"{API_URL}{endpoint}", json=payload, headers=get_headers(), stream=True)
                for line in res.iter_lines():
                    if line:
                        decoded = line.decode('utf-8')
                        if decoded.startswith("data: "):
                            content = decoded.replace("data: ", "").strip()
                            if content == "[DONE]":
                                break
                            try:
                                data = json.loads(content)
                                yield data.get("token", "")
                            except:
                                pass
            
            # Write the stream dynamically to the UI
            try:
                full_reply = st.write_stream(parse_sse_stream())
                st.session_state.chat_msgs.append({"role": "assistant", "content": full_reply})
            except Exception as e:
                st.error("Streaming connection failed. Ensure the backend is running on port 8000.")

# ----------------- VIEW 3: GOALS & STREAKS -----------------
elif st.session_state.nav_selection == "Goals & Streaks":
    st.markdown("### 🎯 Strategic Goals & Momentum Defense")
    
    with st.expander("➕ Define New Goal"):
        with st.form("new_goal_form"):
            new_goal_intent = st.text_input("What is your overarching objective?", placeholder="e.g. Learn full-stack development")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                goal_cat = st.selectbox("Category", ["Career", "Health & Fitness", "Learning", "Finance", "Productivity", "Other"])
            with c2:
                goal_dur = st.selectbox("Duration", ["1 Week", "30 Days", "90 Days", "6 Months", "1 Year"])
            with c3:
                goal_exp = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced", "Expert"])

            if st.form_submit_button("Generate Strategic Plan"):
                payload = {
                    "intention": new_goal_intent,
                    "category": goal_cat,
                    "duration": goal_dur,
                    "experience": goal_exp
                }
                with st.spinner("AURA is generating phases, daily routines, and extracting reminders..."):
                    requests.post(f"{API_URL}/goals", json=payload, headers=get_headers())
                st.success("Plan generated and tasks injected into your queue.")
                st.rerun()

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
            with st.container():
                st.markdown(f"#### {g['intention']} — 🔥 {g['streak']} Days")
                prog_val = g.get("progress", 0)
                st.progress(prog_val / 100.0)
                st.caption(f"⚡ **Automated Trajectory Progress: {prog_val}%** (Synchronized from streak momentum and duration)")
                
                if g.get('daily_routine'):
                    st.markdown(g['daily_routine'])
                else:
                    st.markdown("*No routine defined.*")
                
                c_ci, c_del = st.columns([1, 1])
                if c_ci.button("🔥 Daily Momentum Check-in", key=f"ci_{g['id']}", use_container_width=True):
                    requests.post(f"{API_URL}/goals/{g['id']}/checkin", headers=get_headers())
                    st.rerun()

                if c_del.button("🗑️ Delete Goal", key=f"del_{g['id']}", use_container_width=True):
                    res = requests.delete(f"{API_URL}/goals/{g['id']}", headers=get_headers())
                    if res.status_code == 200:
                        st.rerun()
                    else:
                        st.error(f"Error deleting goal: {res.text}")
            st.write("---")

# ----------------- VIEW 4: REMINDERS & TASKS -----------------
elif st.session_state.nav_selection == "Reminders & Tasks":
    st.markdown("### 🔔 Directive Execution Queue")
    with st.form("add_reminder"):
        r_text = st.text_input("Task Description")
        col1, col2 = st.columns(2)
        r_pri = col1.selectbox("Priority", ["High", "Medium", "Low"])
        r_due = col2.text_input("Due (e.g. Today, Tomorrow)", value="Today")
        if st.form_submit_button("Add Reminder"):
            requests.post(f"{API_URL}/reminders", json={"task_text": r_text, "priority": r_pri, "due_info": r_due}, headers=get_headers())
            st.success("Added.")
            st.rerun()

    dash = requests.get(f"{API_URL}/dashboard/summary", headers=get_headers()).json()
    for r in dash.get("reminders", []):
        st.markdown(f"""
        <div class="aura-card">
            <strong>{r['task']}</strong> — Priority: `{r['priority']}` | Due: `{r['due']}`
        </div>
        """, unsafe_allow_html=True)

# ----------------- VIEW 5: DOMAIN MODULES -----------------
elif st.session_state.nav_selection == "Domain Modules":
    from modules import MODULE_PERSONAS
    m = MODULE_PERSONAS.get(st.session_state.active_module)
    if m:
        st.markdown(f"### {m['icon']} {m['title']}")
        st.info(m['system_prompt'])
        st.markdown("#### Suggested Directives")
        for p in m['starter_prompts']:
            if st.button(p, use_container_width=True):
                if "chat_session_id" not in st.session_state:
                    import uuid
                    st.session_state.chat_session_id = str(uuid.uuid4())
                st.session_state.chat_msgs.append({"role": "user", "content": p})
                st.session_state.nav_selection = "Assistant Chat"
                st.rerun()
    else:
        st.markdown("### 🧩 Module Not Found")

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