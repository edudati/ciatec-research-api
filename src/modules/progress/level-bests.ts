import type { Prisma } from '@prisma/client';

type Json = Prisma.JsonValue;

function toRecord(bests: Json | null | undefined): Record<string, number> {
  if (bests === null || typeof bests === 'string') {
    return {};
  }
  if (typeof bests !== 'object' || Array.isArray(bests)) {
    return {};
  }
  const o = bests as Record<string, unknown>;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(o)) {
    if (typeof v === 'number' && Number.isFinite(v)) {
      out[k] = v;
    }
  }
  return out;
}

/**
 * Merges match outcome into per-level bests. Strategy: score and generic metrics favor higher; keys that look like time/reaction/duration use lower.
 */
function isLowerIsBetterKey(key: string): boolean {
  const k = key.toLowerCase();
  return k.includes('time') || k.includes('reaction') || k.includes('duration') || k.endsWith('ms');
}

export function mergeLevelBests(
  previous: Json,
  input: { score: number; durationMs: number; extra?: Record<string, unknown> },
): Prisma.JsonObject {
  const prev = toRecord(previous);
  const out: Record<string, number> = { ...prev };

  if (out.score == null) {
    out.score = input.score;
  } else {
    out.score = Math.max(out.score, input.score);
  }

  const timeCandidate = input.durationMs;
  if (out.timeMs == null) {
    out.timeMs = timeCandidate;
  } else {
    out.timeMs = Math.min(out.timeMs, timeCandidate);
  }

  for (const [key, value] of Object.entries(input.extra ?? {})) {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      continue;
    }
    if (isLowerIsBetterKey(key)) {
      const current = out[key];
      if (current == null) {
        out[key] = value;
      } else {
        out[key] = Math.min(current, value);
      }
    } else {
      const current = out[key];
      if (current == null) {
        out[key] = value;
      } else {
        out[key] = Math.max(current, value);
      }
    }
  }

  return out as Prisma.JsonObject;
}
