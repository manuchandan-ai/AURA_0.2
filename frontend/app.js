// frontend/app.js
(() => {
  "use strict";

  const API_URL = "http://127.0.0.1:8000";

  let state = {
    token: localStorage.getItem("aura_token") || null,
    user: JSON.parse(localStorage.getItem("aura_user") || "null")
  };

  function authHeaders() {
    return state.token ? { "Authorization": `Bearer ${state.token}` } : {};
  }

  // =============================================================================
  // 1. THREE.JS MONOCHROME CORE (Audio Reactive)
  // =============================================================================
  const container = document.getElementById("canvas-container");
  if (!container) return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  const coreGroup = new THREE.Group();

  // Wireframe outer mesh
  const geom = new THREE.IcosahedronGeometry(2.2, 2);
  const mat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    wireframe: true,
    transparent: true,
    opacity: 0.18
  });
  const wireCore = new THREE.Mesh(geom, mat);
  coreGroup.add(wireCore);

  // Inner floating particle field
  const pGeom = new THREE.BufferGeometry();
  const pCount = 300;
  const pCoords = new Float32Array(pCount * 3);
  for (let i = 0; i < pCount * 3; i++) {
    pCoords[i] = (Math.random() - 0.5) * 16;
  }
  pGeom.setAttribute("position", new THREE.BufferAttribute(pCoords, 3));
  const pMat = new THREE.PointsMaterial({ size: 0.04, color: 0xffffff, transparent: true, opacity: 0.4 });
  const particles = new THREE.Points(pGeom, pMat);
  scene.add(particles);

  scene.add(coreGroup);
  camera.position.z = 7;
  coreGroup.position.y = 0.5;

  // Audio Visualizer Context
  window.AURA_AUDIO = window.AURA_AUDIO || {
    ctx: null,
    analyser: null,
    dataArray: null,
    active: false
  };

  async function setupMicVisualizer() {
    if (window.AURA_AUDIO.active) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      const src = ctx.createMediaStreamSource(stream);
      src.connect(analyser);

      window.AURA_AUDIO.ctx = ctx;
      window.AURA_AUDIO.analyser = analyser;
      window.AURA_AUDIO.dataArray = new Uint8Array(analyser.frequencyBinCount);
      window.AURA_AUDIO.active = true;
      const hint = document.getElementById("voice-hint");
      if (hint) hint.innerText = "AUDIO SENSORS ACTIVE // LISTENING";
    } catch (e) {
      const hint = document.getElementById("voice-hint");
      if (hint) hint.innerText = "MIC ACCESS REFUSED";
    }
  }

  function animate() {
    requestAnimationFrame(animate);

    let scale = 1.0;
    if (window.AURA_AUDIO.active && window.AURA_AUDIO.analyser) {
      window.AURA_AUDIO.analyser.getByteFrequencyData(window.AURA_AUDIO.dataArray);
      const avg = window.AURA_AUDIO.dataArray.reduce((acc, v) => acc + v, 0) / window.AURA_AUDIO.dataArray.length;
      scale = 1.0 + (avg / 255.0) * 0.5;
    }

    wireCore.scale.set(scale, scale, scale);
    wireCore.rotation.x += 0.002 * scale;
    wireCore.rotation.y += 0.004 * scale;
    particles.rotation.y -= 0.0003;

    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  // =============================================================================
  // 2. REAL-TIME TOKEN STREAMING (SSE Client)
  // =============================================================================
  const streamBox = document.getElementById("chat-stream-box");
  const promptInput = document.getElementById("user-prompt-input");
  const sendBtn = document.getElementById("send-prompt-btn");
  const typingDot = document.getElementById("typing-indicator");

  async function dispatchStreamingChat(query) {
    if (!query.trim() || state.isProcessing) return;

    // Check authentication before sending
    if (!state.token) {
      appendTerminalMessage("SYSTEM", "Authentication required. Please click AUTH in the top bar to sign in.");
      triggerAuthModal();
      return;
    }

    state.isProcessing = true;
    appendTerminalMessage(state.user ? state.user.username : "OPERATOR", query);

    // Create live target bubble
    const auraBubble = document.createElement("div");
    auraBubble.className = "msg aura";
    auraBubble.innerHTML = `<span class="role">AURA</span><p class="content"></p>`;
    terminalBox.appendChild(auraBubble);
    const targetP = auraBubble.querySelector(".content");

    setSystemStatus("THINKING", true);

    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          message: query,
          session_id: state.currentSessionId
        })
      });

      if (res.status === 401) {
        targetP.innerText = "Session expired or unauthorized. Please re-authenticate.";
        triggerAuthModal();
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        targetP.innerText = `Error [HTTP ${res.status}]: ${errData.detail || "Server error occurred."}`;
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let fullText = "";
      let streamBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });
        const parts = streamBuffer.split("\n\n");
        // Retain the last incomplete fragment in the buffer
        streamBuffer = parts.pop();

        for (const part of parts) {
          const trimmed = part.trim();
          if (trimmed.startsWith("data: ")) {
            const payload = trimmed.replace(/^data:\s*/, "").trim();
            if (payload === "[DONE]") break;
            try {
              const parsed = JSON.parse(payload);
              if (parsed.token) {
                fullText += parsed.token;
                targetP.innerText = fullText;
                terminalBox.scrollTop = terminalBox.scrollHeight;
              }
              if (parsed.session_id) {
                state.currentSessionId = String(parsed.session_id);
                localStorage.setItem("aura_session_id", state.currentSessionId);
              }
            } catch (err) {
              // Ignore partial JSON in stream chunk
            }
          }
        }
      }
    } catch (err) {
      targetP.innerText = `Connection failed: ${err.message}`;
    } finally {
      state.isProcessing = false;
      setSystemStatus("IDLE", false);
      syncTelemetry();
    }
  }

  // =============================================================================
  // 3. TELEMETRY & KNOWLEDGE SYNC
  // =============================================================================
  async function syncTelemetry() {
    if (!state.token) return;

    try {
      const res = await fetch(`${API_URL}/dashboard/summary`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        const sessDisplay = document.getElementById("session-display");
        if (sessDisplay) sessDisplay.innerText = (data.user.username || "--").toUpperCase();

        const goalsDiv = document.getElementById("goals-list");
        if (goalsDiv) {
          goalsDiv.innerHTML = data.goals.length ? data.goals.map(g => `
            <div style="border-left: 2px solid #fff; padding-left: 6px; margin-bottom: 4px;">
              <b>${g.intention}</b>
              <span style="color:var(--muted); font-size:0.7rem; display:block;">🔥 ${g.streak}d // ${g.progress}%</span>
            </div>
          `).join("") : `<p class="placeholder-text">Zero objectives configured.</p>`;
        }

        const remsDiv = document.getElementById("reminders-list");
        if (remsDiv) {
          remsDiv.innerHTML = data.reminders.length ? data.reminders.map(r => `
            <div>• ${r.task} <small style="color:var(--muted);">[${r.due}]</small></div>
          `).join("") : `<p class="placeholder-text">All directives cleared.</p>`;
        }
      }

      const fzRes = await fetch(`${API_URL}/goals/freeze-status`, { headers: authHeaders() });
      if (fzRes.ok) {
        const fz = await fzRes.json();
        const shieldsEl = document.getElementById("stat-shields");
        if (shieldsEl) shieldsEl.innerText = fz.freeze_tokens || 0;
      }

      const artsRes = await fetch(`${API_URL}/artifacts`, { headers: authHeaders() });
      if (artsRes.ok) {
        const arts = await artsRes.json();
        const artDiv = document.getElementById("artifacts-list");
        if (artDiv) {
          artDiv.innerHTML = arts.artifacts && arts.artifacts.length ? arts.artifacts.map(a => `
            <div>📄 ${a.filename} <small style="color:var(--muted);">(${a.size_kb} KB)</small></div>
          `).join("") : `<p class="placeholder-text">No files indexed.</p>`;
        }
      }
    } catch (err) {
      console.warn("Telemetry sync notice:", err);
    }
  }

  // =============================================================================
  // 4. AUTH MODAL & MICROPHONE BINDINGS
  // =============================================================================
  const authModal = document.getElementById("auth-modal");
  const authBtn = document.getElementById("auth-trigger-btn");
  const loginForm = document.getElementById("login-form");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const micBtn = document.getElementById("mic-trigger");
  const fileUploader = document.getElementById("file-uploader");

  function triggerAuthModal() {
    if (authModal) authModal.style.display = "flex";
  }

  if (authBtn) authBtn.onclick = triggerAuthModal;
  if (closeModalBtn) closeModalBtn.onclick = () => { if (authModal) authModal.style.display = "none"; };

  if (loginForm) {
    loginForm.onsubmit = async (e) => {
      e.preventDefault();
      const uname = document.getElementById("auth-username").value.trim();
      const pwd = document.getElementById("auth-password").value.trim();
      const errLog = document.getElementById("auth-error-msg");

      try {
        const res = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: uname, password: pwd })
        });
        const data = await res.json();
        if (res.ok) {
          state.token = data.access_token;
          state.user = data;
          localStorage.setItem("aura_token", data.access_token);
          localStorage.setItem("aura_user", JSON.stringify(data));
          if (authModal) authModal.style.display = "none";
          syncTelemetry();
        } else {
          if (errLog) errLog.innerText = data.detail || "Authentication rejected.";
        }
      } catch (err) {
        if (errLog) errLog.innerText = "Backend unreachable.";
      }
    };
  }

  if (micBtn) {
    micBtn.onclick = async () => {
      await setupMicVisualizer();
    };
  }

  if (fileUploader) {
    fileUploader.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const form = new FormData();
      form.append("file", file);
      form.append("prompt", "Analyze and summarize this document.");

      const statusElem = document.getElementById("system-status");
      if (statusElem) statusElem.innerText = "INDEXING";

      const res = await fetch(`${API_URL}/artifacts/upload`, {
        method: "POST",
        headers: authHeaders(),
        body: form
      });

      if (res.ok) {
        syncTelemetry();
      }
      if (statusElem) statusElem.innerText = "IDLE";
    };
  }

  syncTelemetry();
})();