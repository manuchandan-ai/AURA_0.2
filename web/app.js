// =============================================================================
// AURA 2.0 // Modern Unified Web Application Core
// =============================================================================

const API_URL = window.location.origin; // Automatically connects to FastAPI host

let state = {
  token: localStorage.getItem("aura_token") || null,
  user: JSON.parse(localStorage.getItem("aura_user")) || null,
  sessionId: localStorage.getItem("aura_session_id") || generateUUID(),
  messages: [],
  selectedFile: null,
  activeView: "home", // Default landing view is now Home Dashboard
  isListening: false,
  isSpeaking: false,
  micPermissionGranted: false,
};

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function getHeaders() {
  return state.token ? {
    "Authorization": `Bearer ${state.token}`,
    "Content-Type": "application/json"
  } : { "Content-Type": "application/json" };
}

function isTokenExpired(token) {
  if (!token) return true;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    const payload = JSON.parse(atob(parts[1]));
    if (!payload.exp) return false;
    return (Date.now() / 1000) >= (payload.exp - 30);
  } catch (e) {
    return false;
  }
}

async function fetchWithAuth(url, options = {}) {
  if (state.token && isTokenExpired(state.token)) {
    console.warn("Proactive token expiration detected.");
    logoutUser();
    alert("Your session has timed out. Please log in to continue.");
    throw new Error("Session expired");
  }

  const isFormData = options.body instanceof FormData;
  const authHeaders = getHeaders();
  if (isFormData) {
    delete authHeaders["Content-Type"];
  }

  options.headers = {
    ...authHeaders,
    ...(options.headers || {})
  };

  const response = await fetch(url, options);
  if (response.status === 401) {
    console.warn("401 Unauthorized encountered from backend.");
    logoutUser();
    alert("Session expired or unauthorized. Please log in again.");
    throw new Error("Unauthorized");
  }
  return response;
}

function refreshIcons() {
  if (window.lucide) lucide.createIcons();
}

// =============================================================================
// =============================================================================
// 0. GET STARTED / INITIAL LANDING SCREEN CONTROLLER
// =============================================================================
const landingScreen = document.getElementById("landing-screen");
const landingCtaBox = document.getElementById("landing-cta-box");
const btnLandingTopCta = document.getElementById("btn-landing-top-cta");
const btnCloseAuthModal = document.getElementById("btn-close-auth-modal");
const navBtnLanding = document.getElementById("nav-btn-landing");

function renderLandingScreen() {
  if (!landingScreen || !landingCtaBox) return;

  if (state.token && state.user) {
    const uname = (state.user.username || "Operator");
    const capitalName = uname.charAt(0).toUpperCase() + uname.slice(1);
    
    if (btnLandingTopCta) {
      btnLandingTopCta.innerText = "Enter Workspace ➔";
      btnLandingTopCta.onclick = () => enterWorkspace();
    }

    landingCtaBox.innerHTML = `
      <div class="p-5 rounded-2xl bg-surface-100/90 border border-teal-500/30 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="text-left flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300 font-bold text-sm">
            ${capitalName.charAt(0)}
          </div>
          <div>
            <span class="text-[10px] text-teal-400 font-bold uppercase tracking-wider block">Active Session Found</span>
            <span class="text-sm font-bold text-white">Operator ${capitalName}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <button id="btn-landing-resume" class="flex-1 sm:flex-initial px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-surface-200 font-bold text-xs transition shadow-lg shadow-teal-500/20">
            Continue to Dashboard ➔
          </button>
          <button id="btn-landing-switch" class="px-3.5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-medium transition">
            Sign Out
          </button>
        </div>
      </div>
    `;

    const resumeBtn = document.getElementById("btn-landing-resume");
    if (resumeBtn) resumeBtn.onclick = () => enterWorkspace();

    const switchBtn = document.getElementById("btn-landing-switch");
    if (switchBtn) switchBtn.onclick = () => {
      logoutUser();
      renderLandingScreen();
    };
  } else {
    if (btnLandingTopCta) {
      btnLandingTopCta.innerText = "Sign In";
      btnLandingTopCta.onclick = () => openAuthModal("login");
    }

    landingCtaBox.innerHTML = `
      <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
        <button id="btn-landing-start" class="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-400 hover:to-indigo-500 text-white font-bold text-sm shadow-xl shadow-teal-500/20 transition flex items-center justify-center gap-2">
          <span>Get Started ➔</span>
        </button>
        <button id="btn-landing-signin" class="w-full sm:w-auto px-6 py-3 rounded-xl bg-surface-100/90 hover:bg-white/10 border border-surface-border text-slate-200 font-semibold text-sm transition">
          Operator Sign In
        </button>
      </div>
      <p class="text-[11px] text-slate-400 mt-3">Default accounts: <code class="text-teal-400">admin / admin123</code> &bull; <code class="text-teal-400">john / operator123</code></p>
    `;

    const startBtn = document.getElementById("btn-landing-start");
    if (startBtn) startBtn.onclick = () => openAuthModal("register");

    const signinBtn = document.getElementById("btn-landing-signin");
    if (signinBtn) signinBtn.onclick = () => openAuthModal("login");
  }

  refreshIcons();
}

function enterWorkspace() {
  if (!state.token || !state.user) {
    openAuthModal("login");
    return;
  }
  if (landingScreen) landingScreen.classList.add("hidden");
  checkAuth();
}

function showLanding() {
  if (landingScreen) landingScreen.classList.remove("hidden");
  renderLandingScreen();
}

if (navBtnLanding) {
  navBtnLanding.onclick = () => showLanding();
}

// =============================================================================
// SLIDEBAR CONTROLLER
// =============================================================================
const sidebar = document.getElementById("sidebar");
const btnToggleSidebar = document.getElementById("btn-toggle-sidebar");
const btnSidebarCollapse = document.getElementById("btn-sidebar-collapse");
const sidebarOverlay = document.getElementById("sidebar-overlay");

let isSidebarOpen = localStorage.getItem("aura_sidebar_open") !== "false";

function applySidebarState() {
  if (!sidebar) return;
  if (isSidebarOpen) {
    sidebar.classList.remove("slide-collapsed");
    if (sidebarOverlay && window.innerWidth < 768) sidebarOverlay.classList.remove("hidden");
  } else {
    sidebar.classList.add("slide-collapsed");
    if (sidebarOverlay) sidebarOverlay.classList.add("hidden");
  }
  localStorage.setItem("aura_sidebar_open", isSidebarOpen);
  refreshIcons();
}

function toggleSidebar() {
  isSidebarOpen = !isSidebarOpen;
  applySidebarState();
}

if (btnToggleSidebar) btnToggleSidebar.onclick = toggleSidebar;
if (btnSidebarCollapse) btnSidebarCollapse.onclick = () => {
  isSidebarOpen = false;
  applySidebarState();
};
if (sidebarOverlay) sidebarOverlay.onclick = () => {
  isSidebarOpen = false;
  applySidebarState();
};

// =============================================================================
// UPWARD SCROLLING & SCROLL-TO-TOP CONTROLLER
// =============================================================================
const btnScrollTop = document.getElementById("btn-scroll-top");

function handleScrollTelemetry(target) {
  if (!btnScrollTop) return;
  const scrollTop = target.scrollTop || window.scrollY || 0;
  if (scrollTop > 150) {
    btnScrollTop.classList.remove("opacity-0", "pointer-events-none");
    btnScrollTop.classList.add("opacity-100", "pointer-events-auto");
  } else {
    btnScrollTop.classList.add("opacity-0", "pointer-events-none");
    btnScrollTop.classList.remove("opacity-100", "pointer-events-auto");
  }
}

window.addEventListener("scroll", () => handleScrollTelemetry(window));
if (landingScreen) {
  landingScreen.addEventListener("scroll", (e) => handleScrollTelemetry(e.target));
}
document.querySelectorAll(".view-panel").forEach(panel => {
  panel.addEventListener("scroll", (e) => handleScrollTelemetry(e.target));
});

if (btnScrollTop) {
  btnScrollTop.onclick = () => {
    if (landingScreen && !landingScreen.classList.contains("hidden")) {
      landingScreen.scrollTo({ top: 0, behavior: "smooth" });
    }
    const activePanel = document.querySelector(".view-panel:not(.hidden)");
    if (activePanel) {
      activePanel.scrollTo({ top: 0, behavior: "smooth" });
    }
    const chatMsgs = document.getElementById("chat-messages");
    if (chatMsgs) {
      chatMsgs.scrollTo({ top: 0, behavior: "smooth" });
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
}

// =============================================================================
// 1. AUTHENTICATION & USER PROFILE
// =============================================================================
const authModal = document.getElementById("modal-auth");
const authForm = document.getElementById("form-auth");
const authError = document.getElementById("auth-error-msg");
const navAdminTab = document.getElementById("nav-admin-tab");

const tabAuthLogin = document.getElementById("tab-auth-login");
const tabAuthRegister = document.getElementById("tab-auth-register");
const formAuth = document.getElementById("form-auth");
const formRegister = document.getElementById("form-register");
const regStatus = document.getElementById("reg-status-msg");

function openAuthModal(tab = "login") {
  authModal.classList.remove("hidden");
  authModal.classList.add("flex");
  switchAuthTab(tab);
}

function closeAuthModal() {
  authModal.classList.add("hidden");
  authModal.classList.remove("flex");
  authError.innerText = "";
  if (regStatus) regStatus.innerText = "";
}

if (btnCloseAuthModal) btnCloseAuthModal.onclick = closeAuthModal;

function switchAuthTab(tab) {
  const modalContainer = document.getElementById("modal-auth-container");
  if (tab === "register") {
    if (modalContainer) {
      modalContainer.classList.remove("max-w-sm");
      modalContainer.classList.add("max-w-lg");
    }
    if (tabAuthRegister) tabAuthRegister.className = "flex-1 py-2 text-xs font-bold border-b-2 border-teal-500 text-teal-400 transition";
    if (tabAuthLogin) tabAuthLogin.className = "flex-1 py-2 text-xs font-bold border-b-2 border-transparent text-slate-400 hover:text-white transition";
    if (formRegister) formRegister.classList.remove("hidden");
    if (formAuth) formAuth.classList.add("hidden");
  } else {
    if (modalContainer) {
      modalContainer.classList.remove("max-w-lg");
      modalContainer.classList.add("max-w-sm");
    }
    if (tabAuthLogin) tabAuthLogin.className = "flex-1 py-2 text-xs font-bold border-b-2 border-teal-500 text-teal-400 transition";
    if (tabAuthRegister) tabAuthRegister.className = "flex-1 py-2 text-xs font-bold border-b-2 border-transparent text-slate-400 hover:text-white transition";
    if (formAuth) formAuth.classList.remove("hidden");
    if (formRegister) formRegister.classList.add("hidden");
  }
  authError.innerText = "";
  if (regStatus) regStatus.innerText = "";
  refreshIcons();
}

if (tabAuthLogin) tabAuthLogin.onclick = () => switchAuthTab("login");
if (tabAuthRegister) tabAuthRegister.onclick = () => switchAuthTab("register");

// Avatar File Preview on Register
const regAvatarInput = document.getElementById("reg-avatar-input");
const regAvatarPreviewImg = document.getElementById("reg-avatar-preview-img");
const regAvatarPlaceholder = document.getElementById("reg-avatar-placeholder");

if (regAvatarInput) {
  regAvatarInput.addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (regAvatarPreviewImg) {
          regAvatarPreviewImg.src = evt.target.result;
          regAvatarPreviewImg.classList.remove("hidden");
        }
        if (regAvatarPlaceholder) regAvatarPlaceholder.classList.add("hidden");
      };
      reader.readAsDataURL(file);
    }
  });
}

