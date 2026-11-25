import * as THREE from "/static/vendor/three/build/three.module.js";
import { GLTFLoader } from "/static/vendor/three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "/static/vendor/three/examples/jsm/controls/OrbitControls.js";
import { retargetClip } from "/static/vendor/three/examples/jsm/utils/SkeletonUtils.js";

const canvas = document.getElementById("model-preview");
const status = document.getElementById("preview-status");
const empty = document.getElementById("preview-empty");
const resetButton = document.getElementById("reset-view");
const animationSelect = document.getElementById("animation-select");
const loader = new GLTFLoader();

let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let currentObject = null;
let mixer = null;
let clips = [];
let clock = null;
let cameraDistance = 3;
let materialCatalog = [];
let materialByKey = new Map();
let morphTargetCatalog = [];
let morphTargetByKey = new Map();

function ensureRenderer() {
  if (renderer) return true;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: "low-power",
    });
  } catch (error) {
    status.textContent = "WebGL 2 is unavailable in this browser: " + error.message;
    return false;
  }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111923);
  camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  camera.position.set(2.8, 2.1, 3.2);

  scene.add(new THREE.HemisphereLight(0xd9e8ff, 0x40352c, 2.0));
  const key = new THREE.DirectionalLight(0xfff1df, 3.0);
  key.position.set(3, 5, 4);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8ebaff, 1.2);
  fill.position.set(-4, 2, -3);
  scene.add(fill);

  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.minDistance = 0.05;
  controls.maxDistance = 500;
  clock = new THREE.Clock();

  const resize = () => {
    const width = Math.max(1, canvas.clientWidth);
    const height = Math.max(1, canvas.clientHeight);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  };
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(resize).observe(canvas.parentElement);
  } else {
    window.addEventListener("resize", resize);
  }
  resize();

  renderer.setAnimationLoop(() => {
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    controls.update();
    renderer.render(scene, camera);
  });
  return true;
}

function disposeCurrentObject() {
  if (!currentObject) return;
  scene.remove(currentObject);
  currentObject.traverse((node) => {
    if (node.geometry) node.geometry.dispose();
    if (node.material) {
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      for (const material of materials) {
        for (const value of Object.values(material)) {
          if (value && value.isTexture) value.dispose();
        }
        material.dispose();
      }
    }
  });
  currentObject = null;
  mixer = null;
  clips = [];
  materialCatalog = [];
  materialByKey.clear();
  morphTargetCatalog = [];
  morphTargetByKey.clear();
}

function collectMaterials(root) {
  const entries = [];
  const visit = (node, path) => {
    if (node.isMesh && node.material) {
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      materials.forEach((material, slot) => {
        const key = path + "#material:" + slot;
        if (materialByKey.has(key)) return;
        const entry = {
          key,
          name: material.name || node.name || "Material",
          color: material.color ? "#" + material.color.getHexString() : "#ffffff",
          roughness: Number.isFinite(material.roughness) ? material.roughness : 0.5,
          metalness: Number.isFinite(material.metalness) ? material.metalness : 0,
        };
        materialByKey.set(key, material);
        entries.push(entry);
      });
    }
    node.children.forEach((child, index) => {
      const childName = child.name || child.type || "Node";
      visit(child, path + "/" + index + ":" + childName);
    });
  };
  visit(root, "0:" + (root.name || root.type || "Scene"));
  materialCatalog = entries;
}

export function getCharacterMaterials() {
  return materialCatalog.map((entry) => ({ ...entry }));
}

export function applyCharacterAppearance(recipe = {}) {
  for (const [key, values] of Object.entries(recipe)) {
    const material = materialByKey.get(key);
    if (!material) continue;
    if (values.color && material.color) material.color.set(values.color);
    if (Number.isFinite(values.roughness) && "roughness" in material) {
      material.roughness = values.roughness;
    }
    if (Number.isFinite(values.metalness) && "metalness" in material) {
      material.metalness = values.metalness;
    }
    material.needsUpdate = true;
  }
}

function collectMorphTargets(root) {
  const entries = [];
  const visit = (node, path) => {
    if (node.morphTargetDictionary && node.morphTargetInfluences) {
      for (const [name, index] of Object.entries(node.morphTargetDictionary)) {
        const key = path + "#morph:" + index + ":" + name;
        entries.push({
          key,
          name,
          value: Number(node.morphTargetInfluences[index] || 0),
        });
        morphTargetByKey.set(key, { node, index });
      }
    }
    node.children.forEach((child, index) => {
      const childName = child.name || child.type || "Node";
      visit(child, path + "/" + index + ":" + childName);
    });
  };
  visit(root, "0:" + (root.name || root.type || "Scene"));
  morphTargetCatalog = entries;
}

export function getCharacterMorphTargets() {
  return morphTargetCatalog.map((entry) => ({ ...entry }));
}

export function applyCharacterMorphTargets(recipe = {}) {
  for (const [key, value] of Object.entries(recipe)) {
    const target = morphTargetByKey.get(key);
    if (target) target.node.morphTargetInfluences[target.index] = value;
  }
}

