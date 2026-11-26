import * as THREE from "/static/vendor/three/build/three.module.js";
import { GLTFLoader } from "/static/vendor/three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "/static/vendor/three/examples/jsm/controls/OrbitControls.js";
import { retargetClip } from "/static/vendor/three/examples/jsm/utils/SkeletonUtils.js";
import { prepareRetargetedClip } from "./retarget-preview.mjs";
import { resolveAnimationClip, resolveDefaultAnimationClip } from "./animation-clip.mjs";

const canvas = document.getElementById("model-preview");
const status = document.getElementById("preview-status");
const empty = document.getElementById("preview-empty");
const resetButton = document.getElementById("reset-view");
const animationSelect = document.getElementById("animation-select");
const playbackButton = document.getElementById("preview-playback");
const playbackSpeed = document.getElementById("preview-speed");
const exportPreviewButton = document.getElementById("export-preview-png");
const exportTurnaroundButton = document.getElementById("export-turnaround-png");
const frameButtons = document.querySelectorAll("[data-camera-frame]");
const loader = new GLTFLoader();

let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let currentObject = null;
let mixer = null;
let clips = [];
let activeAction = null;
let playbackPaused = false;
let previewFrozen = false;
let clock = null;
let cameraDistance = 3;
let characterBounds = null;
let materialCatalog = [];
let materialByKey = new Map();
let morphTargetCatalog = [];
let morphTargetByKey = new Map();
let proportionBones = new Map();
let proportionBoneBaseline = new Map();

function ensureRenderer() {
  if (renderer) return true;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
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
    if (previewFrozen) return;
    if (mixer) mixer.update(delta);
    controls.update();
    renderer.render(scene, camera);
  });
  return true;
}

function disposeCurrentObject() {
  if (!currentObject) return;
  removeFaceFeaturePreview();
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
  activeAction = null;
  playbackPaused = false;
  updatePlaybackControls();
  characterBounds = null;
  materialCatalog = [];
  materialByKey.clear();
  morphTargetCatalog = [];
  morphTargetByKey.clear();
  proportionBones.clear();
  proportionBoneBaseline.clear();
}

function updatePlaybackControls() {
  playbackButton.disabled = !activeAction;
  playbackButton.textContent = playbackPaused ? "Play" : "Pause";
  playbackButton.setAttribute("aria-pressed", String(!playbackPaused));
  playbackSpeed.disabled = !activeAction;
  exportPreviewButton.disabled = !currentObject;
  exportTurnaroundButton.disabled = !currentObject;
  frameButtons.forEach((button) => { button.disabled = !currentObject; });
}

function setPlaybackPaused(paused) {
  if (!mixer || !activeAction) return;
  if (!activeAction.isRunning()) activeAction.play();
  playbackPaused = Boolean(paused);
  activeAction.paused = playbackPaused;
  updatePlaybackControls();
}

