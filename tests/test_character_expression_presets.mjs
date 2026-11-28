import test from "node:test";
import assert from "node:assert/strict";
import { buildExpressionPreset, buildGeneratedFaceExpression } from "../app/static/character-expression-presets.js";
import { classifyMorphTarget } from "../app/static/character-morph-groups.js";

const targets = [
  { key: "face:Smile", name: "Smile", meshName: "Face", value: 0 },
  { key: "face:JawOpen", name: "JawOpen", meshName: "Face", value: 0.1 },
  { key: "face:BrowDown", name: "BrowDown", meshName: "Face", value: 0 },
  { key: "face:EyeBlink", name: "EyeBlink", meshName: "Face", value: 0.2 },
];

test("smile changes matching shapes and leaves unrelated shapes at baseline", () => {
  const result = buildExpressionPreset("smile", targets);
  assert.equal(result.weights["face:Smile"], 0.85);
  assert.equal(result.weights["face:EyeBlink"], 0.2);
  assert.deepEqual(result.matched, ["face:Smile"]);
  assert.deepEqual(result.unmatched, ["face:JawOpen", "face:BrowDown", "face:EyeBlink"]);
});
test("surprise preset matches jaw-open semantics", () => {
  const result = buildExpressionPreset("surprise", targets);
  assert.equal(result.weights["face:JawOpen"], 0.85);
  assert.deepEqual(result.matched, ["face:JawOpen"]);
});
test("frown and angry presets classify their semantic names", () => {
  assert.equal(buildExpressionPreset("frown", [{key:"f",name:"Mouth_Frown",value:0}]).weights.f, 0.85);
  assert.equal(buildExpressionPreset("angry", [{key:"a",name:"Brow_Down_Left",value:0}]).weights.a, 0.85);
});
test("unmatched shapes retain imported baseline values", () => {
  const result = buildExpressionPreset("smile", [{key:"x",name:"EyeBlink",value:0.37}]);
  assert.equal(result.weights.x, 0.37);
  assert.deepEqual(result.matched, []);
});
test("unknown presets fail explicitly", () => {
  assert.throws(() => buildExpressionPreset("laugh", targets), RangeError);
});

test("morph classification prioritizes shape name over mesh name", () => {
  assert.equal(classifyMorphTarget({ name: "Body_Width", meshName: "BodyMesh" }), "body");
  assert.equal(classifyMorphTarget({ name: "Smile", meshName: "BodyMesh" }), "face");
  assert.equal(classifyMorphTarget({ name: "JawOpen", meshName: "HeadMesh" }), "face");
  assert.equal(classifyMorphTarget({ name: "Muscle", meshName: "Character" }), "body");
  assert.equal(classifyMorphTarget({ name: "UnknownShape", meshName: "Character" }), "other");
});

test("generated face smile preset enables face and sets a friendly expression", () => {
  const result = buildGeneratedFaceExpression("smile", { face_width: 1.12, smile: 0 });
  assert.equal(result.enabled, true);
  assert.equal(result.smile, 0.82);
  assert.equal(result.eye_scale, 1.08);
  assert.equal(result.face_width, 1.12);
});
test("generated face presets provide frown, surprise and angry expressions", () => {
  assert.equal(buildGeneratedFaceExpression("frown").smile, -0.78);
  assert.equal(buildGeneratedFaceExpression("surprise").eye_scale, 1.38);
  assert.equal(buildGeneratedFaceExpression("surprise").mouth_open, 0.82);
  assert.equal(buildGeneratedFaceExpression("angry").brow_angle, 0.42);
});
test("generated face preset rejects unknown names", () => {
  assert.throws(() => buildGeneratedFaceExpression("laugh"), RangeError);
});

test("Blender gaze and expression controls appear in the facial group", () => {
  for (const name of ["GazeLeft", "GazeRight", "GazeUp", "GazeDown", "EyesWide", "Squint", "BrowRaise", "BrowInnerDown", "BrowDown", "Frown"]) {
    assert.equal(classifyMorphTarget({ name, meshName: "CartoonStudioCharacterMesh" }), "face");
  }
});

test("Blender facial controls activate the matching expression presets", () => {
  const controls = [
    { key: "frown", name: "Frown", value: 0 },
    { key: "inner", name: "BrowInnerDown", value: 0 },
    { key: "raise", name: "BrowRaise", value: 0 },
    { key: "wide", name: "EyesWide", value: 0 },
    { key: "down", name: "BrowDown", value: 0 },
  ];
  const frown = buildExpressionPreset("frown", controls);
  assert.equal(frown.weights.frown, 0.85);
  assert.equal(frown.weights.inner, 0.85);
  const surprise = buildExpressionPreset("surprise", controls);
  assert.equal(surprise.weights.raise, 0.85);
  assert.equal(surprise.weights.wide, 0.85);
  const angry = buildExpressionPreset("angry", controls);
  assert.equal(angry.weights.down, 0.85);
});