if (formRegister) {
  formRegister.onsubmit = async (e) => {
    e.preventDefault();
    const username = document.getElementById("reg-username").value.trim();
    const fullName = document.getElementById("reg-fullname") ? document.getElementById("reg-fullname").value.trim() : "";
    const email = document.getElementById("reg-email").value.trim();
    const phone = document.getElementById("reg-phone") ? document.getElementById("reg-phone").value.trim() : "";
    const dob = document.getElementById("reg-dob") ? document.getElementById("reg-dob").value.trim() : "";
    const address = document.getElementById("reg-address") ? document.getElementById("reg-address").value.trim() : "";
    const password = document.getElementById("reg-password").value.trim();
    const confirmPassword = document.getElementById("reg-password-confirm") ? document.getElementById("reg-password-confirm").value.trim() : "";
    const bio = document.getElementById("reg-bio") ? document.getElementById("reg-bio").value.trim() : "";

    if (confirmPassword && password !== confirmPassword) {
      regStatus.className = "text-xs text-rose-400 min-h-[1rem] text-center";
      regStatus.innerText = "Passwords do not match. Please verify.";
      return;
    }

    regStatus.innerText = "Provisioning operator account...";
    regStatus.className = "text-xs text-teal-400 min-h-[1rem] text-center";

    try {
      const fd = new FormData();
      fd.append("username", username);
      fd.append("password", password);
      if (fullName) fd.append("full_name", fullName);
      if (email) fd.append("email", email);
      if (phone) fd.append("phone", phone);
      if (dob) fd.append("dob", dob);
      if (address) fd.append("address", address);
      if (bio) fd.append("bio", bio);

      const avatarFile = regAvatarInput && regAvatarInput.files && regAvatarInput.files[0];
      if (avatarFile) {
        fd.append("avatar", avatarFile);
      }

      const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        body: fd
      });
      const data = await res.json();
      if (res.ok) {
        regStatus.className = "text-xs text-emerald-400 min-h-[1rem] text-center";
        regStatus.innerText = "Account commissioned! Redirecting to sign in...";
        document.getElementById("auth-username").value = username;
        document.getElementById("auth-password").value = password;
        setTimeout(() => {
          switchAuthTab("login");
        }, 1200);
      } else {
        regStatus.className = "text-xs text-rose-400 min-h-[1rem] text-center";
        regStatus.innerText = data.detail || "Registration failed.";
      }
    } catch (err) {
      regStatus.className = "text-xs text-rose-400 min-h-[1rem] text-center";
      regStatus.innerText = "Connection failed. Please check network.";
    }
  };
}

function checkAuth() {
  if (!state.token || !state.user) {
    showLanding();
  } else {
    authModal.classList.add("hidden");
    authModal.classList.remove("flex");
    updateUserProfile();
    loadDashboard();
    loadChatHistory();
    if (state.user.role === "admin") {
      navAdminTab.classList.remove("hidden");
    } else {
      navAdminTab.classList.add("hidden");
    }
  }
}

authForm.onsubmit = async (e) => {
  e.preventDefault();
  const uname = document.getElementById("auth-username").value.trim();
  const pwd = document.getElementById("auth-password").value.trim();
  authError.innerText = "";

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
      closeAuthModal();
      enterWorkspace();
      speakText(`Welcome back, ${data.username}. How can I support your day?`);
    } else {
      authError.innerText = data.detail || "Invalid credentials.";
    }
  } catch (err) {
    authError.innerText = "Neural Engine unreachable on port 8000.";
  }
};

function logoutUser() {
  localStorage.removeItem("aura_token");
  localStorage.removeItem("aura_user");
  state.token = null;
  state.user = null;
  showLanding();
}

document.getElementById("btn-logout").onclick = logoutUser;

function updateUserProfile() {
  if (!state.user) return;
  const uname = state.user.username || "Operator";
  const displayName = state.user.full_name || (uname.charAt(0).toUpperCase() + uname.slice(1));
  const roleText = (state.user.role || "Operator").toUpperCase();

  const userDisplayName = document.getElementById("user-display-name");
  if (userDisplayName) userDisplayName.innerText = displayName;

  const userDisplayRole = document.getElementById("user-display-role");
  if (userDisplayRole) userDisplayRole.innerText = roleText;

  // Sidebar Avatar
  const userAvatar = document.getElementById("user-avatar");
  if (userAvatar) {
    if (state.user.profile_pic) {
      userAvatar.innerHTML = `<img src="${state.user.profile_pic}" alt="Avatar" class="w-full h-full object-cover">`;
    } else {
      userAvatar.innerText = displayName.charAt(0).toUpperCase();
    }
  }

  // Header Avatar
  const headerAvatar = document.getElementById("header-avatar");
  if (headerAvatar) {
    if (state.user.profile_pic) {
      headerAvatar.innerHTML = `<img src="${state.user.profile_pic}" alt="Avatar" class="w-full h-full object-cover">`;
    } else {
      headerAvatar.innerText = displayName.charAt(0).toUpperCase();
    }
  }

  const homeGreeting = document.getElementById("home-greeting");
  if (homeGreeting) homeGreeting.innerText = `Good day, ${displayName}`;
}

// =============================================================================
// 2. NAVIGATION & ROUTING
// =============================================================================
const navTabs = document.querySelectorAll(".nav-tab");
const viewPanels = document.querySelectorAll(".view-panel");
const pageTitle = document.getElementById("page-title");

const titles = {
  home: "Home Dashboard",
  chat: "Conversations & Voice",
  goals: "Goals & Momentum",
  reminders: "Directives & Tasks",
  modules: "Domain Focus",
  artifacts: "Knowledge Vault",
  admin: "Security & Governance",
  profile: "Operator Dossier & Profile",
  about: "About AURA 2.0",
  faq: "Help & Frequently Asked Questions",
  contact: "Contact & Operations Support"
};

navTabs.forEach(tab => {
  tab.onclick = () => {
    const view = tab.getAttribute("data-view");
    switchView(view);
  };
});

function enterWorkspaceDirect() {
  if (landingScreen) landingScreen.classList.add("hidden");
  refreshIcons();
}

// Landing Footer Direct Links
const btnLandingNavAbout = document.getElementById("btn-landing-nav-about");
const btnLandingNavFaq = document.getElementById("btn-landing-nav-faq");
const btnLandingNavContact = document.getElementById("btn-landing-nav-contact");

if (btnLandingNavAbout) btnLandingNavAbout.onclick = () => { enterWorkspaceDirect(); switchView("about"); };
if (btnLandingNavFaq) btnLandingNavFaq.onclick = () => { enterWorkspaceDirect(); switchView("faq"); };
if (btnLandingNavContact) btnLandingNavContact.onclick = () => { enterWorkspaceDirect(); switchView("contact"); };

const viewHistory = [];

function switchView(viewName, pushHistory = true) {
  if (pushHistory && state.activeView && state.activeView !== viewName) {
    viewHistory.push(state.activeView);
    if (viewHistory.length > 25) viewHistory.shift();
  }

  state.activeView = viewName;
  navTabs.forEach(t => t.classList.toggle("active", t.getAttribute("data-view") === viewName));
  viewPanels.forEach(p => p.classList.toggle("hidden", p.id !== `view-${viewName}`));
  pageTitle.innerText = titles[viewName] || "AURA Dashboard";
  refreshIcons();

  if (viewName === "home" || viewName === "goals" || viewName === "reminders") {
    loadDashboard();
  } else if (viewName === "artifacts") {
    loadArtifacts();
  } else if (viewName === "admin") {
    loadAdminData();
  } else if (viewName === "profile") {
    loadUserProfileView();
  }
}

function navigateBack() {
  if (viewHistory.length > 0) {
    const prev = viewHistory.pop();
    switchView(prev, false);
  } else if (state.activeView !== "home") {
    switchView("home", false);
  } else {
    // If already on Home and history is empty, show Landing Screen
    const landing = document.getElementById("landing-screen");
    const appShell = document.getElementById("app-shell");
    if (landing && appShell) {
      appShell.classList.add("hidden");
      landing.classList.remove("hidden");
    }
  }
}

// Logo acts as Universal Backward Button
const btnLogoHome = document.getElementById("btn-logo-home");
if (btnLogoHome) {
  btnLogoHome.onclick = () => {
    navigateBack();
  };
}

const btnUniversalLogoBack = document.getElementById("btn-universal-logo-back");
if (btnUniversalLogoBack) {
  btnUniversalLogoBack.onclick = () => {
    navigateBack();
  };
}

// =============================================================================
// HOME JARVIS HERO: SEARCH OMNIBAR & VOICE ACTIVATION
// =============================================================================
function setHomeSearch(query) {
  const input = document.getElementById("home-search-input");
  if (input) {
    input.value = query;
    input.focus();
  }
}

function submitHomeSearch() {
  const input = document.getElementById("home-search-input");
  if (!input) return;
  const query = input.value.trim();
  if (!query) return;
  input.value = "";

  switchView("chat");
  const chatInput = document.getElementById("chat-input");
  if (chatInput) {
    chatInput.value = query;
    sendChatMessage();
  }
}

