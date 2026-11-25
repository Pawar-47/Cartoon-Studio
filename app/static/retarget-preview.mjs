const HUMANOID_PROFILE_BONES = [
  "Hips", "Spine", "Head",
  "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
  "RightUpperLeg", "RightLowerLeg", "RightFoot",
  "LeftUpperArm", "LeftLowerArm", "LeftHand",
  "RightUpperArm", "RightLowerArm", "RightHand",
];

function firstSkinnedMesh(root) {
  let result = null;
  root?.traverse((node) => {
    if (!result && node.isSkinnedMesh && node.skeleton) result = node;
  });
  return result;
}

export function prepareRetargetedClip(
  sourceRoot,
  targetRoot,
  sourceMapping,
  targetMapping,
  sourceClip,
  retargetClip,
) {
  const sourceMesh = firstSkinnedMesh(sourceRoot);
  const targetMesh = firstSkinnedMesh(targetRoot);
  if (!sourceMesh || !targetMesh) {
    throw new Error("Both GLBs must contain a skinned humanoid mesh.");
  }
  if (typeof retargetClip !== "function") {
    throw new Error("The browser retarget engine is unavailable.");
  }

  const sourceBones = new Set(sourceMesh.skeleton.bones.map((bone) => bone.name));
  const targetBones = new Set(targetMesh.skeleton.bones.map((bone) => bone.name));
  const names = {};
  const usedSourceNames = new Set();
  const usedTargetNames = new Set();

  for (const profileName of HUMANOID_PROFILE_BONES) {
    const sourceName = sourceMapping?.[profileName];
    const targetName = targetMapping?.[profileName];
    if (typeof sourceName !== "string" || !sourceName || !sourceBones.has(sourceName)) {
      throw new Error("The source rig is missing its mapped " + profileName + " bone.");
    }
    if (typeof targetName !== "string" || !targetName || !targetBones.has(targetName)) {
      throw new Error("The target rig is missing its mapped " + profileName + " bone.");
    }
    if (usedSourceNames.has(sourceName) || usedTargetNames.has(targetName)) {
      throw new Error("The saved humanoid mapping contains duplicate bone assignments.");
    }
    usedSourceNames.add(sourceName);
    usedTargetNames.add(targetName);
    names[targetName] = sourceName;
  }

  // Animation tracks target nodes under the GLTF scene root, not necessarily under
  // the SkinnedMesh node. Attach the imported skeleton to each root for sampling.
  sourceRoot.skeleton = sourceMesh.skeleton;
  targetRoot.skeleton = targetMesh.skeleton;
  const retargetedClip = retargetClip(targetRoot, sourceRoot, sourceClip, {
    names,
    hip: sourceMapping.Hips,
    preserveBoneMatrix: true,
    preserveBonePositions: true,
  });
  if (!retargetedClip || !retargetedClip.tracks.length) {
    throw new Error("Three.js could not produce a retargeted animation clip.");
  }
  return { sourceMesh, targetMesh, retargetedClip };
}
