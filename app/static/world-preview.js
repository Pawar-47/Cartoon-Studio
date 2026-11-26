import * as THREE from "/static/vendor/three/build/three.module.js";
import { GLTFLoader } from "/static/vendor/three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "/static/vendor/three/examples/jsm/controls/OrbitControls.js";

const canvas = document.getElementById("world-preview");
const status = document.getElementById("world-preview-status");
const empty = document.getElementById("world-preview-empty");
const loader = new GLTFLoader();
let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let currentRoot = null;

function resize() {
  if (!renderer || !canvas.parentElement) return;
  const width = Math.max(1, canvas.clientWidth);
  const height = Math.max(1, canvas.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function ensureRenderer() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "low-power",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x202c38);
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
  camera.position.set(85, 75, 95);
  scene.add(new THREE.HemisphereLight(0xdcecff, 0x59634c, 2.1));
  const key = new THREE.DirectionalLight(0xfff0d9, 3.0);
  key.position.set(45, 85, 30);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9fc6ff, 1.1);
  fill.position.set(-55, 35, -45);
  scene.add(fill);
  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.minDistance = 12;
  controls.maxDistance = 260;
  new ResizeObserver(resize).observe(canvas.parentElement);
  window.addEventListener("resize", resize);
  resize();
  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
}

function disposeRoot(root) {
  root.traverse((node) => {
    if (node.geometry) node.geometry.dispose();
    if (node.material) {
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      materials.forEach((material) => material.dispose());
    }
  });
}

export function clearWorldPreview() {
  if (currentRoot && scene) {
    scene.remove(currentRoot);
    disposeRoot(currentRoot);
    currentRoot = null;
  }
  empty.hidden = false;
  status.textContent = "Save and generate a scene to preview it.";
}

export async function showWorldPreview(url) {
  ensureRenderer();
  status.textContent = "Loading generated 3D world…";
  const gltf = await loader.loadAsync(url);
  if (currentRoot) {
    scene.remove(currentRoot);
    disposeRoot(currentRoot);
  }
  currentRoot = gltf.scene;
  scene.add(currentRoot);
  const bounds = new THREE.Box3().setFromObject(currentRoot);
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const extent = Math.max(size.x, size.y, size.z, 1);
  controls.target.copy(center);
  camera.position.set(center.x + extent * 1.15, center.y + extent * 0.9, center.z + extent * 1.35);
  camera.near = Math.max(extent / 1000, 0.01);
  camera.far = extent * 20;
  camera.updateProjectionMatrix();
  controls.minDistance = extent * 0.18;
  controls.maxDistance = extent * 5;
  controls.update();
  empty.hidden = true;
  status.textContent = "3D preview ready · " + currentRoot.children.length + " scene groups";
}
