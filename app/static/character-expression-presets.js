const PRESET_TOKENS = Object.freeze({
  smile: /smile|happy|grin|mouthup/,
  frown: /frown|sad|unhappy|mouthdown|browinnerdown/,
  surprise: /surpris|shocked|jawopen|mouthopen|eyeswide|browinnerup|browraise/,
  angry: /angry|scowl|mad|browdown|browlower/,
});

export function buildExpressionPreset(name, targets) {
  if (!Object.hasOwn(PRESET_TOKENS, name)) throw new RangeError("Unknown facial expression preset: " + name);
  const matcher = PRESET_TOKENS[name], weights = {}, matched = [], unmatched = [];
  for (const target of targets) {
    const identity = (String(target.name || "") + " " + String(target.meshName || "")).toLowerCase().replace(/[^a-z0-9]+/g, "");
    const isMatch = matcher.test(identity);
    weights[target.key] = isMatch ? 0.85 : Number(target.value ?? 0);
    (isMatch ? matched : unmatched).push(target.key);
  }
  return { weights, matched, unmatched };
}
