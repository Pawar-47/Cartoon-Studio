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
  const frontDirection = detectCharacterFaceDirection(center);
  const direction = new THREE.Vector3(0.9, 0.65, 1.15 * frontDirection).normalize();
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
function removeFaceFeaturePreview() {
  if (!faceFeatureGroup || !currentObject) return;
  currentObject.remove(faceFeatureGroup);
  faceFeatureGroup.traverse((node) => {
    node.geometry?.dispose();
    if (node.material) (Array.isArray(node.material) ? node.material : [node.material]).forEach((material) => material.dispose());
  });
  faceFeatureGroup = null;
}

function boxInCharacterSpace(worldBox) {
  const points = [];
  for (const x of [worldBox.min.x, worldBox.max.x]) {
    for (const y of [worldBox.min.y, worldBox.max.y]) {
      for (const z of [worldBox.min.z, worldBox.max.z]) {
        points.push(currentObject.worldToLocal(new THREE.Vector3(x, y, z)));
      }
    }
  }
  return new THREE.Box3().setFromPoints(points);
}

function detectCharacterFaceDirection(headCenter) {
  const featureTokens = ["eye", "brow", "mouth", "lip", "face"];
  let featureZ = 0;
  let featureSamples = 0;
  const vertex = new THREE.Vector3();
  currentObject.traverse((node) => {
    if (!node.isMesh || !node.geometry?.attributes?.position) return;
    const geometry = node.geometry;
    const index = geometry.index;
    const vertexCount = index ? index.count : geometry.attributes.position.count;
    const groups = geometry.groups.length ? geometry.groups : [{ start: 0, count: vertexCount, materialIndex: 0 }];
    for (const group of groups) {
      const material = Array.isArray(node.material) ? node.material[group.materialIndex] : node.material;
      const label = [geometry.name, material?.name].filter(Boolean).join(" ").toLowerCase();
      if (!featureTokens.some((token) => label.includes(token))) continue;
      const start = Math.max(0, group.start || 0);
      const end = Math.min(vertexCount, start + (group.count ?? vertexCount));
      const stride = Math.max(1, Math.floor((end - start) / 256));
      for (let offset = start; offset < end; offset += stride) {
        const vertexIndex = index ? index.getX(offset) : offset;
        if (typeof node.getVertexPosition === "function") node.getVertexPosition(vertexIndex, vertex);
        else vertex.fromBufferAttribute(geometry.attributes.position, vertexIndex);
        node.localToWorld(vertex);
        currentObject.worldToLocal(vertex);
        featureZ += vertex.z;
        featureSamples += 1;
      }
    }
  });
  if (!featureSamples) return 1;
  return featureZ / featureSamples >= headCenter.z ? 1 : -1;
}

