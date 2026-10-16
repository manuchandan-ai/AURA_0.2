const API_URL = "http://127.0.0.1:8000";

let session = {
  token: localStorage.getItem("aura_token") || null,
  user: JSON.parse(localStorage.getItem("aura_user")) || null
};

function getHeaders() {
  return session.token ? { "Authorization": `Bearer ${session.token}`, "Content-Type": "application/json" } : {};
}

// =============================================================================
// 1. THREE.JS HOLOGRAPHIC ARC-REACTOR / NEURAL ORB
// =============================================================================
const canvasContainer = document.getElementById("reactor-canvas-container");
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
canvasContainer.appendChild(renderer.domElement);

// Core Holographic Wireframe Reactor
const reactorGroup = new THREE.Group();

// Central Icosahedron Core
const coreGeom = new THREE.IcosahedronGeometry(2.4, 2);
const coreMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, wireframe: true, transparent: true, opacity: 0.7 });
const coreMesh = new THREE.Mesh(coreGeom, coreMat);
reactorGroup.add(coreMesh);

// Outer Ring Orbit
const ringGeom = new THREE.TorusGeometry(4.2, 0.06, 16, 100);
const ringMat = new THREE.MeshBasicMaterial({ color: 0x0066ff, transparent: true, opacity: 0.5 });
const ringMesh = new THREE.Mesh(ringGeom, ringMat);
reactorGroup.add(ringMesh);

// Secondary Diagonal Ring
const ring2Geom = new THREE.TorusGeometry(3.6, 0.04, 16, 100);
const ring2Mat = new THREE.MeshBasicMaterial({ color: 0x9d4edd, transparent: true, opacity: 0.4 });
const ring2Mesh = new THREE.Mesh(ring2Geom, ring2Mat);
ring2Mesh.rotation.x = Math.PI / 3;
reactorGroup.add(ring2Mesh);

// Ambient Floating Particle Grid
const pGeom = new THREE.BufferGeometry();
const pCount = 500;
const pCoords = new Float32Array(pCount * 3);
for (let i = 0; i < pCount * 3; i++) {
  pCoords[i] = (Math.random() - 0.5) * 40;
}
pGeom.setAttribute("position", new THREE.BufferAttribute(pCoords, 3));
const pMat = new THREE.PointsMaterial({ size: 0.06, color: 0x00f3ff, transparent: true, opacity: 0.6 });
const particles = new THREE.Points(pGeom, pMat);
scene.add(particles);

scene.add(reactorGroup);
camera.position.z = 10;
reactorGroup.position.y = 1.2;

// Reactor State Pulse
let isSpeakingOrListening = false;

function animateScene() {
  requestAnimationFrame(animateScene);
  const rotSpeed = isSpeakingOrListening ? 0.025 : 0.005;

  coreMesh.rotation.x += rotSpeed;
  coreMesh.rotation.y += rotSpeed * 1.5;
  ringMesh.rotation.z += 0.008;
  ring2Mesh.rotation.y -= 0.009;
  particles.rotation.y -= 0.0005;

  renderer.render(scene, camera);
}
animateScene();

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// =============================================================================
// 2. HUD CLOCK & REAL-TIME STATUS
// =============================================================================
function updateHudClock() {
  const now = new Date();
  document.getElementById("hud-clock").innerText = now.toTimeString().split(" ")[0] + " LOCAL";
}
setInterval(updateHudClock, 1000);
updateHudClock();

// =============================================================================
// 3. J.A.R.V.I.S. VOICE SYNTHESIS & SPEECH RECOGNITION (Hands-Free)
// =============================================================================
const voiceIndicator = document.getElementById("voice-indicator");
const voiceBtn = document.getElementById("btn-voice-toggle");
const terminalStream = document.getElementById("terminal-stream");

