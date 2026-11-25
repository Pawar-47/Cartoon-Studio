export function normalizeAnimationName(value) {
  return String(value ?? "")
    .trim()
    .split(/[|:]/)
    .pop()
    .split("/")
    .pop()
    .toLowerCase();
}

export function resolveAnimationClip(clips, requestedName = "") {
  const available = Array.isArray(clips) ? clips : [];
  const requested = String(requestedName ?? "").trim();
  if (!requested) {
    return available.find((clip) => normalizeAnimationName(clip?.name) !== "reset") ?? null;
  }
  if (normalizeAnimationName(requested) === "reset") return null;
  const exact = available.find((clip) => clip?.name === requested);
  if (exact) return exact;
  const normalized = normalizeAnimationName(requested);
  const matches = available.filter((clip) => normalizeAnimationName(clip?.name) === normalized);
  return matches.length === 1 ? matches[0] : null;
}

export function resolveDefaultAnimationClip(clips) {
  const available = Array.isArray(clips) ? clips : [];
  const exactIdle = available.find((clip) => normalizeAnimationName(clip?.name) === "idle");
  if (exactIdle) return exactIdle;

  const idleVariant = available.find((clip) =>
    /^idle(?:$|[_\s-])/i.test(normalizeAnimationName(clip?.name))
  );
  return idleVariant ?? resolveAnimationClip(available);
}
