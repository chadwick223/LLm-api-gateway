/**
 * AEGIS LLM GATEWAY - APPLICATION CONFIG & STATE
 */

export const API_BASE = "";

export const PROVIDER_NAMES = {
  groq: "Groq",
  gemini: "Gemini",
  cloudflare: "Cloudflare",
  nvidia: "Nvidia",
  ollama: "Ollama"
};

export const PROVIDER_DESCRIPTIONS = {
  groq: "GPT-OSS 20B and 120B, Qwen",
  gemini: "Flash-Lite and Flash models",
  cloudflare: "Workers AI, Qwen and GLM",
  nvidia: "NIM, Nemotron 3 models",
  ollama: "Self-hosted, OpenAI-compatible"
};

// Global Reactive State
export const state = {
  currentTab: "agent",
  isRawView: false,
  currentResponseData: null,
  keyStatusData: null,
  allTelemetryRecords: [],
  activeTelemetryFilter: "all", // 'all', 'success', 'error'
  activeProviderFilter: "all",
  telemetrySearchQuery: "",
  telemetryPageSize: 7,
  activeModalProvider: null
};
