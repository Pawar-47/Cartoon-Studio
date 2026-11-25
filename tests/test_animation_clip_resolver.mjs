import assert from "node:assert/strict";
import test from "node:test";
import { normalizeAnimationName, resolveAnimationClip } from "../app/static/animation-clip.mjs";

const clips = [
  { name: "RESET" },
  { name: "Idle" },
  { name: "Walking" },
  { name: "Running" },
];

test("matches an exact imported clip name", () => {
  assert.equal(resolveAnimationClip(clips, "Running"), clips[3]);
});

test("matches a Godot AnimationLibrary-prefixed clip name", () => {
  assert.equal(resolveAnimationClip(clips, "RobotArmature/Walking"), clips[2]);
});

test("normalizes case and preserves the actual clip object", () => {
  assert.equal(normalizeAnimationName("RobotArmature/Walking"), "walking");
  assert.equal(resolveAnimationClip(clips, "walking"), clips[2]);
});

test("does not substitute another clip for an unknown saved name", () => {
  assert.equal(resolveAnimationClip(clips, "Dance"), null);
});

test("uses the first playable clip only when no name was saved", () => {
  assert.equal(resolveAnimationClip(clips), clips[1]);
  assert.equal(resolveAnimationClip(clips, ""), clips[1]);
});

test("never resolves the internal RESET track", () => {
  assert.equal(resolveAnimationClip(clips, "RESET"), null);
  assert.equal(resolveAnimationClip([{ name: "RESET" }]), null);
});

test("rejects ambiguous normalized names instead of guessing", () => {
  const ambiguous = [{ name: "Walking" }, { name: "RobotArmature/Walking" }];
  assert.equal(resolveAnimationClip(ambiguous, "Other/Walking"), null);
});
