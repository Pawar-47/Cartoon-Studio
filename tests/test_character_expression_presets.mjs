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
test("RobotExpressive expression names map to supported presets", () => {
  assert.equal(buildExpressionPreset("smile", [{key:"h",name:"Happy",value:0}]).weights.h, 0.85);
  assert.equal(buildExpressionPreset("frown", [{key:"s",name:"Sad",value:0}]).weights.s, 0.85);
  assert.equal(buildExpressionPreset("surprise", [{key:"s",name:"Surprised",value:0}]).weights.s, 0.85);
  assert.equal(buildExpressionPreset("angry", [{key:"a",name:"Angry",value:0}]).weights.a, 0.85);
});
test("surprise preset matches jaw-open semantics", () => {
  const result = buildExpressionPreset("surprise", targets);
  assert.equal(result.weights["face:JawOpen"], 0.85);
  assert.deepEqual(result.matched, ["face:JawOpen"]);
});
test("unmatched shapes retain imported baseline values", () => {
  const result = buildExpressionPreset("smile", [{key:"x",name:"EyeBlink",value:0.37}]);
  assert.equal(result.weights.x, 0.37);
  assert.deepEqual(result.matched, []);
});
test("unknown presets fail explicitly", () => {
  assert.throws(() => buildExpressionPreset("laugh", targets), RangeError);
});