function toggleJarvisVoiceHome() {
  switchView("chat");
  speakText("AURA online. I am listening to your directive.");
  setTimeout(() => {
    if (typeof startListening === "function") {
      startListening();
    }
  }, 400);
}

// =============================================================================
// 3. HUMAN VOICE ENGINE & WEB AUDIO VISUALIZER (JARVIS EXPERIENCE)
// =============================================================================
let recognition = null;
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

const micBtn = document.getElementById("btn-mic-toggle");
const voiceWave = document.getElementById("voice-wave-container");
const voiceLiveText = document.getElementById("voice-live-text");
const btnCancelVoice = document.getElementById("btn-cancel-voice");
const aiStatusPill = document.getElementById("ai-status-pill");
const aiStatusText = document.getElementById("ai-status-text");

function setAiStatus(status, text) {
  aiStatusText.innerText = text;
  aiStatusPill.className = `flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition ${
    status === 'listening' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
    status === 'thinking' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
    status === 'speaking' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
    'bg-teal-500/10 text-teal-400 border-teal-500/20'
  }`;
}

// --- Web Audio API Visualizer for Arc Reactor & Chat Waves ---
let audioCtx = null;
let analyser = null;
let micStream = null;
let animFrameId = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) audioCtx = new AudioContextClass();
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
  return audioCtx;
}

function startAudioVisualizer(stream) {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.8;
    const source = ctx.createMediaStreamSource(stream);
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    const homeBars = document.querySelectorAll("#home-orb-soundwave span");
    const chatBars = document.querySelectorAll("#voice-wave-container .wave-bar");

    const updateBars = () => {
      if (!state.isListening && !state.isSpeaking) {
        homeBars.forEach(b => b.style.transform = "scaleY(1)");
        chatBars.forEach(b => b.style.transform = "scaleY(1)");
        return;
      }
      analyser.getByteFrequencyData(dataArray);

      homeBars.forEach((bar, idx) => {
        const val = dataArray[idx % dataArray.length] / 255;
        const barScale = Math.max(0.6, Math.min(3.2, 0.7 + val * 2.5));
        bar.style.transform = `scaleY(${barScale})`;
      });

      chatBars.forEach((bar, idx) => {
        const val = dataArray[idx % dataArray.length] / 255;
        const barScale = Math.max(0.5, Math.min(3.0, 0.6 + val * 2.4));
        bar.style.transform = `scaleY(${barScale})`;
      });

      animFrameId = requestAnimationFrame(updateBars);
    };
    if (animFrameId) cancelAnimationFrame(animFrameId);
    animFrameId = requestAnimationFrame(updateBars);
  } catch (e) {
    console.warn("Visualizer init notice:", e);
  }
}

let simulatedPulseInterval = null;
function startSimulatedSpeechPulse() {
  stopSimulatedSpeechPulse();
  const homeBars = document.querySelectorAll("#home-orb-soundwave span");
  const chatBars = document.querySelectorAll("#voice-wave-container .wave-bar");
  simulatedPulseInterval = setInterval(() => {
    if (!state.isSpeaking) {
      stopSimulatedSpeechPulse();
      return;
    }
    homeBars.forEach(b => {
      b.style.transform = `scaleY(${0.7 + Math.random() * 2.2})`;
    });
    chatBars.forEach(b => {
      b.style.transform = `scaleY(${0.6 + Math.random() * 2.0})`;
    });
  }, 110);
}

function stopSimulatedSpeechPulse() {
  if (simulatedPulseInterval) {
    clearInterval(simulatedPulseInterval);
    simulatedPulseInterval = null;
  }
  const homeBars = document.querySelectorAll("#home-orb-soundwave span");
  const chatBars = document.querySelectorAll("#voice-wave-container .wave-bar");
  homeBars.forEach(b => b.style.transform = "scaleY(1)");
  chatBars.forEach(b => b.style.transform = "scaleY(1)");
}

// --- Sentence-Boundary Low-Latency Speech Synthesis Engine ---
let speechQueue = [];
let isProcessingSpeechQueue = false;

function queueSpeechSentence(sentence) {
  if (!('speechSynthesis' in window)) return;
  const clean = sentence
    .replace(/[*#`_\[\]()]/g, "")
    .replace(/\(Engine:[^)]*\)/g, "")
    .replace(/https?:\/\/\S+/g, "")
    .trim();
  if (!clean) return;

  speechQueue.push(clean);
  if (!isProcessingSpeechQueue) {
    processNextSpeech();
  }
}

function processNextSpeech() {
  if (!speechQueue.length) {
    isProcessingSpeechQueue = false;
    state.isSpeaking = false;
    setAiStatus("ready", "AURA Ready");
    stopSimulatedSpeechPulse();
    return;
  }

  isProcessingSpeechQueue = true;
  state.isSpeaking = true;
  setAiStatus("speaking", "AURA Speaking...");
  startSimulatedSpeechPulse();

  const textToSpeak = speechQueue.shift();
  const utter = new SpeechSynthesisUtterance(textToSpeak);
  utter.pitch = 1.0;
  utter.rate = 1.05;

  const voices = window.speechSynthesis.getVoices();
  const naturalVoice = voices.find(v => (v.lang.includes("en-US") || v.lang.includes("en-GB")) && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha")));
  if (naturalVoice) utter.voice = naturalVoice;

  utter.onend = () => {
    processNextSpeech();
  };
  utter.onerror = () => {
    processNextSpeech();
  };

  window.speechSynthesis.speak(utter);
}

function stopAllSpeech() {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  speechQueue = [];
  isProcessingSpeechQueue = false;
  state.isSpeaking = false;
  stopSimulatedSpeechPulse();
}

function speakText(text) {
  stopListening();
  stopAllSpeech();
  queueSpeechSentence(text);
}

async function initSpeechRecognition() {
  if (!SpeechRec) {
    alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
    return false;
  }

  if (recognition) return true;

  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    state.isListening = true;
    voiceWave.classList.remove("hidden");
    voiceLiveText.innerText = "Listening to you... Speak naturally";
    micBtn.classList.add("bg-teal-500/30", "text-teal-300");
    setAiStatus("listening", "Listening...");
  };

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    if (transcript.trim()) {
      stopListening();
      sendUserMessage(transcript);
    }
  };

  recognition.onerror = (e) => {
    console.warn("Speech error:", e.error);
    if (e.error === "not-allowed") {
      alert("Microphone permission was blocked. Please click the lock/settings icon in your browser URL bar and allow Microphone access.");
    }
    stopListening();
  };

  recognition.onend = () => {
    stopListening();
  };

  return true;
}

async function startListening() {
  if (state.isSpeaking) stopAllSpeech();
  stopAllSpeech();

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micStream = stream;
    state.micPermissionGranted = true;
    startAudioVisualizer(stream);
  } catch (err) {
    alert("Microphone access is required for voice chat. Please allow microphone access in your browser.");
    stopListening();
    return;
  }

  const ok = await initSpeechRecognition();
  if (!ok) return;

  try {
    recognition.start();
  } catch (err) {
    console.log("Recognition start notice:", err);
  }
}

function stopListening() {
  state.isListening = false;
  voiceWave.classList.add("hidden");
  micBtn.classList.remove("bg-teal-500/30", "text-teal-300");
  if (micStream) {
    micStream.getTracks().forEach(t => t.stop());
    micStream = null;
  }
  if (!state.isSpeaking) {
    setAiStatus("ready", "AURA Ready");
    stopSimulatedSpeechPulse();
  }
  if (recognition) {
    try { recognition.abort(); } catch (err) {}
  }
}

micBtn.onclick = () => {
  if (state.isListening) stopListening();
  else startListening();
};

btnCancelVoice.onclick = stopListening;

// Hotkey: Tap Spacebar to speak (when not in an input box)
window.addEventListener("keydown", (e) => {
  if (e.code === "Space" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
    e.preventDefault();
    if (state.activeView !== "chat") switchView("chat");
    if (state.isListening) stopListening();
    else startListening();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    startNewChat();
  }
});

// =============================================================================
// 4. CONVERSATION STREAM & SENDING (REAL-TIME SSE & TOKEN RENDERING)
// =============================================================================
const chatMessagesContainer = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send-message");
const fileInput = document.getElementById("chat-file-input");
const fileLabel = document.getElementById("selected-file-label");

fileInput.onchange = (e) => {
  if (e.target.files.length) {
    state.selectedFile = e.target.files[0];
    fileLabel.innerText = `📎 ${state.selectedFile.name}`;
  } else {
    state.selectedFile = null;
    fileLabel.innerText = "";
  }
};

function renderMessage(role, text) {
  const isAura = role === "assistant" || role === "aura";
  const div = document.createElement("div");
  div.className = `chat-bubble flex gap-3.5 max-w-2xl ${isAura ? 'aura' : 'user self-end flex-row-reverse'}`;

  const avatar = isAura ? `
    <div class="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center shrink-0 mt-0.5">
      <i data-lucide="sparkles" class="w-3.5 h-3.5 text-teal-400"></i>
    </div>
  ` : `
    <div class="w-7 h-7 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-xs shrink-0 mt-0.5">
      ${(state.user?.username || 'U').charAt(0).toUpperCase()}
    </div>
  `;

  const formattedHtml = text.replace(/\n/g, "<br>");

  div.innerHTML = `
    ${avatar}
    <div class="bubble-content ${isAura ? 'bg-surface-100/90 border border-surface-border text-slate-200' : 'bg-gradient-to-tr from-teal-600 to-indigo-600 text-white'} rounded-2xl ${isAura ? 'rounded-tl-sm' : 'rounded-tr-sm'} p-4 text-sm leading-relaxed shadow-sm">
      ${formattedHtml}
    </div>
  `;

  chatMessagesContainer.appendChild(div);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  refreshIcons();
}

