const BODY_TOKENS = /body|torso|chest|waist|hip|shoulder|arm|leg|muscle|belly|stomach|height|breast|bust|thigh|calf|buttock/;
const FACE_TOKENS = /eye|gaze|iris|pupil|sclera|brow|lid|blink|squint|mouth|lip|jaw|cheek|nose|face|smile|frown|angry|sad|happy|surpris|tongue|teeth/;

function normalize(value) {
  return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}

export function classifyMorphTarget(target) {
  const name = normalize(target.name);
  if (BODY_TOKENS.test(name)) return "body";
  if (FACE_TOKENS.test(name)) return "face";
  const mesh = normalize(target.meshName);
  if (BODY_TOKENS.test(mesh)) return "body";
  if (FACE_TOKENS.test(mesh)) return "face";
  return "other";
}