function frameCharacter(preset = "full") {
  if (!camera || !controls || !characterBounds || characterBounds.isEmpty()) return;
  const size = characterBounds.getSize(new THREE.Vector3());
  const center = characterBounds.getCenter(new THREE.Vector3());
  const direction = new THREE.Vector3(0.9, 0.65, 1.15).normalize();
  let targetY = center.y;
  let distance = cameraDistance;
  if (preset === "head") {
    targetY = characterBounds.min.y + size.y * 0.88;
    distance = cameraDistance * 0.42;
  } else if (preset === "upper") {
    targetY = characterBounds.min.y + size.y * 0.66;
    distance = cameraDistance * 0.72;
  }
  const target = new THREE.Vector3(center.x, targetY, center.z);
  controls.target.copy(target);
  camera.position.copy(target).addScaledVector(direction, distance);
  camera.near = Math.max(distance / 10000, 0.001);
  camera.far = Math.max(cameraDistance * 100, 100);
  camera.updateProjectionMatrix();
  controls.update();
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
          meshName: node.name || "Mesh",
          surfaceIndex: slot,
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
  return materialCatalog.map((entry) => {
    const material = materialByKey.get(entry.key);
    return {
      ...entry,
      color: material?.color ? "#" + material.color.getHexString() : entry.color,
    };
  });
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
  morphTargetByKey.clear();
  const entries = [];
  const visit = (node, path) => {
    if (node.morphTargetDictionary && node.morphTargetInfluences) {
      for (const [name, index] of Object.entries(node.morphTargetDictionary)) {
        const key = path + "#morph:" + index + ":" + name;
        entries.push({
          key,
          name,
          meshName: node.name || "Mesh",
          targetIndex: index,
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


let faceFeatureGroup = null;
let faceFeatureParent = null;
const faceSuppressedMaterials = new Map();

const faceSurfaceTokens = ["skin", "eye", "brow", "eyebrow", "nose", "nostril", "ear", "mustache", "moustache"];

function faceMaterialGroups(node) {
  const geometry = node.geometry;
  if (geometry.groups.length) return geometry.groups;
  const vertexCount = geometry.index ? geometry.index.count : geometry.attributes.position.count;
  return [{ start: 0, count: vertexCount, materialIndex: 0 }];
}

function faceSurfaceLabel(node, group) {
  const materials = Array.isArray(node.material) ? node.material : [node.material];
  const material = materials[group.materialIndex] || materials[0];
  return [node.name, node.geometry?.name, material?.name].filter(Boolean).join(" ").toLowerCase();
}

function isReplaceableFaceSurface(label) {
  return faceSurfaceTokens.some((token) => label.includes(token));
}

function surfaceBoundsInBoneSpace(node, bone, matches) {
  const bounds = new THREE.Box3().makeEmpty();
  const vertex = new THREE.Vector3();
  const meshes = [];
  if (node?.isMesh) meshes.push(node);
  else node?.traverse((child) => { if (child.isMesh) meshes.push(child); });
  for (const mesh of meshes) {
    const geometry = mesh.geometry;
    const position = geometry?.attributes?.position;
    if (!position) continue;
    const index = geometry.index;
    for (const group of faceMaterialGroups(mesh)) {
      if (!matches(faceSurfaceLabel(mesh, group))) continue;
      const start = Math.max(0, group.start || 0);
      const end = Math.min(index ? index.count : position.count, start + (group.count ?? position.count));
      for (let offset = start; offset < end; offset += 1) {
        const vertexIndex = index ? index.getX(offset) : offset;
        if (typeof mesh.getVertexPosition === "function") mesh.getVertexPosition(vertexIndex, vertex);
        else vertex.fromBufferAttribute(position, vertexIndex);
        mesh.localToWorld(vertex);
        bone.worldToLocal(vertex);
        bounds.expandByPoint(vertex);
      }
    }
  }
  return bounds.isEmpty() ? null : bounds;
}

function suppressImportedFaceSurfaces(root) {
  const hideSurface = (node) => {
    if (!node?.isMesh || !node.geometry?.attributes?.position) return;
    const groups = faceMaterialGroups(node);
    const targetedSlots = new Set(groups
      .filter((group) => isReplaceableFaceSurface(faceSurfaceLabel(node, group)))
      .map((group) => group.materialIndex));
    if (!targetedSlots.size) return;
    const original = node.material;
    const materials = Array.isArray(original) ? [...original] : [original];
    const hidden = [];
    for (const slot of targetedSlots) {
      const invisible = new THREE.MeshBasicMaterial({
        transparent: true,
        opacity: 0,
        colorWrite: false,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      invisible.visible = false;
      hidden.push(invisible);
      materials[slot] = invisible;
    }
    faceSuppressedMaterials.set(node, { original, hidden });
    node.material = Array.isArray(original) ? materials : materials[0];
  };
  if (root?.isMesh) hideSurface(root);
  else root?.traverse(hideSurface);
}

function headSurfaceRoot(headMesh) {
  let candidate = headMesh;
  for (let parent = headMesh?.parent; parent; parent = parent.parent) {
    if (/(head|face|skull)/i.test(parent.name || "")) candidate = parent;
  }
  return candidate;
}

function restoreImportedFaceSurfaces() {
  for (const [node, state] of faceSuppressedMaterials) {
    node.material = state.original;
    state.hidden.forEach((material) => material.dispose());
  }
  faceSuppressedMaterials.clear();
}

function generatedFaceFrontDepth(bounds, center, x, y, faceWidth, cheekFullness, jawWidth, frontDirection) {
  const t = THREE.MathUtils.clamp((bounds.max.y - y) / Math.max(bounds.getSize(new THREE.Vector3()).y, 0.001), 0.025, 0.975);
  const profile = Math.max(Math.sin(Math.PI * t), 0.025);
  const lowerFace = THREE.MathUtils.clamp((t - 0.58) / 0.42, 0, 1);
  const jawProfile = THREE.MathUtils.lerp(1, THREE.MathUtils.clamp(jawWidth, 0.7, 1.3), Math.pow(lowerFace, 1.2));
  const cheekDistance = (t - 0.47) / 0.14;
  const cheekProfile = 1 + (THREE.MathUtils.clamp(cheekFullness, 0.5, 1.5) - 1) * Math.exp(-cheekDistance * cheekDistance);
  const size = bounds.getSize(new THREE.Vector3());
  const xRadius = Math.max(size.x * 0.5 * Math.pow(profile, 0.72) * jawProfile * cheekProfile * faceWidth, 0.001);
  const zRadius = size.z * 0.5 * Math.pow(profile, 0.72) * THREE.MathUtils.lerp(0.92, 1, cheekProfile - 0.5);
  const sideRatio = THREE.MathUtils.clamp((x - center.x) / xRadius, -0.97, 0.97);
  return center.z + frontDirection * zRadius * Math.sqrt(1 - sideRatio * sideRatio);
}

function makeGeneratedFaceHeadGeometry(bounds, center, faceWidth, cheekFullness, jawWidth, chinLength, frontDirection) {
  const ringCount = 18;
  const segmentCount = 28;
  const size = bounds.getSize(new THREE.Vector3());
  const positions = [];
  const uvs = [];
  const indices = [];
  for (let ringIndex = 0; ringIndex <= ringCount; ringIndex += 1) {
    const t = ringIndex / ringCount;
    const vertical = Math.cos(Math.PI * t);
    const profile = Math.max(Math.sin(Math.PI * t), 0.025);
    const lowerFace = THREE.MathUtils.clamp((t - 0.58) / 0.42, 0, 1);
    const chinProfile = THREE.MathUtils.lerp(1, THREE.MathUtils.clamp(chinLength, 0.65, 1.4), Math.pow(lowerFace, 1.7));
    const jawProfile = THREE.MathUtils.lerp(1, THREE.MathUtils.clamp(jawWidth, 0.7, 1.3), Math.pow(lowerFace, 1.2));
    const cheekDistance = (t - 0.47) / 0.14;
    const cheekProfile = 1 + (THREE.MathUtils.clamp(cheekFullness, 0.5, 1.5) - 1) * Math.exp(-cheekDistance * cheekDistance);
    const xRadius = size.x * 0.5 * Math.pow(profile, 0.72) * jawProfile * cheekProfile * faceWidth;
    const zRadius = size.z * 0.5 * Math.pow(profile, 0.72) * THREE.MathUtils.lerp(0.92, 1, cheekProfile - 0.5);
    let yOffset = vertical * size.y * 0.5;
    if (t > 0.84) yOffset -= (chinProfile - 1) * size.y * 0.08;
    for (let segmentIndex = 0; segmentIndex <= segmentCount; segmentIndex += 1) {
      const u = segmentIndex / segmentCount;
      const angle = Math.PI * 2 * u;
      positions.push(
        center.x + Math.cos(angle) * xRadius,
        center.y + yOffset,
        center.z + Math.sin(angle) * zRadius * frontDirection,
      );
      uvs.push(u, t);
    }
  }
  const rowWidth = segmentCount + 1;
  for (let ringIndex = 0; ringIndex < ringCount; ringIndex += 1) {
    for (let segmentIndex = 0; segmentIndex < segmentCount; segmentIndex += 1) {
      const a = ringIndex * rowWidth + segmentIndex;
      const b = (ringIndex + 1) * rowWidth + segmentIndex;
      const c = b + 1;
      const d = a + 1;
      if (frontDirection > 0) indices.push(a, d, b, b, d, c);
      else indices.push(a, b, d, b, c, d);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function removeFaceFeaturePreview() {
  if (faceFeatureGroup) {
    faceFeatureParent?.remove(faceFeatureGroup);
    faceFeatureGroup.traverse((node) => {
      node.geometry?.dispose();
      if (node.material) (Array.isArray(node.material) ? node.material : [node.material]).forEach((material) => material.dispose());
    });
    faceFeatureGroup = null;
    faceFeatureParent = null;
  }
  restoreImportedFaceSurfaces();
}

function boxInLocalSpace(worldBox, localObject) {
  const points = [];
  for (const x of [worldBox.min.x, worldBox.max.x]) {
    for (const y of [worldBox.min.y, worldBox.max.y]) {
      for (const z of [worldBox.min.z, worldBox.max.z]) {
        points.push(localObject.worldToLocal(new THREE.Vector3(x, y, z)));
      }
    }
  }
  return new THREE.Box3().setFromPoints(points);
}

function detectCharacterFaceDirection(headCenter, headBone, headRoot) {
  const eyeBounds = surfaceBoundsInBoneSpace(headRoot, headBone, (label) => label.includes("eye"));
  const browBounds = surfaceBoundsInBoneSpace(headRoot, headBone, (label) => label.includes("brow") || label.includes("eyebrow"));
  const direction = eyeBounds ? (eyeBounds.getCenter(new THREE.Vector3()).z >= headCenter.z ? 1 : -1) : 1;
  let skinColor = "#c98768";
  const inspectMaterials = (mesh) => {
    if (skinColor !== "#c98768" || !mesh.isMesh) return;
    for (const group of faceMaterialGroups(mesh)) {
      if (!faceSurfaceLabel(mesh, group).includes("skin")) continue;
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const material = materials[group.materialIndex] || materials[0];
      if (material?.color) skinColor = "#" + material.color.getHexString(THREE.SRGBColorSpace);
      return;
    }
  };
  if (headRoot?.isMesh) inspectMaterials(headRoot);
  else headRoot?.traverse(inspectMaterials);
  return { direction, eyeBounds, browBounds, skinColor };
}

export function applyCharacterFaceFeatures(recipe = {}) {
  if (!currentObject) return false;
  removeFaceFeaturePreview();
  if (!recipe.enabled) return true;
  currentObject.updateMatrixWorld(true);
  let headBone = null;
  currentObject.traverse((node) => {
    if (headBone || !node.isBone) return;
    const token = (node.name || "").split(":").pop().toLowerCase().replace(/[_\s]/g, "");
    if (token === "head" || /^head\d+$/.test(token)) headBone = node;
  });
  if (!headBone) return false;
  let head = null;
  let headMesh = null;
  const meshCandidates = [];
  currentObject.traverse((node) => {
    if (!node.isMesh || !node.geometry?.attributes?.position) return;
    const worldBox = new THREE.Box3().setFromObject(node, true);
    if (worldBox.isEmpty()) return;
    const box = boxInLocalSpace(worldBox, headBone);
    const candidate = { node, box, worldBox };
    meshCandidates.push(candidate);
    const label = [node.name, node.geometry.name, node.parent?.name].filter(Boolean).join(" ");
    if (/(head|face|skull)/i.test(label) && (!head || box.getSize(new THREE.Vector3()).y > head.getSize(new THREE.Vector3()).y)) {
      head = box;
      headMesh = node;
    }
  });
  if (!head) {
    const worldBounds = new THREE.Box3().setFromObject(currentObject, true);
    if (worldBounds.isEmpty()) return false;
    const wholeSize = worldBounds.getSize(new THREE.Vector3());
    const upperThreshold = worldBounds.min.y + wholeSize.y * 0.68;
    const upperMeshes = meshCandidates.filter((candidate) => candidate.worldBox.getCenter(new THREE.Vector3()).y >= upperThreshold);
    upperMeshes.sort((a, b) => b.worldBox.getCenter(new THREE.Vector3()).y - a.worldBox.getCenter(new THREE.Vector3()).y);
    if (!upperMeshes.length) return false;
    headMesh = upperMeshes[0].node;
    head = upperMeshes[0].box;
  }
  const headRoot=headSurfaceRoot(headMesh);
  const skinBounds=surfaceBoundsInBoneSpace(headRoot,headBone,(label)=>label.includes("skin"));
  if(!skinBounds)return false;
  const faceSurface=detectCharacterFaceDirection(skinBounds.getCenter(new THREE.Vector3()),headBone,headRoot);
  head=skinBounds;
  const size=head.getSize(new THREE.Vector3()), center=head.getCenter(new THREE.Vector3());
  const faceWidth=THREE.MathUtils.clamp(Number(recipe.face_width??1),0.8,1.25);
  const cheekFullness=THREE.MathUtils.clamp(Number(recipe.cheek_fullness??1),0.5,1.5);
  const jawWidth=THREE.MathUtils.clamp(Number(recipe.jaw_width??1),0.7,1.3);
  const chinLength=THREE.MathUtils.clamp(Number(recipe.chin_length??1),0.65,1.4);
  const earSize=THREE.MathUtils.clamp(Number(recipe.ear_size??1),0.6,1.5);
  const noseWidth=THREE.MathUtils.clamp(Number(recipe.nose_width??1),0.65,1.5);
  const noseHeight=THREE.MathUtils.clamp(Number(recipe.nose_height??1),0.65,1.5);
  const mouthWidth=THREE.MathUtils.clamp(Number(recipe.mouth_width??1),0.65,1.5);
  const width=Math.max(size.x*0.56,size.y*0.18,0.035)*faceWidth;
  const height=Math.max(size.y*0.48,width*0.55,0.035);
  const frontDirection=faceSurface.direction;
  const eyeCenter=faceSurface.eyeBounds?.getCenter(new THREE.Vector3());
  const faceCenterX=center.x;
  const eyeY=eyeCenter?.y??center.y+height*0.10;
  const eyeScale=THREE.MathUtils.clamp(Number(recipe.eye_scale??1),0.65,1.5);
  const spacing=THREE.MathUtils.clamp(Number(recipe.eye_spacing??1),0.65,1.35);
  const smile=THREE.MathUtils.clamp(Number(recipe.smile??0.35),-1,1);
  const mouthOpen=THREE.MathUtils.clamp(Number(recipe.mouth_open??0),0,1);
  const browAngle=THREE.MathUtils.clamp(Number(recipe.brow_angle??0),-0.5,0.5);
  const depth=Math.max(width*0.045,0.008);
  const noseY=eyeY-size.y*0.08;
  const mouthY=eyeY-size.y*0.27;
  const browY=faceSurface.browBounds?.getCenter(new THREE.Vector3()).y??eyeY+height*0.18;
  const frontAt=(x,y)=>generatedFaceFrontDepth(head,center,x,y,faceWidth,cheekFullness,jawWidth,frontDirection);
  const group=new THREE.Group();group.name="CartoonStudioFacePreview";
  const mat=(color,roughness=0.72)=>new THREE.MeshStandardMaterial({color:color||"#ffffff",roughness,metalness:0,depthTest:true,depthWrite:false,side:THREE.DoubleSide});
  const ellipsoid=(name,color,pos,scale,roughness=0.72)=>{
    const mesh=new THREE.Mesh(new THREE.SphereGeometry(1,20,14),mat(color,roughness));
    mesh.name=name;mesh.position.copy(pos);mesh.scale.set(scale.x,scale.y,scale.z);mesh.renderOrder=2;group.add(mesh);return mesh;
  };
  const eyeBounds=faceSurface.eyeBounds;
  const eyeWidth=Math.min(width*0.105*eyeScale,eyeBounds?Math.max(eyeBounds.getSize(new THREE.Vector3()).x*0.12,0.005):width*0.105*eyeScale);
  const eyeHeight=Math.min(height*0.17*eyeScale,eyeBounds?Math.max(eyeBounds.getSize(new THREE.Vector3()).y*0.45,0.005):height*0.17*eyeScale);
  const eyeOffset=(eyeBounds?Math.max(eyeBounds.getSize(new THREE.Vector3()).x*0.25,width*0.18):width*0.245)*spacing;
  const skinColor=recipe.skin_color_auto===false?(recipe.skin_color||"#c98768"):faceSurface.skinColor;
  const noseColor=recipe.nose_color_auto===false?(recipe.nose_color||skinColor):skinColor;
  const generatedHead=new THREE.Mesh(makeGeneratedFaceHeadGeometry(head,center,faceWidth,cheekFullness,jawWidth,chinLength,frontDirection),new THREE.MeshStandardMaterial({color:skinColor,roughness:0.82,side:THREE.DoubleSide}));
  generatedHead.name="CartoonStudio_Face_Head";generatedHead.renderOrder=1;group.add(generatedHead);
  for(const side of [-1,1]){
    const earX=center.x+side*(size.x*0.5+width*0.025);
    const earY=eyeY-size.y*0.055;
    const earSurfaceX=center.x+side*size.x*0.46;
    const earZ=frontAt(earSurfaceX,earY)+frontDirection*depth*0.25;
    ellipsoid("CartoonStudio_Face_Ear",skinColor,new THREE.Vector3(earX,earY,earZ),new THREE.Vector3(width*0.11*earSize,height*0.14*earSize,depth*0.78*earSize));
  }
  for(const side of [-1,1]){
    const earX=center.x+side*(size.x*0.5+width*0.025);
    const earY=eyeY-size.y*0.055;
    const earSurfaceX=center.x+side*size.x*0.46;
    const earZ=frontAt(earSurfaceX,earY)+frontDirection*depth*0.62;
    ellipsoid("CartoonStudio_Face_EarInner","#a96859",new THREE.Vector3(earX,earY,earZ),new THREE.Vector3(width*0.035*earSize,height*0.075*earSize,depth*0.3*earSize));
  }
  for(const side of [-1,1]){
    const x=center.x+side*eyeOffset;
    const eyeZ=frontAt(x,eyeY)+frontDirection*Math.max(depth*0.08,0.001);
    ellipsoid("CartoonStudio_Face_EyeWhite",recipe.eye_color,new THREE.Vector3(x,eyeY,eyeZ),new THREE.Vector3(eyeWidth,eyeHeight,depth));
    ellipsoid("CartoonStudio_Face_Iris",recipe.iris_color,new THREE.Vector3(x+width*0.018,eyeY-height*0.012,eyeZ+frontDirection*depth*0.82),new THREE.Vector3(eyeWidth*0.49,eyeHeight*0.57,depth*0.42),0.35);
    ellipsoid("CartoonStudio_Face_Pupil","#17191d",new THREE.Vector3(x+width*0.022,eyeY-height*0.012,eyeZ+frontDirection*depth*1.16),new THREE.Vector3(eyeWidth*0.23,eyeHeight*0.34,depth*0.22),0.25);
    const brow=ellipsoid("CartoonStudio_Face_Brow",recipe.brow_color,new THREE.Vector3(x,browY,frontAt(x,browY)+frontDirection*depth*0.08),new THREE.Vector3(eyeWidth*1.32,Math.max(eyeHeight*0.24,0.004),depth*0.3));
    brow.rotation.z=-side*browAngle;
  }
  const noseBridgeY=eyeY-(eyeY-noseY)*0.42;
  ellipsoid("CartoonStudio_Face_NoseBridge",noseColor,new THREE.Vector3(center.x,noseBridgeY,frontAt(center.x,noseBridgeY)+frontDirection*depth*0.32),new THREE.Vector3(width*0.025*noseWidth,height*0.075*noseHeight,depth*0.45));
  ellipsoid("CartoonStudio_Face_Nose",noseColor,new THREE.Vector3(center.x,noseY,frontAt(center.x,noseY)+frontDirection*depth*0.42),new THREE.Vector3(width*0.05*noseWidth,height*0.055*noseHeight,depth*0.62));
  for(const side of [-1,1]){
    const x=center.x+side*width*0.027*noseWidth;
    const y=noseY-size.y*0.025;
    ellipsoid("CartoonStudio_Face_Nostril","#633e36",new THREE.Vector3(x,y,frontAt(x,y)+frontDirection*depth*0.82),new THREE.Vector3(width*0.016*noseWidth,height*0.018*noseHeight,depth*0.19));
  }
  const my=mouthY,mw=width*0.19*mouthWidth;
  const mouthDepth=frontAt(center.x,my)+frontDirection*depth*0.38;
  if(recipe.moustache_enabled){
    const moustacheSize=THREE.MathUtils.clamp(Number(recipe.moustache_size??1),0.6,1.5);
    const moustacheY=my+height*0.15;
    for(const side of [-1,1]){
      const x=center.x+side*width*0.078*moustacheSize;
      const lobe=ellipsoid("CartoonStudio_Face_Moustache",recipe.moustache_color||"#38251c",new THREE.Vector3(x,moustacheY,frontAt(x,moustacheY)+frontDirection*depth*0.38),new THREE.Vector3(width*0.075*moustacheSize,height*0.032*moustacheSize,depth*0.42));
      lobe.rotation.z=-side*0.16;
    }
  }
  if(mouthOpen>0.08){
    ellipsoid("CartoonStudio_Face_MouthOpening",recipe.mouth_color,new THREE.Vector3(center.x,my,mouthDepth),new THREE.Vector3(mw,height*(0.018+mouthOpen*0.11),depth*0.62));
    if(mouthOpen>0.45)ellipsoid("CartoonStudio_Face_MouthTongue","#c65f72",new THREE.Vector3(center.x,my-height*0.035,mouthDepth+frontDirection*depth*0.62),new THREE.Vector3(mw*0.52,height*0.025,depth*0.2));
  }else{
    const curve=new THREE.CatmullRomCurve3([
      new THREE.Vector3(center.x-mw,my+smile*height*0.075,frontAt(center.x-mw,my+smile*height*0.075)+frontDirection*depth*0.42),
      new THREE.Vector3(center.x-mw*0.5,my-smile*height*0.07,frontAt(center.x-mw*0.5,my-smile*height*0.07)+frontDirection*depth*0.42),
      new THREE.Vector3(center.x+mw*0.5,my-smile*height*0.07,frontAt(center.x+mw*0.5,my-smile*height*0.07)+frontDirection*depth*0.42),
      new THREE.Vector3(center.x+mw,my+smile*height*0.075,frontAt(center.x+mw,my+smile*height*0.075)+frontDirection*depth*0.42),
    ]);
    const mouth=new THREE.Mesh(new THREE.TubeGeometry(curve,20,Math.max(width*0.012,0.003),8,false),mat(recipe.mouth_color));
    mouth.name="CartoonStudio_Face_Mouth";mouth.renderOrder=2;group.add(mouth);
  }
  suppressImportedFaceSurfaces(headRoot);
  headBone.add(group);faceFeatureGroup=group;faceFeatureParent=headBone;return true;
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

function collectProportionBones(root) {
  proportionBones.clear();
  proportionBoneBaseline.clear();
  root.traverse((node) => {
    if (!node.isBone || !node.name) return;
    if (proportionBones.has(node.name)) {
      proportionBones.set(node.name, null);
      return;
    }
    proportionBones.set(node.name, node);
    proportionBoneBaseline.set(node.name, {
      position: node.position.toArray(),
      scale: node.scale.toArray(),
    });
  });
}

export function applyCharacterBodyProportions(proportions = {}, boneMapping = {}) {
  if (!currentObject || !proportionBones.size) return;
  if (activeAction && !playbackPaused) setPlaybackPaused(true);
  for (const [name, node] of proportionBones) {
    if (!node) continue;
    const baseline = proportionBoneBaseline.get(name);
    node.position.fromArray(baseline.position);
    node.scale.fromArray(baseline.scale);
  }
  const groups = [
    { factor: "torso_length", bones: ["Spine", "Head"], mode: "vertical" },
    { factor: "shoulder_width", bones: ["LeftUpperArm", "RightUpperArm"], mode: "horizontal" },
    { factor: "arm_length", bones: ["LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand"], mode: "vector" },
    { factor: "leg_length", bones: ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"], mode: "vector" },
    { factor: "head_size", bones: ["Head"], mode: "basis" },
  ];
  for (const group of groups) {
    const factor = Number(proportions[group.factor] ?? 1);
    if (!Number.isFinite(factor) || Math.abs(factor - 1) < 0.0001) continue;
    for (const canonicalName of group.bones) {
      const actualName = boneMapping[canonicalName] || canonicalName;
      const bone = proportionBones.get(actualName);
      if (!bone) continue;
      if (group.mode === "vertical") bone.position.y *= factor;
      else if (group.mode === "horizontal") bone.position.x *= factor;
      else if (group.mode === "vector") bone.position.multiplyScalar(factor);
      else if (group.mode === "basis") bone.scale.multiplyScalar(factor);
    }
  }
  currentObject.updateMatrixWorld(true);
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
    collectProportionBones(currentObject);
    applyCharacterAppearance(appearance.materials || appearance);
    applyCharacterMorphTargets(appearance.morph_targets || {});

    const bounds = new THREE.Box3().setFromObject(currentObject);
    if (bounds.isEmpty()) throw new Error("The GLB scene contains no visible geometry.");
    const center = bounds.getCenter(new THREE.Vector3());
    const size = bounds.getSize(new THREE.Vector3());
    currentObject.position.sub(center);
    applyCharacterFaceFeatures(appearance.face_features || {});

    cameraDistance = Math.max(size.x, size.y, size.z, 0.1) * 2.1;
    characterBounds = bounds.clone();
    characterBounds.min.sub(center);
    characterBounds.max.sub(center);
    frameCharacter("full");

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
      const initialClip = resolveDefaultAnimationClip(clips);
      if (initialClip) {
        animationSelect.value = String(clips.indexOf(initialClip));
        activeAction = mixer.clipAction(initialClip);
        activeAction.play();
        playbackPaused = !playAnimations;
        activeAction.paused = playbackPaused;
        mixer.timeScale = Number(playbackSpeed.value) || 1;
        animationSelect.disabled = !playAnimations;
      } else {
        animationSelect.replaceChildren();
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "No playable animations";
        animationSelect.append(option);
        animationSelect.disabled = true;
      }
    } else {
      activeAction = null;
      playbackPaused = false;
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No embedded animations";
      animationSelect.append(option);
      animationSelect.disabled = true;
    }

    updatePlaybackControls();
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
  frameCharacter("full");
}


export async function exportCharacterTurnaround({ width = 1024, transparent = true } = {}) {
  if (!renderer || !currentObject || !camera || !scene || !controls) {
    throw new Error("Load a character preview before exporting a turnaround sheet.");
  }
  const tileSize = Math.max(256, Math.min(1024, Math.round(Number(width) || 1024)));
  const previousSize = renderer.getSize(new THREE.Vector2());
  const previousPixelRatio = renderer.getPixelRatio();
  const previousAspect = camera.aspect;
  const previousPosition = camera.position.clone();
  const previousQuaternion = camera.quaternion.clone();
  const previousTarget = controls.target.clone();
  const previousControlsEnabled = controls.enabled;
  const previousBackground = scene.background;
  const previousClearColor = renderer.getClearColor(new THREE.Color()).clone();
  const previousClearAlpha = renderer.getClearAlpha();
  const labels = ["3/4", "Side", "Back", "Opposite"];
  try {
    previewFrozen = true;
    controls.enabled = false;
    frameCharacter("full");
    const turnaroundTarget = controls.target.clone();
    const offset = camera.position.clone().sub(turnaroundTarget);
    const horizontalRadius = Math.max(Math.hypot(offset.x, offset.z), 0.01);
    const baseAngle = Math.atan2(offset.x, offset.z);
    const sheet = window.document.createElement("canvas");
    sheet.width = tileSize * 2;
    sheet.height = tileSize * 2;
    const context = sheet.getContext("2d");
    if (!context) throw new Error("The browser could not create a 2D canvas for the turnaround sheet.");
    const captureTile = () => new Promise((resolve, reject) => {
      renderer.domElement.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error("The browser could not encode a turnaround view.")),
        "image/png",
      );
    });
    renderer.setPixelRatio(1);
    renderer.setSize(tileSize, tileSize, false);
    camera.aspect = 1;
    camera.updateProjectionMatrix();
    if (transparent) {
      scene.background = null;
      renderer.setClearColor(0x000000, 0);
    }
    for (let index = 0; index < 4; index += 1) {
      const angle = baseAngle + (Math.PI / 2) * index;
      camera.position.set(
        turnaroundTarget.x + Math.sin(angle) * horizontalRadius,
        turnaroundTarget.y + offset.y,
        turnaroundTarget.z + Math.cos(angle) * horizontalRadius,
      );
      camera.lookAt(turnaroundTarget);
      controls.update();
      renderer.render(scene, camera);
      const blob = await captureTile();
      const bitmap = await createImageBitmap(blob);
      const x = (index % 2) * tileSize;
      const y = Math.floor(index / 2) * tileSize;
      context.drawImage(bitmap, x, y, tileSize, tileSize);
      bitmap.close?.();
      context.fillStyle = "rgba(0, 0, 0, 0.55)";
      context.fillRect(x + 12, y + tileSize - 38, 104, 26);
      context.fillStyle = "#ffffff";
      context.font = "600 13px sans-serif";
      context.fillText(labels[index], x + 22, y + tileSize - 20);
    }
    return await new Promise((resolve, reject) => {
      sheet.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error("The browser could not encode the turnaround sheet.")),
        "image/png",
      );
    });
  } finally {
    scene.background = previousBackground;
    renderer.setClearColor(previousClearColor, previousClearAlpha);
    renderer.setPixelRatio(previousPixelRatio);
    renderer.setSize(previousSize.x, previousSize.y, false);
    camera.position.copy(previousPosition);
    camera.quaternion.copy(previousQuaternion);
    camera.aspect = previousAspect;
    camera.updateProjectionMatrix();
    controls.target.copy(previousTarget);
    controls.enabled = previousControlsEnabled;
    controls.update();
    previewFrozen = false;
    renderer.render(scene, camera);
  }
}

export async function exportCharacterPreview({ width = 1024, transparent = true } = {}) {
  if (!renderer || !currentObject || !camera || !scene) {
    throw new Error("Load a character preview before exporting a PNG.");
  }
  const size = Math.max(256, Math.min(4096, Math.round(Number(width) || 1024)));
  const previousSize = renderer.getSize(new THREE.Vector2());
  const previousPixelRatio = renderer.getPixelRatio();
  const previousAspect = camera.aspect;
  const previousBackground = scene.background;
  const previousClearColor = renderer.getClearColor(new THREE.Color()).clone();
  const previousClearAlpha = renderer.getClearAlpha();
  try {
    renderer.setPixelRatio(1);
    renderer.setSize(size, size, false);
    camera.aspect = 1;
    camera.updateProjectionMatrix();
    if (transparent) {
      scene.background = null;
      renderer.setClearColor(0x000000, 0);
    }
    renderer.render(scene, camera);
    const blobPromise = new Promise((resolve, reject) => {
      renderer.domElement.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error("The browser could not encode the character PNG.")),
        "image/png",
      );
    });
    return await blobPromise;
  } finally {
    scene.background = previousBackground;
    renderer.setClearColor(previousClearColor, previousClearAlpha);
    renderer.setPixelRatio(previousPixelRatio);
    renderer.setSize(previousSize.x, previousSize.y, false);
    camera.aspect = previousAspect;
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  }
}

resetButton.addEventListener("click", resetCharacterPreview);
playbackButton.addEventListener("click", () => setPlaybackPaused(!playbackPaused));
playbackSpeed.addEventListener("change", () => {
  if (mixer) mixer.timeScale = Number(playbackSpeed.value) || 1;
});
frameButtons.forEach((button) => button.addEventListener("click", () => frameCharacter(button.dataset.cameraFrame)));
animationSelect.addEventListener("change", () => {
  if (!mixer) return;
  mixer.stopAllAction();
  const index = Number(animationSelect.value);
  activeAction = Number.isInteger(index) && clips[index] ? mixer.clipAction(clips[index]) : null;
  playbackPaused = false;
  if (activeAction) {
    activeAction.reset().play();
    mixer.timeScale = Number(playbackSpeed.value) || 1;
  }
  updatePlaybackControls();
});

export async function showRetargetPreview(sourceBuffer, targetBuffer, sourceMapping, targetMapping, animationName, label = "Retargeted character") {
  canvas.style.display = "block";
  if (!ensureRenderer()) return false;
  status.textContent = "Preparing browser retarget preview…";
  try {
    const [sourceGltf, targetGltf] = await Promise.all([loader.parseAsync(sourceBuffer, ""), loader.parseAsync(targetBuffer, "")]);
    const requestedAnimation = String(animationName || "").trim();
    const clip = resolveAnimationClip(sourceGltf.animations, requestedAnimation);
    if (!clip) {
      throw new Error(
        requestedAnimation
          ? 'The selected source animation "' + requestedAnimation + '" is unavailable in the GLB; no substitute clip was previewed.'
          : "The source GLB contains no playable animation clips."
      );
    }
    const { targetMesh, retargetedClip } = prepareRetargetedClip(
      sourceGltf.scene,
      targetGltf.scene,
      sourceMapping,
      targetMapping,
      clip,
      retargetClip,
    );
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
    characterBounds = bounds.clone();
    characterBounds.min.sub(center);
    characterBounds.max.sub(center);
    frameCharacter("full");
    clips = [retargetedClip];
    mixer = new THREE.AnimationMixer(targetMesh);
    activeAction = mixer.clipAction(retargetedClip);
    activeAction.play();
    playbackPaused = false;
    mixer.timeScale = Number(playbackSpeed.value) || 1;
    updatePlaybackControls();
    animationSelect.replaceChildren();
    const option = document.createElement("option");
    option.value = "0";
    option.textContent = retargetedClip.name || "Retargeted " + clip.name;
    animationSelect.append(option);
    animationSelect.disabled = true;
    empty.hidden = true;
    resetButton.disabled = false;
    status.textContent = label + " · " + clip.name + " · browser preview only; saved Godot scene remains authoritative.";
    return true;
  } catch (error) {
    status.textContent = "Retarget preview unavailable: " + error.message;
    return false;
  }
}