function createStreamingMessageBubble() {
  const div = document.createElement("div");
  div.className = "chat-bubble flex gap-3.5 max-w-2xl aura";
  div.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center shrink-0 mt-0.5">
      <i data-lucide="sparkles" class="w-3.5 h-3.5 text-teal-400"></i>
    </div>
    <div class="bubble-content bg-surface-100/90 border border-surface-border text-slate-200 rounded-2xl rounded-tl-sm p-4 text-sm leading-relaxed shadow-sm">
      <span class="stream-text"></span><span class="inline-block w-1.5 h-4 ml-0.5 bg-teal-400 animate-pulse cursor-indicator"></span>
    </div>
  `;
  chatMessagesContainer.appendChild(div);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  refreshIcons();

  const textEl = div.querySelector(".stream-text");
  const cursorEl = div.querySelector(".cursor-indicator");

  return {
    appendToken(token) {
      textEl.innerText += token;
      chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    },
    finalize(fullText) {
      if (cursorEl) cursorEl.remove();
      if (fullText) {
        textEl.innerHTML = fullText.replace(/\n/g, "<br>");
      }
      chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
      refreshIcons();
    }
  };
}

async function sendUserMessage(msgText) {
  const text = (msgText || chatInput.value).trim();
  if (!text && !state.selectedFile) return;

  chatInput.value = "";
  renderMessage("user", text || `Uploaded file: ${state.selectedFile.name}`);
  stopAllSpeech();

  setAiStatus("thinking", "Thinking...");

  try {
    if (state.selectedFile) {
      const formData = new FormData();
      formData.append("file", state.selectedFile);
      formData.append("prompt", text || "Analyze this file with human clarity.");

      const uploadRes = await fetchWithAuth(`${API_URL}/artifacts/upload`, {
        method: "POST",
        body: formData
      });
      const uploadData = await uploadRes.json();
      state.selectedFile = null;
      fileLabel.innerText = "";
      fileInput.value = "";

      const responseText = uploadData.analysis || "File ingested successfully.";
      renderMessage("aura", responseText);
      speakText(responseText);
      loadChatHistory();
    } else {
      // Real-Time SSE Token Stream
      const bubble = createStreamingMessageBubble();
      const res = await fetchWithAuth(`${API_URL}/chat/stream`, {
        method: "POST",
        body: JSON.stringify({
          message: text,
          session_id: state.sessionId
        })
      });

      if (!res.ok) {
        throw new Error(`Stream request failed: ${res.statusText}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let streamBuffer = "";
      let speechBuffer = "";
      let fullAccumulatedText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });
        const lines = streamBuffer.split("\n\n");
        streamBuffer = lines.pop() || "";

        for (const block of lines) {
          const trimmed = block.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.slice(5).trim();
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === "init") {
              if (data.session_id) {
                state.sessionId = data.session_id;
                localStorage.setItem("aura_session_id", state.sessionId);
              }
            } else if (data.type === "token") {
              const token = data.token;
              bubble.appendToken(token);
              fullAccumulatedText += token;
              speechBuffer += token;

              // Sentence-boundary low-latency audio synthesis
              const match = speechBuffer.match(/^([\s\S]+?[.!?\n]+)([\s\S]*)$/);
              if (match) {
                const sentence = match[1];
                speechBuffer = match[2];
                queueSpeechSentence(sentence);
              }
            } else if (data.type === "done") {
              if (data.session_id) {
                state.sessionId = data.session_id;
                localStorage.setItem("aura_session_id", state.sessionId);
              }
              if (data.full_response) {
                fullAccumulatedText = data.full_response;
              }
            }
          } catch (e) {
            console.warn("Parse stream chunk error:", e);
          }
        }
      }

      bubble.finalize(fullAccumulatedText);
      if (speechBuffer.trim()) {
        queueSpeechSentence(speechBuffer.trim());
      }
      loadChatHistory();
    }
  } catch (err) {
    console.error("sendUserMessage error:", err);
    renderMessage("aura", "Sorry, I had trouble connecting to the core engine just now.");
    setAiStatus("ready", "AURA Ready");
  }
}

btnSend.onclick = () => sendUserMessage();
chatInput.onkeydown = (e) => {
  if (e.key === "Enter") sendUserMessage();
};

function startNewChat() {
  state.sessionId = generateUUID();
  localStorage.setItem("aura_session_id", state.sessionId);
  chatMessagesContainer.innerHTML = `
    <div class="chat-bubble aura flex gap-3.5 max-w-2xl">
      <div class="w-7 h-7 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center shrink-0 mt-0.5">
        <i data-lucide="sparkles" class="w-3.5 h-3.5 text-teal-400"></i>
      </div>
      <div class="bubble-content bg-surface-100/90 border border-surface-border rounded-2xl rounded-tl-sm p-4 text-slate-200 text-sm leading-relaxed shadow-sm">
        New session active. I'm listening—what's on your mind?
      </div>
    </div>
  `;
  switchView("chat");
}

document.getElementById("btn-new-chat").onclick = startNewChat;

// =============================================================================
// 5. CHAT HISTORY SYNCHRONIZATION WITH 3-DOTS DELETE OPTIONS
// =============================================================================
async function loadChatHistory() {
  if (!state.token) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/chat/history`);
    if (res.ok) {
      const data = await res.json();
      const list = document.getElementById("sidebar-history-list");
      list.innerHTML = "";

      if (!data.history || !data.history.length) {
        list.innerHTML = `<span class="text-xs text-slate-500 px-3 py-1 italic">No recent chats yet.</span>`;
        return;
      }

      data.history.forEach(sess => {
        const item = document.createElement("div");
        item.className = "chat-session-item group flex items-center justify-between rounded-lg hover:bg-white/5 pr-1 transition";
        item.innerHTML = `
          <button class="flex-1 min-w-0 text-left px-2.5 py-1.5 text-xs text-slate-300 group-hover:text-white truncate flex items-center gap-2 cursor-pointer">
            <i data-lucide="message-square" class="w-3 h-3 text-slate-500 shrink-0"></i>
            <span class="truncate">${sess.preview}</span>
          </button>
          <button class="btn-chat-options p-1 rounded-md hover:bg-white/10 text-slate-500 hover:text-white transition opacity-60 group-hover:opacity-100 cursor-pointer" title="Chat options">
            <i data-lucide="more-vertical" class="w-3.5 h-3.5"></i>
          </button>
          <div class="chat-menu-dropdown hidden">
            <button class="btn-delete-session w-full text-left px-2.5 py-1.5 rounded-md hover:bg-rose-500/20 text-rose-400 text-xs font-semibold flex items-center gap-2 transition cursor-pointer">
              <i data-lucide="trash-2" class="w-3 h-3 text-rose-400"></i>
              <span>Delete Chat</span>
            </button>
          </div>
        `;

        // Click to load chat session
        item.querySelector("button:first-child").onclick = () => {
          loadSessionMessages(sess);
        };

        // 3-dots toggle
        const optionsBtn = item.querySelector(".btn-chat-options");
        const dropdown = item.querySelector(".chat-menu-dropdown");
        optionsBtn.onclick = (e) => {
          e.stopPropagation();
          document.querySelectorAll(".chat-menu-dropdown").forEach(d => {
            if (d !== dropdown) d.classList.add("hidden");
          });
          dropdown.classList.toggle("hidden");
          refreshIcons();
        };

        // Delete chat session
        const deleteBtn = item.querySelector(".btn-delete-session");
        deleteBtn.onclick = async (e) => {
          e.stopPropagation();
          dropdown.classList.add("hidden");
          await deleteChatSession(sess.session_id);
        };

        list.appendChild(item);
      });
      refreshIcons();
    }
  } catch (err) {}
}

// Global click dismisses chat dropdowns
document.addEventListener("click", () => {
  document.querySelectorAll(".chat-menu-dropdown").forEach(d => d.classList.add("hidden"));
});

async function deleteChatSession(sessionId) {
  if (!confirm("Are you sure you want to delete this chat session?")) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/chat/session/${sessionId}`, {
      method: "DELETE"
    });
    if (res.ok) {
      if (state.sessionId === sessionId) {
        startNewChat();
      }
      loadChatHistory();
    } else {
      alert("Failed to delete chat session.");
    }
  } catch (err) {
    console.error("Delete chat error:", err);
  }
}

function loadSessionMessages(sessionData) {
  state.sessionId = sessionData.session_id;
  localStorage.setItem("aura_session_id", state.sessionId);
  chatMessagesContainer.innerHTML = "";

  sessionData.messages.forEach(m => {
    renderMessage(m.role, m.content);
  });
  switchView("chat");
}

// =============================================================================
// 6. DASHBOARD & GOALS TELEMETRY
// =============================================================================
const goalsGrid = document.getElementById("goals-grid");
const homeGoalsContainer = document.getElementById("home-goals-container");
const homeTasksContainer = document.getElementById("home-tasks-container");