export async function showCharacterPreview(buffer, label = "Character", appearance = {}, options = {}) {
  const playAnimations = options.playAnimations !== false;
  canvas.style.display = "block";
  if (!ensureRenderer()) return false;
  status.textContent = "Loading 3D model…";
  try {
    const gltf = await loader.parseAsync(buffer, "");
    disposeCurrentObject();
    currentObject = gltf.scene || gltf.scenes[0];
    if (!currentObject) throw new Error("The GLB contains no previewable scene.");
    scene.add(currentObject);
    currentObject.updateMatrixWorld(true);
    collectMaterials(currentObject);
    collectMorphTargets(currentObject);
    applyCharacterAppearance(appearance.materials || appearance);
    applyCharacterMorphTargets(appearance.morph_targets || {});

    const bounds = new THREE.Box3().setFromObject(currentObject);
    if (bounds.isEmpty()) throw new Error("The GLB scene contains no visible geometry.");
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    currentObject.position.sub(center);

    cameraDistance = Math.max(size.x, size.y, size.z, 0.1) * 2.1;
    camera.near = Math.max(cameraDistance / 10000, 0.001);
    camera.far = Math.max(cameraDistance * 100, 100);
    camera.position.set(cameraDistance * 0.9, cameraDistance * 0.65, cameraDistance * 1.15);
    camera.updateProjectionMatrix();
    controls.target.set(0, 0, 0);
    controls.update();

    animationSelect.replaceChildren();
    clips = gltf.animations;
    if (clips.length) {
      mixer = new THREE.AnimationMixer(currentObject);
      clips.forEach((clip, index) => {
        const option = document.createElement("option");
        option.value = String(index);
        option.textContent = clip.name || "Animation " + (index + 1);
        animationSelect.append(option);
      });
      if (playAnimations) mixer.clipAction(clips[0]).play();
      animationSelect.disabled = !playAnimations;
    } else {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No embedded animations";
      animationSelect.append(option);
      animationSelect.disabled = true;
    }

    empty.hidden = true;
    canvas.style.display = "block";
    resetButton.disabled = false;
    status.textContent = label + " · " + clips.length + " animation(s)" + (playAnimations ? "" : " · playback paused for appearance editing") + " · Drag to orbit, scroll to zoom";
    return true;
  } catch (error) {
    status.textContent = "Preview unavailable: " + error.message;
    return false;
  }
}

export function resetCharacterPreview() {
  if (!camera || !controls) return;
  camera.position.set(cameraDistance * 0.9, cameraDistance * 0.65, cameraDistance * 1.15);
  controls.target.set(0, 0, 0);
  controls.update();
}

resetButton.addEventListener("click", resetCharacterPreview);
animationSelect.addEventListener("change", () => {
  if (!mixer) return;
  mixer.stopAllAction();
  const index = Number(animationSelect.value);
  if (Number.isInteger(index) && clips[index]) mixer.clipAction(clips[index]).play();
});

export async function showRetargetPreview(sourceBuffer, targetBuffer, sourceMapping, targetMapping, animationName, label = "Retargeted character") {
  canvas.style.display = "block";
  if (!ensureRenderer()) return false;
  status.textContent = "Preparing browser retarget preview…";
  try {
    const [sourceGltf, targetGltf] = await Promise.all([loader.parseAsync(sourceBuffer, ""), loader.parseAsync(targetBuffer, "")]);
    const findSkinnedMesh = (root) => {
      let result = null;
      root.traverse((node) => { if (!result && node.isSkinnedMesh && node.skeleton) result = node; });
      return result;
    };
    const sourceMesh = findSkinnedMesh(sourceGltf.scene), targetMesh = findSkinnedMesh(targetGltf.scene);
    if (!sourceMesh || !targetMesh) throw new Error("Both GLBs must contain a skinned humanoid mesh.");
    const clip = sourceGltf.animations.find((item) => item.name === animationName)
      || sourceGltf.animations.find((item) => item.name.toUpperCase() !== "RESET");
    if (!clip) throw new Error("The saved source animation is no longer available.");
    const names = {};
    for (const profileName of Object.keys(sourceMapping || {})) {
      const sourceName = sourceMapping[profileName], targetName = targetMapping?.[profileName];
      if (sourceName && targetName) names[targetName] = sourceName;
    }
    if (Object.keys(names).length < 15) throw new Error("The saved humanoid mapping is incomplete; browser preview was not started.");
    const retargetedClip = retargetClip(targetMesh, sourceMesh, clip, {
      names, hip: sourceMapping?.Hips || "Hips", preserveBoneMatrix: true, preserveBonePositions: true,
    });
    if (!retargetedClip || !retargetedClip.tracks.length) throw new Error("Three.js could not produce a retargeted animation clip.");
    disposeCurrentObject();
    currentObject = targetGltf.scene;
    scene.add(currentObject);
    currentObject.updateMatrixWorld(true);
    collectMaterials(currentObject);
    collectMorphTargets(currentObject);
    const bounds = new THREE.Box3().setFromObject(currentObject);
    if (bounds.isEmpty()) throw new Error("The target GLB contains no visible geometry.");
    const center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    currentObject.position.sub(center);
    cameraDistance = Math.max(size.x, size.y, size.z, 0.1) * 2.1;
    camera.near = Math.max(cameraDistance / 10000, 0.001);
    camera.far = Math.max(cameraDistance * 100, 100);
    camera.position.set(cameraDistance * 0.9, cameraDistance * 0.65, cameraDistance * 1.15);
    camera.updateProjectionMatrix();
    controls.target.set(0, 0, 0);
    controls.update();
    clips = [retargetedClip];
    mixer = new THREE.AnimationMixer(currentObject);
    mixer.clipAction(retargetedClip).play();
    animationSelect.replaceChildren();
    const option = document.createElement("option");
    option.value = "0";
    option.textContent = retargetedClip.name || "Retargeted " + clip.name;
    animationSelect.append(option);
    animationSelect.disabled = true;
    empty.hidden = true;
    resetButton.disabled = false;
    status.textContent = label + " · browser preview only; saved Godot scene remains authoritative.";
    return true;
  } catch (error) {
    status.textContent = "Retarget preview unavailable: " + error.message;
    return false;
  }
}
