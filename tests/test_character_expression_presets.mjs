import test from "node:test";
import assert from "node:assert/strict";
import { buildExpressionPreset } from "../app/static/character-expression-presets.js";

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
