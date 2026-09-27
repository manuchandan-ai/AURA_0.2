// ----------------- THREE.JS INTERACTIVE 3D BACKGROUND -----------------
const container = document.getElementById('webgl-canvas-container');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// Create 3D Singularity Geometric Core
const geom = new THREE.TorusKnotGeometry(3.5, 0.9, 120, 24);
const mat = new THREE.MeshStandardMaterial({
  color: 0x7c3aed,
  wireframe: true,
  roughness: 0.1
});
const singularity = new THREE.Mesh(geom, mat);
scene.add(singularity);

const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0x38bdf8, 2, 50);
pointLight.position.set(5, 5, 5);
scene.add(pointLight);

camera.position.z = 12;

function renderFrame() {
  requestAnimationFrame(renderFrame);
  singularity.rotation.x += 0.003;
  singularity.rotation.y += 0.006;
  renderer.render(scene, camera);
}
renderFrame();

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ----------------- FASTAPI STATE & AUTHENTICATION -----------------
const API_URL = "http://127.0.0.1:8000";
let authToken = localStorage.getItem("aura_token") || null;

async function fetchDashboard() {
  if (!authToken) {
    document.getElementById("view-container").innerHTML = `
      <div class="glass-card">
        <h2>🔒 Operator Session Required</h2>
        <p>Please authenticate via the API or Streamlit portal.</p>
      </div>
    `;
    return;
  }

  const res = await fetch(`${API_URL}/dashboard/summary`, {
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  if (res.ok) {
    const data = await res.json();
    document.getElementById("view-container").innerHTML = `
      <div class="glass-card">
        <h2>⚛️ Welcome Back, ${data.user.username.toUpperCase()}</h2>
        <p>Status: Active | Objectives: ${data.goals.length} | Directives: ${data.reminders.length}</p>
      </div>
    `;
  }
}

fetchDashboard();