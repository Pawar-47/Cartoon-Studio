import assert from "node:assert/strict";
import test from "node:test";
import {
  normalizeAnimationName,
  resolveAnimationClip,
  resolveDefaultAnimationClip,
} from "../app/static/animation-clip.mjs";

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

test("prefers an exact idle clip over other idle variants", () => {
  const previewClips = [
    { name: "Death" },
    { name: "Idle_Gun" },
    { name: "RobotArmature/Idle" },
    { name: "Idle_Neutral" },
  ];
  assert.equal(resolveDefaultAnimationClip(previewClips), previewClips[2]);
});

test("uses a named idle variant when no exact idle clip exists", () => {
  const previewClips = [{ name: "RESET" }, { name: "Death" }, { name: "Idle_Neutral" }];
  assert.equal(resolveDefaultAnimationClip(previewClips), previewClips[2]);
});

test("falls back to the first playable clip when no idle clip exists", () => {
  const previewClips = [{ name: "RESET" }, { name: "Walking" }, { name: "Running" }];
  assert.equal(resolveDefaultAnimationClip(previewClips), previewClips[1]);
});

test("returns no default when only the internal reset clip is available", () => {
  assert.equal(resolveDefaultAnimationClip([{ name: "RESET" }]), null);
});
