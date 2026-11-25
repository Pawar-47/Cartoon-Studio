import assert from "node:assert/strict";
import test from "node:test";
import * as THREE from "../app/static/vendor/three/build/three.module.js";
import { retargetClip } from "../app/static/vendor/three/examples/jsm/utils/SkeletonUtils.js";

function makeSkinnedMesh(rootName, armName) {
  const mesh = new THREE.SkinnedMesh(
    new THREE.BufferGeometry(),
    new THREE.MeshBasicMaterial()
  );
  const hips = new THREE.Bone();
  hips.name = rootName;
  const arm = new THREE.Bone();
  arm.name = armName;
  hips.add(arm);
  mesh.add(hips);
  mesh.bind(new THREE.Skeleton([hips, arm]));
  mesh.updateMatrixWorld(true);
  return mesh;
}

test("Three.js retargetClip maps a selected source clip to target bone names", () => {
  const source = makeSkinnedMesh("Hips", "LeftUpperArm");
  const target = makeSkinnedMesh("Hips", "LeftArm");
  const endRotation = new THREE.Quaternion().setFromAxisAngle(
    new THREE.Vector3(0, 0, 1),
    Math.PI / 2
  );
  const sourceTrack = new THREE.QuaternionKeyframeTrack(
    ".bones[LeftUpperArm].quaternion",
    [0, 1],
    [0, 0, 0, 1, endRotation.x, endRotation.y, endRotation.z, endRotation.w]
  );
  const sourceClip = new THREE.AnimationClip("Walking", 1, [sourceTrack]);
  const targetClip = retargetClip(target, source, sourceClip, {
    names: { Hips: "Hips", LeftArm: "LeftUpperArm" },
    hip: "Hips",
    fps: 30,
  });

  assert.equal(targetClip.name, "Walking");
  assert.ok(
    targetClip.tracks.some((track) => track.name.includes("LeftArm")),
    "retargeted clip must contain a track for the target arm name"
  );
  assert.ok(
    !targetClip.tracks.some((track) => track.name.includes("LeftUpperArm")),
    "retargeted clip must not retain the source arm name"
  );

  const mixer = new THREE.AnimationMixer(target);
  mixer.clipAction(targetClip).play();
  mixer.update(0.5);
  const targetArm = target.skeleton.getBoneByName("LeftArm");
  assert.ok(
    targetArm.quaternion.angleTo(new THREE.Quaternion()) > 0.1,
    "the target arm must receive the selected source animation pose"
  );
});