// Text-to-Speech Output (British/Calm Jarvis Cadence)
function speakAsJarvis(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  // Strip Markdown markers for clean vocal speech
  const cleanSpeech = text.replace(/[*#`_\[\]()]/g, "").replace(/\(Engine:[^)]*\)/g, "").trim();

  const utterance = new SpeechSynthesisUtterance(cleanSpeech);
  utterance.pitch = 0.95;
  utterance.rate = 1.05;

  // Pick suitable English voice if available
  const voices = window.speechSynthesis.getVoices();
  const jarvisVoice = voices.find(v => v.lang.includes("en-GB") || v.name.includes("UK") || v.name.includes("Natural"));
  if (jarvisVoice) utterance.voice = jarvisVoice;

  utterance.onstart = () => {
    isSpeakingOrListening = true;
    coreMat.color.setHex(0x9d4edd); // Purple Pulse during Speech
  };
  utterance.onend = () => {
    isSpeakingOrListening = false;
    coreMat.color.setHex(0x00f3ff); // Restore Cyan
  };

  window.speechSynthesis.speak(utterance);
}

// Hands-Free Speech Recognition
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isSpeakingOrListening = true;
    voiceBtn.classList.add("active");
    voiceIndicator.innerText = "● J.A.R.V.I.S. LISTENING DIRECTLY...";
    coreMat.color.setHex(0xffaa00); // Amber listening state
  };

  recognition.onresult = (event) => {
    const speechResult = event.results[0][0].transcript;
    handleUserDirective(speechResult);
  };

  recognition.onerror = () => {
    resetVoiceUI();
  };

  recognition.onend = () => {
    resetVoiceUI();
  };
}

function resetVoiceUI() {
  isSpeakingOrListening = false;
  voiceBtn.classList.remove("active");
  voiceIndicator.innerText = "CLICK REACTOR OR PRESS [SPACE] TO SPEAK";
  coreMat.color.setHex(0x00f3ff);
}

voiceBtn.onclick = () => {
  if (recognition) recognition.start();
  else alert("Speech recognition not supported in this browser. Use Chromium/Edge.");
};

// Hotkey Spacebar Trigger (when not typing in an input)
window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && document.activeElement.tagName !== "INPUT" && recognition) {
    e.preventDefault();
    recognition.start();
  }
});

// =============================================================================
// 4. DIRECTIVE DISPATCH ENGINE
// =============================================================================
async function handleUserDirective(directiveText) {
  if (!directiveText.trim()) return;

  const currentUsername = (session.user && session.user.username) ? session.user.username.toUpperCase() : "OPERATOR";

  // Append User message to HUD Terminal
  terminalStream.innerHTML += `
    <div class="log-entry operator">
      <span class="sender">${currentUsername}</span>
      <span class="text">${directiveText}</span>
    </div>
  `;
  terminalStream.scrollTop = terminalStream.scrollHeight;

  try {
    const res = await fetch(`${API_URL}/jarvis/directive`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ transcript: directiveText })
    });

    if (res.ok) {
      const data = await res.json();
      terminalStream.innerHTML += `
        <div class="log-entry jarvis">
          <span class="sender">J.A.R.V.I.S. (${data.engine})</span>
          <span class="text">${data.response_text}</span>
        </div>
      `;
      terminalStream.scrollTop = terminalStream.scrollHeight;
      speakAsJarvis(data.response_text);
      syncHudTelemetry();
    } else {
      const err = await res.json();
      terminalStream.innerHTML += `<div class="log-entry jarvis" style="color:var(--neon-red);"><span class="text">${err.detail || "Directive processing failure."}</span></div>`;
    }
  } catch (err) {
    terminalStream.innerHTML += `<div class="log-entry jarvis" style="color:var(--neon-red);"><span class="text">Neural Gateway Offline.</span></div>`;
  }
}

// Text Command Box Handler
const cmdInput = document.getElementById("cmd-input");
const cmdSendBtn = document.getElementById("cmd-send-btn");

function submitTextCommand() {
  const val = cmdInput.value.trim();
  if (val) {
    handleUserDirective(val);
    cmdInput.value = "";
  }
}
cmdSendBtn.onclick = submitTextCommand;
cmdInput.onkeydown = (e) => { if (e.key === "Enter") submitTextCommand(); };