async function loadDashboard() {
  if (!state.token) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/dashboard/summary`);
    if (res.ok) {
      const data = await res.json();
      const goals = data.goals || [];
      const reminders = data.reminders || [];

      // Update Key Stat Badges
      const statGoals = document.getElementById("stat-goals-count");
      const statTasks = document.getElementById("stat-tasks-count");
      const statPeak = document.getElementById("stat-peak-streak");
      if (statGoals) statGoals.innerText = goals.length;
      if (statTasks) statTasks.innerText = reminders.length;
      if (statPeak) {
        const maxStreak = Math.max(0, ...goals.map(g => g.streak || 0));
        statPeak.innerText = `🔥 ${maxStreak}d`;
      }

      // Populate task goal dropdown
      const taskGoalSelect = document.getElementById("new-task-goal");
      if (taskGoalSelect) {
        const currentVal = taskGoalSelect.value;
        taskGoalSelect.innerHTML = `<option value="">General Directive</option>` + goals.map(g => `
          <option value="${g.id}">${g.intention}</option>
        `).join("");
        taskGoalSelect.value = currentVal;
      }

      renderGoals(goals);
      renderHomeGoals(goals);
      renderReminders(reminders);
      renderHomeTasks(reminders);
    }

    const fzRes = await fetchWithAuth(`${API_URL}/goals/freeze-status`);
    if (fzRes.ok) {
      const fz = await fzRes.json();
      const sCount = fz.freeze_tokens || 0;
      document.getElementById("shield-count").innerText = sCount;
      const statShield = document.getElementById("stat-shield-count");
      if (statShield) statShield.innerText = sCount;
    }
  } catch (err) {}
}

function renderHomeGoals(goals) {
  if (!homeGoalsContainer) return;
  if (!goals.length) {
    homeGoalsContainer.innerHTML = `<p class="text-xs text-slate-500 italic py-2 text-center">No active goals yet. Click "+ New Goal" to generate a plan.</p>`;
    return;
  }
  homeGoalsContainer.innerHTML = goals.slice(0, 3).map(g => {
    const prog = g.progress || 0;
    return `
      <div class="flex items-center justify-between p-3 rounded-xl bg-surface-200/60 border border-white/5 hover:border-white/10 transition">
        <div class="min-w-0 pr-3 flex-1">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-bold text-white truncate">${g.intention}</span>
            <span class="text-[10px] text-amber-400 font-bold shrink-0">🔥 ${g.streak}d</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="h-1.5 flex-1 bg-surface-100 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-500 rounded-full" style="width: ${prog}%"></div>
            </div>
            <span class="text-[10px] text-teal-300 font-bold shrink-0">${prog}%</span>
          </div>
        </div>
        <button onclick="switchView('reminders')" class="px-2.5 py-1 rounded-lg bg-teal-500/15 hover:bg-teal-500/25 text-teal-300 text-xs font-semibold shrink-0 transition">Tasks →</button>
      </div>
    `;
  }).join("");
}

function renderHomeTasks(reminders) {
  if (!homeTasksContainer) return;
  if (!reminders.length) {
    homeTasksContainer.innerHTML = `<p class="text-xs text-slate-500 italic py-2 text-center">Zero pending tasks. All cleared!</p>`;
    return;
  }
  homeTasksContainer.innerHTML = reminders.slice(0, 5).map(r => `
    <div class="flex items-center justify-between p-2 rounded-xl ${r.is_completed ? 'bg-surface-200/30 opacity-70' : 'bg-surface-200/50'} border border-white/5 text-xs text-slate-300 transition">
      <div class="flex items-center gap-2 min-w-0 flex-1 pr-2">
        <input 
          type="checkbox" 
          onchange="toggleReminder(${r.id})" 
          ${r.is_completed ? 'checked' : ''} 
          class="w-3.5 h-3.5 rounded text-teal-500 bg-surface-200 border-white/20 focus:ring-0 cursor-pointer shrink-0"
        >
        <span class="truncate ${r.is_completed ? 'line-through text-slate-500' : ''}">${r.task}</span>
      </div>
      <div class="flex items-center gap-1.5 shrink-0">
        <span class="text-[10px] text-teal-400 font-medium">[${r.due || 'Today'}]</span>
        <button onclick="deleteReminder(${r.id})" title="Delete Task" class="p-1 rounded hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition cursor-pointer">
          <i data-lucide="trash-2" class="w-3 h-3"></i>
        </button>
      </div>
    </div>
  `).join("");
  refreshIcons();
}

function formatGoalRoutine(routineText) {
  if (!routineText || typeof routineText !== 'string' || !routineText.trim()) {
    return '<div class="text-xs text-slate-400 italic py-2">Daily action plan is generating...</div>';
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatInline(str) {
    let escaped = escapeHtml(str);
    // Replace **bold**
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-medium">$1</strong>');
    // Replace *italic*
    escaped = escaped.replace(/\*(.+?)\*/g, '<em class="text-slate-200">$1</em>');
    // Replace `code`
    escaped = escaped.replace(/`(.+?)`/g, '<code class="bg-surface-300 text-teal-300 px-1 py-0.5 rounded text-[11px]">$1</code>');
    return escaped;
  }

  const rawLines = routineText.split(/\r?\n/);
  const sections = [];
  let currentSection = {
    title: "",
    type: "general",
    items: []
  };

  function getSectionType(title) {
    const lower = title.toLowerCase();
    if (lower.includes("summary") || lower.includes("overview") || lower.includes("intention")) return "summary";
    if (lower.includes("roadmap") || lower.includes("phase") || lower.includes("strategic") || lower.includes("timeline")) return "roadmap";
    if (lower.includes("daily") || lower.includes("action") || lower.includes("task") || lower.includes("routine") || lower.includes("habit")) return "daily";
    return "general";
  }

  for (let rawLine of rawLines) {
    const line = rawLine.trim();
    if (!line) continue;

    // Check if line is a primary heading: e.g. "### 📋 Goal Summary", "### 1. Goal Summary", "### Roadmap", "### Daily Tasks"
    const headingMatch = line.match(/^#{1,4}\s*(.*)$/) || line.match(/^(\*{2})?(Goal Summary|Strategic Roadmap|Daily Action Plan|Daily Tasks|Roadmap|Daily Routine)(\*{2})?:?$/i);

    if (headingMatch) {
      if (currentSection.items.length > 0 || currentSection.title) {
        sections.push(currentSection);
      }
      let rawTitle = headingMatch[1] ? headingMatch[1].trim() : headingMatch[2].trim();
      rawTitle = rawTitle.replace(/^\d+[\.\)]\s*/, '');
      currentSection = {
        title: rawTitle,
        type: getSectionType(rawTitle),
        items: []
      };
      continue;
    }

    // Check if line is a subphase heading (e.g. "Week 1 (Days 1‑7):" or "Phase 1 (Setup):")
    const subPhaseMatch = line.match(/^(\*{2})?(Phase|Week|Stage|Part|Month|Sprint|Day)\s+\d+.*?:(\*{2})?$/i);
    if (subPhaseMatch) {
      currentSection.items.push({
        type: "subheading",
        content: line.replace(/\*+/g, '').trim()
      });
      continue;
    }

    // Check if line is a bullet item: "- ...", "* ...", "• ...", "1. ..."
    const bulletMatch = line.match(/^([*\-•]|\d+[\.\)])\s+(.*)$/);
    if (bulletMatch) {
      let content = bulletMatch[2];
      if (!content.startsWith("**")) {
        const pm = content.match(/^((?:Phase|Week|Day|Stage|Step)\s+\d+[^:]*:\s*)(.*)$/i);
        if (pm) {
          content = `**${pm[1].trim()}** ${pm[2].trim()}`;
        }
      }
      currentSection.items.push({
        type: "bullet",
        prefix: bulletMatch[1],
        content: content
      });
      continue;
    }

    // Otherwise it's a regular text line
    currentSection.items.push({
      type: "text",
      content: line
    });
  }

  if (currentSection.items.length > 0 || currentSection.title) {
    sections.push(currentSection);
  }

  return sections.map((sec, idx) => {
    let headerHtml = "";
    if (sec.title) {
      let badgeCls = "text-teal-300 bg-teal-500/10 border-teal-500/20";
      let dotCls = "bg-teal-400";
      let icon = "📋";

      if (sec.type === "roadmap") {
        badgeCls = "text-indigo-300 bg-indigo-500/10 border-indigo-500/20";
        dotCls = "bg-indigo-400";
        icon = "🗺️";
      } else if (sec.type === "daily") {
        badgeCls = "text-amber-300 bg-amber-500/10 border-amber-500/20";
        dotCls = "bg-amber-400";
        icon = "✅";
      }

      const cleanTitle = sec.title.replace(/^[\p{Extended_Pictographic}\p{Emoji}\uFE0E\uFE0F\s]+/u, '').trim();
      const displayTitle = `${icon} ${cleanTitle || sec.title}`;

      headerHtml = `
        <div class="flex items-center gap-2 ${idx > 0 ? 'mt-4 pt-2.5 border-t border-white/5' : 'mt-0'} mb-2">
          <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md border ${badgeCls}">
            <span class="w-1.5 h-1.5 rounded-full ${dotCls}"></span>
            ${formatInline(displayTitle)}
          </span>
        </div>
      `;
    }

    const itemsHtml = sec.items.map(item => {
      if (item.type === "subheading") {
        return `
          <div class="text-[11px] font-bold text-indigo-300/90 mt-2.5 mb-1 flex items-center gap-1.5 pl-0.5">
            <span class="text-indigo-400 font-bold">▸</span>
            <span>${formatInline(item.content)}</span>
          </div>
        `;
      } else if (item.type === "bullet") {
        const isNum = /^\d+[\.\)]/.test(item.prefix);
        const bulletBadge = isNum
          ? `<span class="text-[10px] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5 shrink-0 mt-0.5 leading-none">${escapeHtml(item.prefix)}</span>`
          : `<span class="w-1.5 h-1.5 rounded-full ${sec.type === 'roadmap' ? 'bg-indigo-400/90' : sec.type === 'daily' ? 'bg-amber-400/90' : 'bg-teal-400/90'} mt-1.5 shrink-0"></span>`;

        return `
          <div class="flex items-start gap-2 text-xs text-slate-300 leading-relaxed py-0.5 pl-1">
            ${bulletBadge}
            <div class="flex-1 min-w-0">${formatInline(item.content)}</div>
          </div>
        `;
      } else {
        return `
          <p class="text-xs text-slate-300 leading-relaxed py-0.5 pl-1 ${sec.type === 'summary' ? 'italic text-slate-300/90' : ''}">
            ${formatInline(item.content)}
          </p>
        `;
      }
    }).join("");

    return `
      <div class="goal-section-group">
        ${headerHtml}
        <div class="space-y-1">
          ${itemsHtml}
        </div>
      </div>
    `;
  }).join("");
}

function renderGoals(goals) {
  if (!goalsGrid) return;
  if (!goals.length) {
    goalsGrid.innerHTML = `
      <div class="p-12 text-center text-slate-400 text-sm col-span-2 border border-dashed border-white/10 rounded-2xl bg-surface-100/30">
        <i data-lucide="target" class="w-8 h-8 text-slate-500 mx-auto mb-2"></i>
        <p class="font-medium text-white mb-1">No active goals defined yet</p>
        <p class="text-xs text-slate-500 mb-4">Set your intention and AURA will craft an automated roadmap and daily routine.</p>
        <button onclick="openGoalModal()" class="px-4 py-2 rounded-xl bg-teal-500 hover:bg-teal-400 text-surface-200 font-semibold text-xs transition">Create Your First Goal</button>
      </div>
    `;
    refreshIcons();
    return;
  }

  goalsGrid.innerHTML = goals.map(g => {
    const prog = g.progress || 0;
    return `
      <div class="bg-surface-100 border border-surface-border rounded-2xl p-5 flex flex-col justify-between hover:border-white/15 transition shadow-sm">
        <div>
          <div class="flex items-start justify-between gap-3 mb-3">
            <div>
              <span class="text-[10px] font-bold uppercase tracking-wider text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/20">${g.timeline || 'Goal'}</span>
              <h3 class="font-bold text-white text-base mt-1.5 leading-snug">${g.intention}</h3>
            </div>
            <span class="flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
              🔥 ${g.streak}d
            </span>
          </div>

          <div class="mb-4">
            <div class="flex items-center justify-between text-xs mb-1.5">
              <span class="text-slate-400">Automated Trajectory</span>
              <span class="font-bold text-teal-300">${prog}%</span>
            </div>
            <div class="h-2 w-full bg-surface-200 rounded-full overflow-hidden border border-white/5">
              <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-500 rounded-full transition-all duration-500 shadow-sm" style="width: ${prog}%"></div>
            </div>
          </div>

          <div class="bg-surface-200/60 p-3.5 rounded-xl border border-white/5 mb-4 max-h-64 overflow-y-auto space-y-2">
            ${formatGoalRoutine(g.daily_routine)}
          </div>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-surface-border">
          <button onclick="checkinGoal(${g.id})" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-500/15 hover:bg-teal-500/25 border border-teal-500/30 text-teal-300 text-xs font-semibold transition">
            <i data-lucide="check" class="w-3.5 h-3.5"></i>
            <span>Check-in Today</span>
          </button>
          <button onclick="deleteGoal(${g.id})" title="Delete Goal" class="p-1.5 rounded-lg hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  }).join("");

  refreshIcons();
}

