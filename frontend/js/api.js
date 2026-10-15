/**
 * AEGIS LLM GATEWAY - BACKEND API CLIENT
 * Centralizes all network communication with FastAPI endpoints
 */

import { API_BASE } from './config.js';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return await res.json();
}

export async function sendChatPrompt(prompt) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
    throw new Error(err.detail || "Server error executing chat");
  }

  return await res.json();
}

export async function fetchKeys() {
  const res = await fetch(`${API_BASE}/api/keys`);
  if (!res.ok) throw new Error("Failed to load key configurations");
  return await res.json();
}

export async function testKey(provider, key = null, extra = {}) {
  const payload = { provider };
  if (key) payload.key = key;
  if (extra && Object.keys(extra).length > 0) payload.extra = extra;

  const res = await fetch(`${API_BASE}/api/keys/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json().catch(() => ({ valid: false, message: "Invalid response from server" }));
  if (!res.ok && !data.message) {
    throw new Error(data.detail || `Test failed with status ${res.status}`);
  }
  return data;
}

export async function saveKeys(provider, keys, extra = {}) {
  const res = await fetch(`${API_BASE}/api/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider,
      keys,
      extra
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Failed to save keys (${res.status})` }));
    throw new Error(err.detail || "Failed to save keys");
  }

  return await res.json();
}

export async function fetchMetrics(limit = 150) {
  const res = await fetch(`${API_BASE}/api/metrics?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to load telemetry records");
  return await res.json();
}