// =============================================================================
// 5. HUD TELEMETRY SYNCHRONIZATION
// =============================================================================
async function syncHudTelemetry() {
  if (!session.token) return;

  try {
    const res = await fetch(`${API_URL}/dashboard/summary`, { headers: getHeaders() });
    if (res.ok) {
      const data = await res.json();

      // Objectives List
      const goalsList = document.getElementById("hud-goals-list");
      goalsList.innerHTML = (data.goals && data.goals.length) ? data.goals.map(g => `
        <div style="margin-bottom:8px; border-left: 2px solid var(--neon-cyan); padding-left: 8px;">
          <strong style="color:#fff;">${g.intention}</strong><br>
          <small style="color:var(--neon-amber);">🔥 STREAK: ${g.streak}d | PROG: ${g.progress}%</small>
        </div>
      `).join("") : "<em>Zero objectives registered.</em>";

      // Directives List
      const remsList = document.getElementById("hud-reminders-list");
      remsList.innerHTML = (data.reminders && data.reminders.length) ? data.reminders.map(r => `
        <div style="margin-bottom:6px; color:#cceeff;">
          • ${r.task} <small style="color:var(--neon-cyan);">[${r.due}]</small>
        </div>
      `).join("") : "<em>All directives cleared.</em>";
    }

    const fzRes = await fetch(`${API_URL}/goals/freeze-status`, { headers: getHeaders() });
    if (fzRes.ok) {
      const fzData = await fzRes.json();
      document.getElementById("stat-shields").innerText = fzData.freeze_tokens;
    }
  } catch (e) {
    console.error("Telemetry sync failed", e);
  }
}

// Right Control Action Listeners
document.getElementById("btn-claim-shield").onclick = async () => {
  await fetch(`${API_URL}/goals/buy-freeze`, { method: "POST", headers: getHeaders() });
  syncHudTelemetry();
};

document.getElementById("btn-morning-briefing").onclick = async () => {
  const res = await fetch(`${API_URL}/briefing/listen`, { headers: getHeaders() });
  if (res.ok) {
    const blob = await res.blob();
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();
  }
};

document.getElementById("btn-export-backup").onclick = async () => {
  const res = await fetch(`${API_URL}/export/json`, { headers: getHeaders() });
  if (res.ok) {
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `AURA_WORKSPACE_${Date.now()}.json`;
    a.click();
  }
};

document.getElementById("btn-session-kill").onclick = () => {
  localStorage.clear();
  location.reload();
};

// =============================================================================
// 6. BIOMETRIC AUTHENTICATION MODAL
// =============================================================================
const authModal = document.getElementById("auth-modal");
const authForm = document.getElementById("auth-form");

function verifySession() {
  if (!session.token || !session.user) {
    authModal.style.display = "flex";
  } else {
    authModal.style.display = "none";
    document.getElementById("stat-user-badge").innerText = `OPERATOR: ${session.user.username.toUpperCase()}`;
    document.getElementById("dos-user").innerText = session.user.username.toUpperCase();
    document.getElementById("dos-role").innerText = session.user.role.toUpperCase();
    syncHudTelemetry();
  }
}

authForm.onsubmit = async (e) => {
  e.preventDefault();
  const uname = document.getElementById("auth-user").value;
  const pwd = document.getElementById("auth-pwd").value;
  const errLog = document.getElementById("auth-error");

  try {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: uname, password: pwd })
    });
    const data = await res.json();
    if (res.ok) {
      session.token = data.access_token;
      session.user = data;
      localStorage.setItem("aura_token", data.access_token);
      localStorage.setItem("aura_user", JSON.stringify(data));
      verifySession();
      speakAsJarvis(`Welcome back, ${data.username}. All neural subsystems are initialized.`);
    } else {
      errLog.innerText = data.detail || "Authentication rejected.";
    }
  } catch (err) {
    errLog.innerText = "Neural Engine unreachable on port 8000.";
  }
};

verifySession();