async function checkinGoal(goalId) {
  try {
    const res = await fetchWithAuth(`${API_URL}/goals/${goalId}/checkin`, {
      method: "POST"
    });
    if (res.ok) {
      loadDashboard();
      speakText("Momentum recorded. Your progress has been updated!");
    }
  } catch (err) {}
}

async function deleteGoal(goalId) {
  if (!confirm("Are you sure you want to delete this goal?")) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/goals/${goalId}`, {
      method: "DELETE"
    });
    if (res.ok) {
      loadDashboard();
    }
  } catch (err) {}
}

// Modal Goal Handlers
const goalModal = document.getElementById("modal-goal");
const formNewGoal = document.getElementById("form-new-goal");
const btnSubmitGoal = document.getElementById("btn-submit-goal");

function openGoalModal() {
  goalModal.classList.remove("hidden");
  goalModal.classList.add("flex");
}

function closeGoalModal() {
  goalModal.classList.add("hidden");
  goalModal.classList.remove("flex");
}

const btnOpenGoalModal = document.getElementById("btn-open-goal-modal");
if (btnOpenGoalModal) btnOpenGoalModal.onclick = openGoalModal;

formNewGoal.onsubmit = async (e) => {
  e.preventDefault();
  const intent = document.getElementById("goal-intent").value.trim();
  const cat = document.getElementById("goal-cat").value;
  const dur = document.getElementById("goal-dur").value;
  const exp = document.getElementById("goal-exp").value;

  btnSubmitGoal.disabled = true;
  btnSubmitGoal.innerHTML = `<span class="inline-block animate-spin mr-1.5">⚙️</span> Dispatching Goal Blueprint...`;

  try {
    const res = await fetchWithAuth(`${API_URL}/goals`, {
      method: "POST",
      body: JSON.stringify({
        intention: intent,
        category: cat,
        duration: dur,
        experience: exp
      })
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.job_id) {
        btnSubmitGoal.innerHTML = `<span class="inline-block animate-pulse mr-1.5">🧠</span> Synthesizing Roadmap in Background...`;
        
        let attempts = 0;
        const maxAttempts = 35;
        const pollJob = async () => {
          try {
            const pollRes = await fetchWithAuth(`${API_URL}/goals/jobs/${data.job_id}`);
            if (pollRes.ok) {
              const pollData = await pollRes.json();
              if (pollData.status === "ready") {
                closeGoalModal();
                formNewGoal.reset();
                loadDashboard();
                speakText("New goal established. Your strategic roadmap and daily tasks are ready!");
                btnSubmitGoal.disabled = false;
                btnSubmitGoal.innerText = "Generate AI Roadmap ➔";
                return;
              } else if (pollData.status === "failed") {
                closeGoalModal();
                formNewGoal.reset();
                loadDashboard();
                speakText("Goal registered with fallback milestones.");
                btnSubmitGoal.disabled = false;
                btnSubmitGoal.innerText = "Generate AI Roadmap ➔";
                return;
              }
            }
          } catch (pollErr) {
            console.warn("Polling error:", pollErr);
          }

          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(pollJob, 1200);
          } else {
            closeGoalModal();
            formNewGoal.reset();
            loadDashboard();
            btnSubmitGoal.disabled = false;
            btnSubmitGoal.innerText = "Generate AI Roadmap ➔";
          }
        };

        setTimeout(pollJob, 1000);
        return;
      } else {
        closeGoalModal();
        formNewGoal.reset();
        loadDashboard();
        speakText(`New goal established.`);
      }
    } else {
      alert("Failed to initialize goal. Please check input parameters.");
    }
  } catch (err) {
    console.error("Goal submission error:", err);
    alert("Connection error while creating goal.");
  } finally {
    if (!btnSubmitGoal.disabled) {
      btnSubmitGoal.innerText = "Generate AI Roadmap ➔";
    }
  }
};

// =============================================================================
// 7. REMINDERS & DIRECTIVES
// =============================================================================
const remindersList = document.getElementById("reminders-list");
const newTaskInput = document.getElementById("new-task-input");
const newTaskGoal = document.getElementById("new-task-goal");
const formAddTask = document.getElementById("form-add-task");
const btnAddTask = document.getElementById("btn-add-task");

function renderReminders(reminders) {
  if (!remindersList) return;
  if (!reminders.length) {
    remindersList.innerHTML = `
      <div class="p-8 text-center text-slate-500 text-sm border border-dashed border-white/10 rounded-2xl">
        Zero pending directives. You are completely caught up!
      </div>
    `;
    return;
  }

  remindersList.innerHTML = reminders.map(r => `
    <div class="flex items-center justify-between p-3.5 rounded-xl ${r.is_completed ? 'bg-surface-100/40 opacity-70 border-white/5' : 'bg-surface-100 border-surface-border'} border hover:border-white/15 transition group">
      <div class="flex items-center gap-3 min-w-0 flex-1 pr-3">
        <input 
          type="checkbox" 
          onchange="toggleReminder(${r.id})" 
          ${r.is_completed ? 'checked' : ''} 
          class="w-4 h-4 rounded text-teal-500 bg-surface-200 border-white/20 focus:ring-0 cursor-pointer shrink-0"
        >
        <span class="text-sm font-medium ${r.is_completed ? 'line-through text-slate-500' : 'text-slate-200'} truncate">${r.task}</span>
        ${r.goal_title ? `
          <span class="text-[10px] font-semibold text-teal-300 bg-teal-500/10 border border-teal-500/20 px-2 py-0.5 rounded-md truncate max-w-[140px] shrink-0">
            🎯 ${r.goal_title}
          </span>
        ` : ''}
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-400">${r.due || 'Today'}</span>
        <button onclick="deleteReminder(${r.id})" title="Delete Directive" class="p-1.5 rounded-lg hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition cursor-pointer">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
        </button>
      </div>
    </div>
  `).join("");
  refreshIcons();
}

async function addNewTask() {
  const input = document.getElementById("new-task-input");
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;
  
  const goalSelect = document.getElementById("new-task-goal");
  const goalId = goalSelect && goalSelect.value ? parseInt(goalSelect.value) : null;
  
  input.value = "";
  try {
    const res = await fetchWithAuth(`${API_URL}/reminders`, {
      method: "POST",
      body: JSON.stringify({
        task_text: text,
        priority: "High",
        due_info: "Today",
        goal_id: goalId
      })
    });
    if (res.ok) {
      loadDashboard();
      speakText("Directive recorded.");
    }
  } catch (err) {}
}

async function toggleReminder(reminderId) {
  try {
    const res = await fetchWithAuth(`${API_URL}/reminders/${reminderId}/toggle`, {
      method: "POST"
    });
    if (res.ok) {
      const data = await res.json();
      if (data.streak_updated) {
        speakText("Outstanding execution! Daily task completed and momentum streak recorded.");
      }
      loadDashboard();
    }
  } catch (err) {}
}

async function deleteReminder(reminderId) {
  if (!confirm("Are you sure you want to delete this directive?")) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/reminders/${reminderId}`, {
      method: "DELETE"
    });
    if (res.ok) {
      loadDashboard();
    }
  } catch (err) {}
}

if (formAddTask) {
  formAddTask.onsubmit = (e) => {
    e.preventDefault();
    addNewTask();
  };
} else if (btnAddTask) {
  btnAddTask.onclick = () => {
    addNewTask();
  };
}

if (newTaskInput) {
  newTaskInput.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      addNewTask();
    }
  };
}

// =============================================================================
// 8. DOMAIN MODULES & HOME QUICK LAUNCHERS
// =============================================================================
const modulesData = [
  { name: "Career & Leadership", icon: "briefcase", color: "text-blue-400", prompt: "Evaluate my career growth strategy and help me prepare for upcoming milestones." },
  { name: "Full-Stack Engineering", icon: "code", color: "text-emerald-400", prompt: "Review my architecture design and help me optimize system performance." },
  { name: "Cybersecurity & Defenses", icon: "shield-alert", color: "text-rose-400", prompt: "Audit my operational security posture and identify threat vectors." },
  { name: "Financial Mastery", icon: "coins", color: "text-amber-400", prompt: "Help me review my financial goals, runway, and investment allocation." },
  { name: "Vitality & Health", icon: "heart-pulse", color: "text-pink-400", prompt: "Design an optimized daily energy, nutrition, and workout routine." },
  { name: "Peak Productivity", icon: "zap", color: "text-purple-400", prompt: "Audit my daily schedule to eliminate friction and maximize deep work." },
];

const modulesContainer = document.getElementById("modules-cards-container");
if (modulesContainer) {
  modulesContainer.innerHTML = modulesData.map(m => `
    <div class="bg-surface-100 border border-surface-border rounded-2xl p-5 hover:border-teal-500/40 transition flex flex-col justify-between">
      <div>
        <div class="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center mb-3 ${m.color}">
          <i data-lucide="${m.icon}" class="w-4 h-4"></i>
        </div>
        <h3 class="font-bold text-white text-base mb-1">${m.name}</h3>
        <p class="text-xs text-slate-400 mb-4 leading-relaxed">${m.prompt}</p>
      </div>
      <button onclick="injectPrompt('${m.prompt}')" class="w-full py-2 rounded-xl bg-white/5 hover:bg-teal-500/20 text-teal-300 text-xs font-semibold transition border border-white/5 hover:border-teal-500/30">
        Initiate Session ➔
      </button>
    </div>
  `).join("");
}