export function applyCharacterFaceFeatures(recipe = {}) {
  if (!currentObject) return false;
  removeFaceFeaturePreview();
  if (!recipe.enabled) return true;
  currentObject.updateMatrixWorld(true);
  const worldBounds = new THREE.Box3().setFromObject(currentObject);
  if (worldBounds.isEmpty()) return false;
  let head = null;
  currentObject.traverse((node) => {
    if (!node.isMesh || !/(head|face|skull)/i.test(node.name || "")) return;
    const worldBox = new THREE.Box3().setFromObject(node);
    const box = worldBox.isEmpty() ? null : boxInCharacterSpace(worldBox);
    if (box && (!head || box.getSize(new THREE.Vector3()).y > head.getSize(new THREE.Vector3()).y)) head = box;
  });
  if (!head) {
    const bounds = boxInCharacterSpace(worldBounds);
    const size = bounds.getSize(new THREE.Vector3());
    head = new THREE.Box3(new THREE.Vector3(bounds.min.x,bounds.max.y-size.y*0.24,bounds.max.z-size.z*0.28),bounds.max.clone());
  }
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
  const frontDirection=detectCharacterFaceDirection(center);
  const front=(frontDirection>0?head.max.z:head.min.z)+frontDirection*Math.max(size.z*0.035,width*0.025);
  const eyeScale=THREE.MathUtils.clamp(Number(recipe.eye_scale??1),0.65,1.5);
  const spacing=THREE.MathUtils.clamp(Number(recipe.eye_spacing??1),0.65,1.35);
  const smile=THREE.MathUtils.clamp(Number(recipe.smile??0.35),-1,1);
  const mouthOpen=THREE.MathUtils.clamp(Number(recipe.mouth_open??0),0,1);
  const browAngle=THREE.MathUtils.clamp(Number(recipe.brow_angle??0),-0.5,0.5);
  const depth=Math.max(width*0.045,0.008);
  const group=new THREE.Group();group.name="CartoonStudioFacePreview";
  const mat=(color,roughness=0.72)=>new THREE.MeshStandardMaterial({color:color||"#ffffff",roughness,metalness:0,depthTest:false,depthWrite:false});
  const ellipsoid=(name,color,pos,scale,roughness=0.72)=>{
    const mesh=new THREE.Mesh(new THREE.SphereGeometry(1,20,14),mat(color,roughness));
    mesh.name=name;mesh.position.copy(pos);mesh.scale.set(scale.x,scale.y,scale.z);mesh.renderOrder=30;group.add(mesh);return mesh;
  };
  const eyeY=center.y+height*0.10, offset=width*0.245*spacing, ew=width*0.105*eyeScale, eh=height*0.17*eyeScale;
  const skinColor=recipe.skin_color||recipe.nose_color||"#c98768";
  for(const side of [-1,1]){
    ellipsoid("FaceEar",skinColor,new THREE.Vector3(center.x+side*size.x*0.43,center.y-height*0.02,front+frontDirection*depth*0.08),new THREE.Vector3(width*0.075*earSize,height*0.14*earSize,depth*0.72*earSize));
  }
  for(const side of [-1,1]){
    ellipsoid("FaceEarInner","#a96859",new THREE.Vector3(center.x+side*size.x*0.43,center.y-height*0.02,front+frontDirection*depth*0.69),new THREE.Vector3(width*0.027*earSize,height*0.085*earSize,depth*0.19*earSize));
  }
  for(const side of [-1,1]){
    const x=center.x+side*offset;
    ellipsoid("FaceEyeWhite",recipe.eye_color,new THREE.Vector3(x,eyeY,front),new THREE.Vector3(ew,eh,depth));
    ellipsoid("FaceIris",recipe.iris_color,new THREE.Vector3(x+width*0.018,eyeY-height*0.012,front+frontDirection*depth*0.88),new THREE.Vector3(ew*0.49,eh*0.57,depth*0.42),0.35);
    ellipsoid("FacePupil","#17191d",new THREE.Vector3(x+width*0.022,eyeY-height*0.012,front+frontDirection*depth*1.22),new THREE.Vector3(ew*0.23,eh*0.34,depth*0.22),0.25);
    const brow=ellipsoid("FaceEyebrow",recipe.brow_color,new THREE.Vector3(x,eyeY+eh*1.55,front+frontDirection*depth*0.12),new THREE.Vector3(ew*1.32,Math.max(height*0.035,0.006),depth*0.38));
    brow.rotation.z=-side*browAngle;
  }
  for(const side of [-1,1]){
    ellipsoid("FaceCheek",skinColor,new THREE.Vector3(center.x+side*width*0.255*jawWidth,center.y-height*0.19,front+frontDirection*depth*0.35),new THREE.Vector3(width*0.085*cheekFullness,height*0.065*cheekFullness,depth*0.62));
    ellipsoid("FaceJaw",skinColor,new THREE.Vector3(center.x+side*width*0.17*jawWidth,center.y-height*0.34,front+frontDirection*depth*0.24),new THREE.Vector3(width*0.115*jawWidth,height*0.075,depth*0.55));
  }
  ellipsoid("FaceChin",skinColor,new THREE.Vector3(center.x,center.y-height*(0.405+(chinLength-1)*0.025),front+frontDirection*depth*0.24),new THREE.Vector3(width*0.13*jawWidth,height*0.06*chinLength,depth*0.62));
  ellipsoid("FaceNoseBridge",recipe.nose_color,new THREE.Vector3(center.x,center.y-height*0.015,front+frontDirection*depth*0.48),new THREE.Vector3(width*0.035*noseWidth,height*0.09*noseHeight,depth*0.72));
  ellipsoid("FaceNose",recipe.nose_color,new THREE.Vector3(center.x,center.y-height*0.08,front+frontDirection*depth*0.6),new THREE.Vector3(width*0.055*noseWidth,height*0.075*noseHeight,depth*0.8));
  for(const side of [-1,1]){
    ellipsoid("FaceNostril","#633e36",new THREE.Vector3(center.x+side*width*0.027*noseWidth,center.y-height*0.112*noseHeight,front+frontDirection*depth*1.18),new THREE.Vector3(width*0.016*noseWidth,height*0.018*noseHeight,depth*0.19));
  }
  const my=center.y-height*0.30,mw=width*0.19*mouthWidth;
  if(mouthOpen>0.08){
    ellipsoid("FaceMouthOpening",recipe.mouth_color,new THREE.Vector3(center.x,my,front+frontDirection*depth*0.58),new THREE.Vector3(mw,height*(0.018+mouthOpen*0.11),depth*0.62));
    if(mouthOpen>0.45)ellipsoid("FaceMouthTongue","#c65f72",new THREE.Vector3(center.x,my-height*0.035,front+frontDirection*depth*1.08),new THREE.Vector3(mw*0.52,height*0.025,depth*0.2));
  }else{
    const curve=new THREE.CatmullRomCurve3([
      new THREE.Vector3(center.x-mw,my+smile*height*0.075,front+frontDirection*depth*0.5),
      new THREE.Vector3(center.x-mw*0.5,my-smile*height*0.07,front+frontDirection*depth*0.55),
      new THREE.Vector3(center.x+mw*0.5,my-smile*height*0.07,front+frontDirection*depth*0.55),
      new THREE.Vector3(center.x+mw,my+smile*height*0.075,front+frontDirection*depth*0.5),
    ]);
    const mouth=new THREE.Mesh(new THREE.TubeGeometry(curve,20,Math.max(width*0.012,0.003),8,false),mat(recipe.mouth_color));
    mouth.name="FaceMouth";mouth.renderOrder=31;group.add(mouth);
  }
  currentObject.add(group);faceFeatureGroup=group;return true;
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

async function parseCharacterGlb(buffer, timeoutMs = 45_000) {
  let timer;
  try {
    return await Promise.race([
      loader.parseAsync(buffer, ""),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error("GLB parsing exceeded " + timeoutMs / 1000 + " seconds.")), timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export async function showCharacterPreview(buffer, label = "Character", appearance = {}, options = {}) {
  const playAnimations = options.playAnimations !== false;
  canvas.style.display = "block";
  if (!ensureRenderer()) return false;
  status.textContent = "Loading 3D model…";
  try {
    // Release the previous model before parsing its replacement. Keeping both
    // scenes alive during GLB parsing can double peak CPU/GPU memory in the
    // browser, especially when a saved character is edited repeatedly.
    disposeCurrentObject();
    const gltf = await parseCharacterGlb(buffer);
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
  const labels = ["Front 3/4", "Side", "Back 3/4", "Opposite side"];
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
