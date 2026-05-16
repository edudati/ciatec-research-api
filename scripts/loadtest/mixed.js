/**
 * Mixed load: telemetry bursts + light API reads.
 *
 * Prereqs: k6, env BASE_URL (e.g. https://api.ciatec.org), TOKEN (Bearer JWT for a test user).
 *
 * Acceptance (adjust to your SLO):
 * - p95 of tagged "light" requests should not regress beyond baseline when telemetry_weight > 0.
 * - Run twice: BASELINE (telemetry_weight=0) vs LOAD (telemetry_weight=0.5), compare http_req_duration{group:light}.
 *
 * Example:
 *   k6 run -e BASE_URL=http://localhost:8000 -e TOKEN=eyJ... scripts/loadtest/mixed.js
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";

const lightLatency = new Trend("light_p95_helper");
const failRate = new Rate("checks_failed");

export const options = {
  scenarios: {
    mixed: {
      executor: "constant-vus",
      vus: 10,
      duration: "2m",
    },
  },
  thresholds: {
    checks_failed: ["rate<0.05"],
  },
};

const base = __ENV.BASE_URL || "http://localhost:8000";
const token = __ENV.TOKEN || "";
const telemetryWeight = parseFloat(__ENV.TELEMETRY_WEIGHT || "0.3");

const headers = {
  "Content-Type": "application/json",
  Authorization: token ? `Bearer ${token}` : "",
};

function pickTelemetryPath() {
  const id = __ENV.MATCH_ID || "00000000-0000-0000-0000-000000000001";
  const games = ["trunktilt", "bubbles", "bestbeat"];
  const g = games[Math.floor(Math.random() * games.length)];
  const kind = Math.random() < 0.5 ? "world" : "pose";
  return `${base}/api/v1/${g}/matches/${id}/telemetry/${kind}`;
}

function telemetryBody() {
  return JSON.stringify({
    frames: [{ frame_id: 0, ball_x: 1.0 }],
  });
}

export default function () {
  if (Math.random() < telemetryWeight && token) {
    const res = http.post(pickTelemetryPath(), telemetryBody(), { headers });
    failRate.add(!check(res, { "telemetry status": (r) => r.status === 200 || r.status === 201 || r.status === 202 || r.status === 403 || r.status === 404 || r.status === 409 }));
  } else {
    const res = http.get(`${base}/health`, { tags: { group: "light" } });
    lightLatency.add(res.timings.duration);
    failRate.add(!check(res, { "health 200": (r) => r.status === 200 }));
  }
  sleep(0.2);
}