const homeModulesGrid = document.getElementById("home-modules-grid");
if (homeModulesGrid) {
  homeModulesGrid.innerHTML = modulesData.map(m => `
    <button onclick="injectPrompt('${m.prompt}')" class="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-200/60 hover:bg-teal-500/10 border border-white/5 hover:border-teal-500/30 transition text-center group">
      <div class="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center mb-1.5 ${m.color} group-hover:scale-110 transition">
        <i data-lucide="${m.icon}" class="w-3.5 h-3.5"></i>
      </div>
      <span class="text-[11px] font-semibold text-slate-200 group-hover:text-teal-300 transition truncate w-full">${m.name.split(' ')[0]}</span>
    </button>
  `).join("");
}

function injectPrompt(text) {
  switchView("chat");
  chatInput.value = text;
  sendUserMessage();
}

// =============================================================================
// 9. KNOWLEDGE VAULT
// =============================================================================
const vaultList = document.getElementById("vault-artifacts-list");
const vaultFileInput = document.getElementById("vault-file-input");

async function loadArtifacts() {
  if (!state.token) return;
  try {
    const res = await fetchWithAuth(`${API_URL}/artifacts`);
    if (res.ok) {
      const data = await res.json();
      if (!data.artifacts || !data.artifacts.length) {
        vaultList.innerHTML = `<p class="text-xs text-slate-500 italic">No artifacts uploaded yet.</p>`;
        return;
      }
      vaultList.innerHTML = data.artifacts.map(a => `
        <div class="flex items-center justify-between p-3.5 rounded-xl bg-surface-100 border border-surface-border">
          <div class="flex items-center gap-3">
            <i data-lucide="file-text" class="w-4 h-4 text-teal-400"></i>
            <div>
              <p class="text-xs font-bold text-white">${a.filename}</p>
              <p class="text-[10px] text-slate-400">${a.size_kb} KB</p>
            </div>
          </div>
          <button onclick="injectPrompt('Analyze artifact: ${a.filename}')" class="text-xs font-semibold px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-teal-300 transition">Analyze</button>
        </div>
      `).join("");
      refreshIcons();
    }
  } catch (err) {}
}

if (vaultFileInput) {
  vaultFileInput.onchange = async (e) => {
    if (!e.target.files.length) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("prompt", "Analyze and summarize this artifact.");

    try {
      await fetchWithAuth(`${API_URL}/artifacts/upload`, {
        method: "POST",
        body: formData
      });
      loadArtifacts();
      speakText(`Artifact ${file.name} uploaded and indexed.`);
    } catch (err) {}
  };
}

// Audio Briefing Player
document.getElementById("btn-play-briefing").onclick = async () => {
  try {
    const res = await fetchWithAuth(`${API_URL}/briefing/listen`);
    if (res.ok) {
      const blob = await res.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audio.play();
    }
  } catch (err) {}
};

// =============================================================================
// 10. ADMIN GOVERNANCE DESK (ADMIN ONLY)
// =============================================================================
const adminPendingList = document.getElementById("admin-pending-list");
const adminUsersTable = document.getElementById("admin-users-table");
const adminAppealsList = document.getElementById("admin-appeals-list");

async function loadAdminData() {
  if (!state.token || state.user?.role !== "admin") return;

  // 1. Load All Users
  try {
    const res = await fetchWithAuth(`${API_URL}/admin/users`);
    if (res.ok) {
      const data = await res.json();
      renderAdminUsers(data.users || []);
    }
  } catch (err) {}

  // 2. Load Pending Operators
  try {
    const pRes = await fetchWithAuth(`${API_URL}/admin/pending-operators`);
    if (pRes.ok) {
      const pData = await pRes.json();
      renderAdminPending(pData.pending_operators || []);
    }
  } catch (err) {}

  // 3. Load Appeals
  try {
    const aRes = await fetchWithAuth(`${API_URL}/admin/appeals`);
    if (aRes.ok) {
      const aData = await aRes.json();
      renderAdminAppeals(aData.appeals || []);
    }
  } catch (err) {}
}

function renderAdminUsers(users) {
  if (!adminUsersTable) return;
  adminUsersTable.innerHTML = users.map(u => {
    const isBanned = u.status === "banned";
    return `
      <tr class="hover:bg-white/5 transition">
        <td class="py-2.5 font-medium text-white flex items-center gap-2">
          <div class="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center font-bold text-[10px]">${u.username.charAt(0).toUpperCase()}</div>
          <span>${u.username}</span>
        </td>
        <td class="py-2.5 text-slate-300 font-mono text-[11px]">${u.role}</td>
        <td class="py-2.5">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
            u.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
            u.status === 'banned' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
            'bg-amber-500/10 text-amber-400 border border-amber-500/20'
          }">${u.status.toUpperCase()}</span>
        </td>
        <td class="py-2.5 text-slate-300">${u.freeze_tokens || 0}</td>
        <td class="py-2.5 text-right">
          ${u.role !== 'admin' ? `
            ${isBanned ? `
              <button onclick="changeOperatorStatus(${u.id}, 'unban')" class="px-2 py-1 rounded bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 text-[10px] font-bold transition">Unban</button>
            ` : `
              <button onclick="changeOperatorStatus(${u.id}, 'ban')" class="px-2 py-1 rounded bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 text-[10px] font-bold transition">Ban</button>
            `}
          ` : `<span class="text-slate-500 text-[10px] italic">Admin</span>`}
        </td>
      </tr>
    `;
  }).join("");
}

function renderAdminPending(pending) {
  if (!adminPendingList) return;
  if (!pending.length) {
    adminPendingList.innerHTML = `<p class="text-xs text-slate-500 italic py-2">No pending operator requests.</p>`;
    return;
  }
  adminPendingList.innerHTML = pending.map(p => `
    <div class="flex items-center justify-between p-3 rounded-xl bg-surface-200/60 border border-white/5">
      <div>
        <p class="text-xs font-bold text-white">${p.username} <span class="text-slate-400 font-normal">(${p.email || 'No email'})</span></p>
        <p class="text-[10px] text-slate-400 italic">${p.bio || 'Standard operator request'}</p>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="changeOperatorStatus(${p.id}, 'approve')" class="px-2.5 py-1 rounded-lg bg-teal-500 hover:bg-teal-400 text-surface-200 text-xs font-bold transition">Approve</button>
        <button onclick="changeOperatorStatus(${p.id}, 'reject')" class="px-2.5 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 text-xs font-bold transition">Reject</button>
      </div>
    </div>
  `).join("");
}

function renderAdminAppeals(appeals) {
  if (!adminAppealsList) return;
  if (!appeals.length) {
    adminAppealsList.innerHTML = `<p class="text-xs text-slate-500 italic py-2">No active appeals pending review.</p>`;
    return;
  }
  adminAppealsList.innerHTML = appeals.map(a => `
    <div class="p-3.5 rounded-xl bg-surface-200/60 border border-white/5">
      <div class="flex items-center justify-between mb-1">
        <span class="text-xs font-bold text-white">${a.username} <span class="text-slate-400">(${a.type})</span></span>
        <span class="text-[10px] text-slate-500">${new Date(a.date).toLocaleDateString()}</span>
      </div>
      <p class="text-xs text-slate-300 leading-relaxed mb-3 bg-surface-100 p-2.5 rounded-lg border border-white/5">${a.message}</p>
      <div class="flex items-center gap-2">
        <button onclick="changeOperatorStatus(${a.user_id}, 'unban')" class="px-3 py-1 rounded-lg bg-teal-500 hover:bg-teal-400 text-surface-200 text-xs font-bold transition">Approve & Unban</button>
        <button onclick="alert('Appeal dismissed.')" class="px-3 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 text-xs font-semibold transition">Dismiss</button>
      </div>
    </div>
  `).join("");
}

async function changeOperatorStatus(userId, action) {
  let reason = null;
  if (action === "ban") {
    reason = prompt("Provide reason for banning this operator:", "Security policy infraction");
    if (!reason) return;
  }
  try {
    const res = await fetch(`${API_URL}/admin/operators/${userId}/status`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ action: action, reason: reason })
    });
    if (res.ok) {
      loadAdminData();
    }
  } catch (err) {}
}

// =============================================================================
// 11. FAQ ACCORDION & CONTACT US HANDLERS
// =============================================================================
// FAQ Accordion Toggles
document.querySelectorAll(".faq-toggle").forEach(btn => {
  btn.onclick = () => {
    const content = btn.nextElementSibling;
    const chevron = btn.querySelector(".faq-chevron");
    const isHidden = content.classList.contains("hidden");
    content.classList.toggle("hidden", !isHidden);
    if (chevron) chevron.classList.toggle("rotate-180", isHidden);
  };
});

// FAQ Search Filtering
const faqSearchInput = document.getElementById("faq-search-input");
if (faqSearchInput) {
  faqSearchInput.oninput = (e) => {
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll(".faq-item").forEach(item => {
      const text = item.innerText.toLowerCase();
      item.style.display = text.includes(q) ? "block" : "none";
    });
  };
}

// Contact Us Form Submission
const formContactUs = document.getElementById("form-contact-us");
const contactStatus = document.getElementById("contact-status-msg");
if (formContactUs) {
  formContactUs.onsubmit = (e) => {
    e.preventDefault();
    contactStatus.className = "text-xs text-emerald-400 text-center min-h-[1.2rem] font-medium";
    contactStatus.innerText = "✓ Message successfully dispatched to AURA Operations desk. We will reach back shortly!";
    formContactUs.reset();
    setTimeout(() => {
      contactStatus.innerText = "";
    }, 4500);
  };
}

