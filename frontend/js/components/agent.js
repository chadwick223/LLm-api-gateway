/**
 * AEGIS LLM GATEWAY - AGENT PLAYGROUND & RUN CONTROLLER
 */

import { state } from '../config.js';
import { sendChatPrompt } from '../api.js';
import { showToast } from './toast.js';
import { parseAndRenderMarkdown } from '../utils/markdown.js';

let promptInput = null;
let btnRunAgent = null;
let userPromptDisplay = null;
let chatWorkspace = null;
let routeBadgePill = null;
let responseFormattedArea = null;
let responseRawContent = null;
let btnCopyResponse = null;
let btnToggleRaw = null;
let btnRawLabel = null;

let stepRoutingVal = null;
let stepModelVal = null;
let stepProviderSub = null;
let stepKeyVal = null;

let tileLatencyVal = null;
let tileTokensVal = null;
let tilePromptVal = null;
let tileCompVal = null;

export function initAgentPlayground() {
  promptInput = document.getElementById("prompt-input");
  btnRunAgent = document.getElementById("btn-run-agent");
  userPromptDisplay = document.getElementById("user-prompt-display");
  chatWorkspace = document.getElementById("chat-workspace");
  routeBadgePill = document.getElementById("route-badge-pill");
  responseFormattedArea = document.getElementById("response-formatted-area");
  responseRawContent = document.getElementById("response-raw-content");
  btnCopyResponse = document.getElementById("btn-copy-response");
  btnToggleRaw = document.getElementById("btn-toggle-raw");
  btnRawLabel = document.getElementById("btn-raw-label");

  stepRoutingVal = document.getElementById("step-routing-val");
  stepModelVal = document.getElementById("step-model-val");
  stepProviderSub = document.getElementById("step-provider-sub");
  stepKeyVal = document.getElementById("step-key-val");

  tileLatencyVal = document.getElementById("tile-latency-val");
  tileTokensVal = document.getElementById("tile-tokens-val");
  tilePromptVal = document.getElementById("tile-prompt-val");
  tileCompVal = document.getElementById("tile-comp-val");

  if (!btnRunAgent || !promptInput) return;

  // Preset pill click triggers
  document.querySelectorAll(".preset-pill-tag").forEach((tag) => {
    tag.addEventListener("click", () => {
      promptInput.value = tag.dataset.prompt;
      autoResizePrompt();
      promptInput.focus();
    });
  });

  // Keep textarea height responsive to content
  promptInput.addEventListener("input", autoResizePrompt);

  // Keyboard shortcut: Enter to execute, Shift+Enter for newline
  promptInput.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.isComposing) return;
    if (e.shiftKey) return;
    e.preventDefault();
    executePrompt();
  });

  // Run Button Click
  btnRunAgent.addEventListener("click", executePrompt);

  // Copy Response Action
  if (btnCopyResponse) {
    btnCopyResponse.addEventListener("click", () => {
      if (!state.currentResponseData) {
        showToast("No response to copy.", "info");
        return;
      }
      const textToCopy = state.currentResponseData.raw || state.currentResponseData.text || "";
      navigator.clipboard.writeText(textToCopy);
      showToast("Response copied to clipboard!", "success");
    });
  }

  // Raw / Formatted Toggle Action
  if (btnToggleRaw) {
    btnToggleRaw.addEventListener("click", () => {
      state.isRawView = !state.isRawView;
      if (btnRawLabel) {
        btnRawLabel.textContent = state.isRawView ? "Formatted" : "Raw";
      }

      if (state.isRawView) {
        if (responseFormattedArea) responseFormattedArea.classList.add("hidden");
        if (responseRawContent) responseRawContent.classList.remove("hidden");
      } else {
        if (responseFormattedArea) responseFormattedArea.classList.remove("hidden");
        if (responseRawContent) responseRawContent.classList.add("hidden");
      }
    });
  }
}

export function autoResizePrompt() {
  if (!promptInput) return;
  promptInput.style.height = "auto";
  promptInput.style.height = Math.min(promptInput.scrollHeight, 200) + "px";
}

export function formatPromptPreview(prompt) {
  let preview = prompt.split("\n").slice(0, 6).join("\n");
  if (preview.length > 300) preview = preview.slice(0, 300);
  if (preview.length < prompt.length) preview = preview.trimEnd() + " …";
  return preview;
}

export async function executePrompt() {
  if (!btnRunAgent || btnRunAgent.disabled) return;

  const prompt = promptInput.value.trim();
  if (!prompt) {
    showToast("Please enter a prompt or select a preset.", "error");
    promptInput.focus();
    return;
  }

  // Update prompt preview bubble in chat column
  if (userPromptDisplay) {
    userPromptDisplay.textContent = formatPromptPreview(prompt);
  }

  // Set running UI state
  btnRunAgent.disabled = true;
  btnRunAgent.innerHTML = `<span>Routing...</span>`;
  if (stepRoutingVal) stepRoutingVal.textContent = "Classifying...";
  if (stepModelVal) stepModelVal.textContent = "Selecting...";
  if (stepProviderSub) stepProviderSub.textContent = "via gateway";
  if (stepKeyVal) stepKeyVal.textContent = "Rotating...";

  const startTime = performance.now();

  try {
    const data = await sendChatPrompt(prompt);
    const elapsedMs = Math.round(performance.now() - startTime);
    const elapsedSec = (elapsedMs / 1000).toFixed(1);

    state.currentResponseData = data;
    const rawText = data.text || (typeof data === "string" ? data : JSON.stringify(data, null, 2));
    state.currentResponseData.raw = rawText;

    // 1. Update Route Classification Badge
    const difficulty = (data.difficulty || "Easy").toLowerCase();
    if (routeBadgePill) {
      routeBadgePill.textContent = `${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)} route`;
      routeBadgePill.className = `route-badge ${difficulty === "medium" ? "medium" : ""}`;
    }

    // 2. Parse and render rich response
    parseAndRenderMarkdown(rawText, responseFormattedArea, responseRawContent);

    // Scroll chat workspace back to the top of response
    if (chatWorkspace) {
      chatWorkspace.scrollTop = 0;
    }

    // 3. Update Stepper Timeline
    if (stepRoutingVal) stepRoutingVal.textContent = `Classified ${difficulty}`;
    if (stepModelVal) stepModelVal.textContent = data.model || "gpt-oss-20b";
    if (stepProviderSub) stepProviderSub.textContent = `via ${data.provider || "groq"}`;
    if (stepKeyVal) stepKeyVal.textContent = `Key ${data.key_index !== undefined ? data.key_index : 0}, rotated`;

    // 4. Update 2x2 Metric Tiles
    if (tileLatencyVal) {
      tileLatencyVal.textContent = `${data.duration_ms ? (data.duration_ms / 1000).toFixed(1) : elapsedSec} s`;
    }
    const promptTok = data.prompt_tokens || 0;
    const compTok = data.completion_tokens || 0;
    if (tileTokensVal) tileTokensVal.textContent = promptTok + compTok;
    if (tilePromptVal) tilePromptVal.textContent = promptTok;
    if (tileCompVal) tileCompVal.textContent = compTok;

    showToast(`Task executed successfully via ${data.provider || 'gateway'}!`, "success");

  } catch (err) {
    showToast(`Execution failed: ${err.message}`, "error");
    if (stepRoutingVal) stepRoutingVal.textContent = "Error";
    if (stepModelVal) stepModelVal.textContent = "Failed";
    if (stepProviderSub) stepProviderSub.textContent = "check logs";
  } finally {
    btnRunAgent.disabled = false;
    btnRunAgent.innerHTML = `<span>Run</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
  }
}
