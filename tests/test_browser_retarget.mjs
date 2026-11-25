import assert from "node:assert/strict";
import test from "node:test";
import * as THREE from "../app/static/vendor/three/build/three.module.js";
import { readFile } from "node:fs/promises";
import { prepareRetargetedClip } from "../app/static/retarget-preview.mjs";

const profileParents = {
  Hips: null,
  Spine: "Hips",
  Head: "Spine",
  LeftUpperLeg: "Hips",
  LeftLowerLeg: "LeftUpperLeg",
  LeftFoot: "LeftLowerLeg",
  RightUpperLeg: "Hips",
  RightLowerLeg: "RightUpperLeg",
  RightFoot: "RightLowerLeg",
  LeftUpperArm: "Spine",
  LeftLowerArm: "LeftUpperArm",
  LeftHand: "LeftLowerArm",
  RightUpperArm: "Spine",
  RightLowerArm: "RightUpperArm",
  RightHand: "RightLowerArm",
};

function createRig(prefix, roll = 0) {
  const root = new THREE.Group();
  const armature = new THREE.Group();
  root.add(armature);
  const bones = {};
  for (const [profileName, parentName] of Object.entries(profileParents)) {
    const bone = new THREE.Bone();
    bone.name = prefix + profileName;
    if (profileName === "Spine") bone.position.y = 1;
    if (profileName === "Head") bone.position.y = 1;
    if (profileName.endsWith("UpperLeg")) {
      bone.position.set(profileName.startsWith("Left") ? 0.2 : -0.2, -0.5, 0);
    }
    if (profileName.endsWith("LowerLeg") || profileName.endsWith("Foot")) {
      bone.position.y = -0.5;
    }
    if (profileName.endsWith("UpperArm")) {
      bone.position.set(profileName.startsWith("Left") ? 0.4 : -0.4, 0.8, 0);
    }
    if (profileName.endsWith("LowerArm") || profileName.endsWith("Hand")) {
      bone.position.x = profileName.startsWith("Left") ? 0.5 : -0.5;
    }
    if (profileName === "LeftUpperArm") bone.rotation.z = roll;
    if (parentName) bones[parentName].add(bone);
    else armature.add(bone);
    bones[profileName] = bone;
  }
  const mesh = new THREE.SkinnedMesh(
    new THREE.BufferGeometry(),
    new THREE.MeshBasicMaterial(),
  );
  root.add(mesh);
  root.updateMatrixWorld(true);
  mesh.bind(new THREE.Skeleton(Object.values(bones)));
  root.skeleton = mesh.skeleton;
  root.updateMatrixWorld(true);
  return { root, mesh, bones };
}

const sourceMapping = Object.fromEntries(
  Object.keys(profileParents).map((name) => [name, "src_" + name]),
);
const targetMapping = Object.fromEntries(
  Object.keys(profileParents).map((name) => [name, "dst_" + name]),
);

const skeletonUtilsSource = await readFile(
  new URL("../app/static/vendor/three/examples/jsm/utils/SkeletonUtils.js", import.meta.url),
  "utf8",
);
const threeModuleUrl = new URL(
  "../app/static/vendor/three/build/three.module.js",
  import.meta.url,
).href;
const nodeCompatibleSource = skeletonUtilsSource.replace(
  "from 'three';",
  "from '" + threeModuleUrl + "';",
);
const skeletonUtilsUrl = "data:text/javascript;base64," +
  Buffer.from(nodeCompatibleSource).toString("base64");
const { retargetClip } = await import(skeletonUtilsUrl);

test("retargets scene-root animation tracks onto a sibling target skeleton", () => {
  const source = createRig("src_");
  const target = createRig("dst_", 0.24);
  const armRotation = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(0, 0, 1),
    0.7,
  );
  const clip = new THREE.AnimationClip("Walking", 1, [
    new THREE.VectorKeyframeTrack(
      "src_Hips.position",
      [0, 1],
      [0, 0, 0, 0, 0.25, 0],
    ),
    new THREE.QuaternionKeyframeTrack(
      "src_LeftUpperArm.quaternion",
      [0, 1],
      [0, 0, 0, 1, ...armRotation.toArray()],
    ),
  ]);

  const prepared = prepareRetargetedClip(
    source.root,
    target.root,
    sourceMapping,
    targetMapping,
    clip,
    retargetClip,
  );
  assert.equal(prepared.targetMesh, target.mesh);
  assert.ok(prepared.retargetedClip.tracks.some(
    (track) => track.name === ".bones[dst_LeftUpperArm].quaternion",
  ));
  assert.ok(prepared.retargetedClip.tracks.some(
    (track) => track.name === ".bones[dst_Hips].position",
  ));

  const mixer = new THREE.AnimationMixer(prepared.targetMesh);
  mixer.clipAction(prepared.retargetedClip).play();
  mixer.update(0.5);
  assert.ok(target.bones.LeftUpperArm.quaternion.angleTo(
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), 0.35),
  ) < 0.35);
  assert.ok(target.bones.Hips.position.y > 0.01);
});

test("rejects incomplete and duplicate humanoid mappings before retargeting", () => {
  const source = createRig("src_");
  const target = createRig("dst_");
  const clip = new THREE.AnimationClip("Idle", 1, [
    new THREE.QuaternionKeyframeTrack(
      "src_LeftUpperArm.quaternion",
      [0, 1],
      [0, 0, 0, 1, 0, 0, 0, 1],
    ),
  ]);
  const incomplete = { ...sourceMapping };
  delete incomplete.LeftHand;
  assert.throws(
    () => prepareRetargetedClip(
      source.root, target.root, incomplete, targetMapping, clip, retargetClip,
    ),
    /missing its mapped LeftHand bone/,
  );
  const duplicate = { ...sourceMapping, LeftHand: sourceMapping.LeftLowerArm };
  assert.throws(
    () => prepareRetargetedClip(
      source.root, target.root, duplicate, targetMapping, clip, retargetClip,
    ),
    /duplicate bone assignments/,
  );
});