// =============================================================================
// 12. OPERATOR DOSSIER & PROFILE CONTROLLER
// =============================================================================
async function loadUserProfileView() {
  if (!state.token) return;

  try {
    const res = await fetchWithAuth(`${API_URL}/user/profile`);
    if (!res.ok) {
      return;
    }
    const data = await res.json();
    
    // Synchronize local state with latest user details
    state.user = { ...state.user, ...data };
    localStorage.setItem("aura_user", JSON.stringify(state.user));
    updateUserProfile();

    // Dossier Hero Elements
    const heroFullName = document.getElementById("profile-hero-fullname");
    if (heroFullName) heroFullName.innerText = data.full_name || data.username;

    const heroUsername = document.getElementById("profile-hero-username");
    if (heroUsername) heroUsername.innerText = data.username;

    const heroRoleBadge = document.getElementById("profile-hero-role-badge");
    if (heroRoleBadge) heroRoleBadge.innerText = (data.role || "OPERATOR").toUpperCase();

    const heroEmail = document.getElementById("profile-hero-email");
    if (heroEmail) heroEmail.innerText = data.email || "Email not specified";

    const heroPhone = document.getElementById("profile-hero-phone");
    if (heroPhone) heroPhone.innerText = data.phone || "Phone not specified";

    const heroDob = document.getElementById("profile-hero-dob");
    if (heroDob) heroDob.innerText = data.dob || "DOB not set";

    const heroAddress = document.getElementById("profile-hero-address");
    if (heroAddress) heroAddress.innerText = data.address || "Station / Address not specified";

    const heroBio = document.getElementById("profile-hero-bio");
    if (heroBio) {
      heroBio.innerText = data.bio ? `"${data.bio}"` : '"Autonomous operations practitioner leveraging real-time neural workflows."';
    }

    // Avatar Image in Dossier
    const avatarImg = document.getElementById("profile-avatar-img");
    const avatarFallback = document.getElementById("profile-avatar-fallback");
    if (data.profile_pic) {
      if (avatarImg) {
        avatarImg.src = data.profile_pic;
        avatarImg.classList.remove("hidden");
      }
      if (avatarFallback) avatarFallback.classList.add("hidden");
    } else {
      if (avatarImg) avatarImg.classList.add("hidden");
      if (avatarFallback) {
        avatarFallback.classList.remove("hidden");
        avatarFallback.innerText = (data.full_name || data.username || "U").charAt(0).toUpperCase();
      }
    }

    // Telemetry Stats
    const stats = data.stats || {};
    const statGoals = document.getElementById("profile-stat-goals");
    if (statGoals) statGoals.innerText = stats.active_goals || 0;

    const statDone = document.getElementById("profile-stat-completed");
    if (statDone) statDone.innerText = stats.completed_tasks || 0;

    const statPending = document.getElementById("profile-stat-pending");
    if (statPending) statPending.innerText = stats.pending_tasks || 0;

    const statStreak = document.getElementById("profile-stat-streak");
    if (statStreak) statStreak.innerText = `${stats.peak_streak || 0} Days`;

    const statShields = document.getElementById("profile-stat-shields");
    if (statShields) statShields.innerText = data.freeze_tokens ?? 0;

    // Form Edit Fields
    const inFullname = document.getElementById("prof-input-fullname");
    if (inFullname) inFullname.value = data.full_name || "";

    const inUsername = document.getElementById("prof-input-username");
    if (inUsername) inUsername.value = `@${data.username}`;

    const inEmail = document.getElementById("prof-input-email");
    if (inEmail) inEmail.value = data.email || "";

    const inPhone = document.getElementById("prof-input-phone");
    if (inPhone) inPhone.value = data.phone || "";

    const inDob = document.getElementById("prof-input-dob");
    if (inDob) inDob.value = data.dob || "";

    const inAvatarUrl = document.getElementById("prof-input-avatar-url");
    if (inAvatarUrl) inAvatarUrl.value = data.profile_pic || "";

    const inAddress = document.getElementById("prof-input-address");
    if (inAddress) inAddress.value = data.address || "";

    const inBio = document.getElementById("prof-input-bio");
    if (inBio) inBio.value = data.bio || "";

    // Diagnostics Card
    const metaId = document.getElementById("profile-meta-id");
    if (metaId) metaId.innerText = `#${data.id}`;

    const metaCreated = document.getElementById("profile-meta-created");
    if (metaCreated) {
      metaCreated.innerText = data.created_at ? new Date(data.created_at).toLocaleDateString() : "--";
    }

    const metaRole = document.getElementById("profile-meta-role");
    if (metaRole) metaRole.innerText = (data.role || "OPERATOR").toUpperCase();

    refreshIcons();
  } catch (err) {
    console.error("Failed to load user profile view:", err);
  }
}

// Profile Details Form Submission
const formProfileDetails = document.getElementById("form-profile-details");
const profSaveStatus = document.getElementById("prof-save-status");

if (formProfileDetails) {
  formProfileDetails.onsubmit = async (e) => {
    e.preventDefault();
    if (!state.token) return;

    const payload = {
      full_name: document.getElementById("prof-input-fullname").value.trim(),
      email: document.getElementById("prof-input-email").value.trim(),
      phone: document.getElementById("prof-input-phone").value.trim(),
      dob: document.getElementById("prof-input-dob").value.trim(),
      address: document.getElementById("prof-input-address").value.trim(),
      bio: document.getElementById("prof-input-bio").value.trim(),
      profile_pic: document.getElementById("prof-input-avatar-url").value.trim()
    };

    profSaveStatus.innerText = "Synchronizing profile modifications...";
    profSaveStatus.className = "text-xs text-teal-400";

    try {
      const res = await fetchWithAuth(`${API_URL}/user/profile`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        profSaveStatus.className = "text-xs text-emerald-400";
        profSaveStatus.innerText = "Profile credentials synchronized successfully.";
        state.user = { ...state.user, ...data.user };
        localStorage.setItem("aura_user", JSON.stringify(state.user));
        updateUserProfile();
        loadUserProfileView();
        setTimeout(() => { profSaveStatus.innerText = ""; }, 3000);
      } else {
        profSaveStatus.className = "text-xs text-rose-400";
        profSaveStatus.innerText = data.detail || "Failed to update profile.";
      }
    } catch (err) {
      profSaveStatus.className = "text-xs text-rose-400";
      profSaveStatus.innerText = "Network failure updating profile.";
    }
  };
}

// Password Change Form Submission
const formChangePassword = document.getElementById("form-change-password");
const pwdStatusMsg = document.getElementById("pwd-status-msg");

if (formChangePassword) {
  formChangePassword.onsubmit = async (e) => {
    e.preventDefault();
    if (!state.token) return;

    const currentPassword = document.getElementById("pwd-current").value.trim();
    const newPassword = document.getElementById("pwd-new").value.trim();
    const confirmPassword = document.getElementById("pwd-confirm").value.trim();

    if (newPassword !== confirmPassword) {
      pwdStatusMsg.className = "text-xs text-rose-400 text-center";
      pwdStatusMsg.innerText = "New passwords do not match.";
      return;
    }

    pwdStatusMsg.className = "text-xs text-teal-400 text-center";
    pwdStatusMsg.innerText = "Updating password cipher...";

    try {
      const res = await fetchWithAuth(`${API_URL}/user/profile`, {
        method: "PUT",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });
      const data = await res.json();
      if (res.ok) {
        pwdStatusMsg.className = "text-xs text-emerald-400 text-center";
        pwdStatusMsg.innerText = "Password updated securely.";
        document.getElementById("pwd-current").value = "";
        document.getElementById("pwd-new").value = "";
        document.getElementById("pwd-confirm").value = "";
        setTimeout(() => { pwdStatusMsg.innerText = ""; }, 3000);
      } else {
        pwdStatusMsg.className = "text-xs text-rose-400 text-center";
        pwdStatusMsg.innerText = data.detail || "Password update failed.";
      }
    } catch (err) {
      pwdStatusMsg.className = "text-xs text-rose-400 text-center";
      pwdStatusMsg.innerText = "Network failure updating password.";
    }
  };
}

// Profile Photo Direct Upload via Camera Button
const profilePhotoFileInput = document.getElementById("profile-photo-file-input");
if (profilePhotoFileInput) {
  profilePhotoFileInput.addEventListener("change", async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file || !state.token) return;

    const fd = new FormData();
    fd.append("photo", file);

    const profSaveStatus = document.getElementById("prof-save-status");
    if (profSaveStatus) {
      profSaveStatus.innerText = "Uploading avatar photo...";
      profSaveStatus.className = "text-xs text-teal-400";
    }

    try {
      const res = await fetchWithAuth(`${API_URL}/user/profile-photo`, {
        method: "POST",
        body: fd
      });
      const data = await res.json();
      if (res.ok) {
        if (profSaveStatus) {
          profSaveStatus.innerText = "Avatar uploaded successfully!";
          profSaveStatus.className = "text-xs text-emerald-400";
          setTimeout(() => { profSaveStatus.innerText = ""; }, 2500);
        }
        state.user.profile_pic = data.profile_pic;
        localStorage.setItem("aura_user", JSON.stringify(state.user));
        updateUserProfile();
        loadUserProfileView();
      } else {
        if (profSaveStatus) {
          profSaveStatus.innerText = data.detail || "Upload failed.";
          profSaveStatus.className = "text-xs text-rose-400";
        }
      }
    } catch (err) {
      if (profSaveStatus) {
        profSaveStatus.innerText = "Error uploading photo.";
        profSaveStatus.className = "text-xs text-rose-400";
      }
    }
  });
}

// =============================================================================
// INITIAL BOOT
// =============================================================================
applySidebarState();
if (state.token && isTokenExpired(state.token)) {
  console.warn("Stored token is expired on boot.");
  localStorage.removeItem("aura_token");
  localStorage.removeItem("aura_user");
  state.token = null;
  state.user = null;
}
showLanding();
refreshIcons();

// Speech Synthesis Streaming Buffer
let speechBuffer = "";
const synth = window.speechSynthesis;

function speakChunk(text) {
  if (!synth) return;
  const clean = text.replace(/[*#`_\[\]()]/g, "").trim();
  if (!clean) return;
  
  const utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.05;
  utter.pitch = 0.95;
  synth.speak(utter);
}

// In your SSE Stream Reader:
async function streamChatResponse(userPrompt, token) {
  const response = await fetch("http://127.0.0.1:8000/chat/stream", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message: userPrompt })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let fullResponse = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split("\n\n");

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const payloadStr = line.replace("data: ", "").trim();
        if (payloadStr === "[DONE]") {
          if (speechBuffer.trim()) {
            speakChunk(speechBuffer);
            speechBuffer = "";
          }
          break;
        }

        try {
          const parsed = JSON.parse(payloadStr);
          const tokenText = parsed.token;
          fullResponse += tokenText;
          speechBuffer += tokenText;

          // Speak naturally at sentence boundaries
          if (/[.!?\n]/.test(tokenText) && speechBuffer.length > 25) {
            speakChunk(speechBuffer);
            speechBuffer = "";
          }

          // Update chat UI element live
          document.getElementById("chat-stream-target").innerText = fullResponse;
        } catch (e) {
          // Keep parsing
        }
      }
    }
  }
}