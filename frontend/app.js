/**
 * AEGIS LLM GATEWAY - CLIENT APPLICATION LOGIC
 * Warm Linen & Forest Green Redesign matching reference mockups
 */

const API_BASE = "";

// State
let currentTab = "agent";
let isRawView = false;
let currentResponseData = null;
let keyStatusData = null;
let allTelemetryRecords = [];
let activeTelemetryFilter = "all"; // 'all', 'success', 'error'
let activeProviderFilter = "all";
let telemetrySearchQuery = "";
let telemetryPageSize = 7;
let activeModalProvider = null;
let cooldownTickerInterval = null;

// DOM Elements - Global
const navTabs = document.getElementById("main-nav-tabs");
const tabAgent = document.getElementById("tab-agent");
const tabKeys = document.getElementById("tab-keys");
const tabTelemetry = document.getElementById("tab-telemetry");
const modelStatusPill = document.getElementById("model-status-pill");
const modelStatusText = document.getElementById("model-status-text");

// DOM Elements - Agent Tab
const userPromptDisplay = document.getElementById("user-prompt-display");
const promptInput = document.getElementById("prompt-input");
const btnRunAgent = document.getElementById("btn-run-agent");
const routeBadgePill = document.getElementById("route-badge-pill");
const responseScrollViewport = document.getElementById("response-scroll-viewport");
const responseFormattedArea = document.getElementById("response-formatted-area");
const responseRawContent = document.getElementById("response-raw-content");
const btnCopyResponse = document.getElementById("btn-copy-response");
const btnToggleExpand = document.getElementById("btn-toggle-expand");
const btnExpandLabel = document.getElementById("btn-expand-label");
const btnToggleRaw = document.getElementById("btn-toggle-raw");
const btnRawLabel = document.getElementById("btn-raw-label");

let isExpanded = false;

// Stepper & 2x2 Metric Tiles
const stepRoutingVal = document.getElementById("step-routing-val");
const stepModelVal = document.getElementById("step-model-val");
const stepProviderSub = document.getElementById("step-provider-sub");
const stepKeyVal = document.getElementById("step-key-val");
const tileLatencyVal = document.getElementById("tile-latency-val");
const tileTokensVal = document.getElementById("tile-tokens-val");
const tilePromptVal = document.getElementById("tile-prompt-val");
const tileCompVal = document.getElementById("tile-comp-val");

// DOM Elements - Keys Tab
const btnRefreshKeys = document.getElementById("btn-refresh-keys");
const statTotalKeys = document.getElementById("stat-total-keys");
const statReadyKeys = document.getElementById("stat-ready-keys");
const statCoolingKeys = document.getElementById("stat-cooling-keys");
const statDbStore = document.getElementById("stat-db-store");
const providersTableTbody = document.getElementById("providers-table-tbody");

// DOM Elements - Telemetry Tab
const btnRefreshTelemetry = document.getElementById("btn-refresh-telemetry");
const teleTotalCalls = document.getElementById("tele-total-calls");
const teleTodayCalls = document.getElementById("tele-today-calls");
const teleOkCalls = document.getElementById("tele-ok-calls");
const teleErrorCalls = document.getElementById("tele-error-calls");
const segBarGreen = document.getElementById("seg-bar-green");
const segBarCoral = document.getElementById("seg-bar-coral");
const segLabelSuccess = document.getElementById("seg-label-success");
const segLabelError = document.getElementById("seg-label-error");

const filterAllBtn = document.getElementById("filter-all-btn");
const filterSuccessBtn = document.getElementById("filter-success-btn");
const filterErrorsBtn = document.getElementById("filter-errors-btn");
const filterAllCount = document.getElementById("filter-all-count");
const filterSuccessCount = document.getElementById("filter-success-count");
const filterErrorsCount = document.getElementById("filter-errors-count");
const providerFilterSelect = document.getElementById("provider-filter-select");
const modelSearchInput = document.getElementById("model-search-input");
const telemetryTableTbody = document.getElementById("telemetry-table-tbody");
const showingCallsCaption = document.getElementById("showing-calls-caption");
const btnLoadMore = document.getElementById("btn-load-more");

// Modal Elements
const keyModalBackdrop = document.getElementById("key-modal-backdrop");
const modalProviderTitle = document.getElementById("modal-provider-title");
const modalKeysInput = document.getElementById("modal-keys-input");
const modalExtraCloudflare = document.getElementById("modal-extra-group-cloudflare");
const modalCfAccountId = document.getElementById("modal-cf-account-id");
const modalExtraOllama = document.getElementById("modal-extra-group-ollama");
const modalOllamaBaseUrl = document.getElementById("modal-ollama-base-url");
const modalTestFeedback = document.getElementById("modal-test-feedback");
const btnModalTest = document.getElementById("btn-modal-test");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const btnModalSave = document.getElementById("btn-modal-save");
const btnCloseModal = document.getElementById("btn-close-modal");

const toastContainer = document.getElementById("toast-container");

// ----------------- Initialization -----------------

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupAgentPlayground();
  setupKeysTab();
  setupTelemetryTab();
  checkHealth();

  // Load Initial Data
  loadKeysData();
  loadTelemetryData();
});

// ----------------- Toast Notifications -----------------

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// ----------------- Navigation -----------------

function setupNavigation() {
  navTabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".nav-pill-btn");
    if (!btn) return;

    const tabName = btn.dataset.tab;
    if (tabName === currentTab) return;

    document.querySelectorAll(".nav-pill-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    if (tabName === "agent") tabAgent.classList.add("active");
    if (tabName === "keys") {
      tabKeys.classList.add("active");
      loadKeysData();
    }
    if (tabName === "telemetry") {
      tabTelemetry.classList.add("active");
      loadTelemetryData();
    }

    currentTab = tabName;
  });
}

// ----------------- Health Check -----------------

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.status === "ready") {
        modelStatusText.textContent = "Router ready";
      } else {
        modelStatusText.textContent = "Loading...";
      }
    }
  } catch (err) {
    modelStatusText.textContent = "Offline";
  }
}

// ----------------- Agent Tab -----------------

function setupAgentPlayground() {
  // Preset pill clicks
  document.querySelectorAll(".preset-pill-tag").forEach(tag => {
    tag.addEventListener("click", () => {
      promptInput.value = tag.dataset.prompt;
      promptInput.focus();
    });
  });

  // Enter shortcut
  promptInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      executePrompt();
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      executePrompt();
    }
  });

  btnRunAgent.addEventListener("click", executePrompt);

  // Copy response
  btnCopyResponse.addEventListener("click", () => {
    if (!currentResponseData) {
      showToast("No response to copy.", "info");
      return;
    }
    const textToCopy = currentResponseData.raw || currentResponseData.text || "";
    navigator.clipboard.writeText(textToCopy);
    showToast("Response copied to clipboard!", "success");
  });

  // Expand / Collapse Viewport toggle
  btnToggleExpand.addEventListener("click", () => {
    isExpanded = !isExpanded;
    if (isExpanded) {
      responseScrollViewport.classList.add("is-expanded");
      btnExpandLabel.textContent = "Collapse";
      btnToggleExpand.querySelector("svg").innerHTML = `<polyline points="4 14 10 14 10 20"></polyline><polyline points="20 10 14 10 14 4"></polyline><line x1="14" y1="10" x2="21" y2="3"></line><line x1="3" y1="21" x2="10" y2="14"></line>`;
    } else {
      responseScrollViewport.classList.remove("is-expanded");
      btnExpandLabel.textContent = "Expand";
      btnToggleExpand.querySelector("svg").innerHTML = `<polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line>`;
    }
  });

  // Raw toggle
  btnToggleRaw.addEventListener("click", () => {
    isRawView = !isRawView;
    btnRawLabel.textContent = isRawView ? "Formatted" : "Raw";
    btnToggleRaw.querySelector("svg").innerHTML = isRawView
      ? `<polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline>`
      : `<polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline>`;

    if (isRawView) {
      responseFormattedArea.classList.add("hidden");
      responseRawContent.classList.remove("hidden");
    } else {
      responseFormattedArea.classList.remove("hidden");
      responseRawContent.classList.add("hidden");
    }
  });
}

async function executePrompt() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    showToast("Please enter a prompt or select a preset.", "error");
    promptInput.focus();
    return;
  }

  // Update User Prompt Bubble
  userPromptDisplay.textContent = prompt.length > 100 ? prompt.substring(0, 100) + "..." : prompt;

  // Running state
  btnRunAgent.disabled = true;
  btnRunAgent.innerHTML = `<span>Routing...</span>`;
  stepRoutingVal.textContent = "Classifying...";
  stepModelVal.textContent = "Selecting...";
  stepProviderSub.textContent = "via gateway";
  stepKeyVal.textContent = "Rotating...";

  const startTime = performance.now();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });

    const elapsedMs = Math.round(performance.now() - startTime);
    const elapsedSec = (elapsedMs / 1000).toFixed(1);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Server error");
    }

    const data = await res.json();
    currentResponseData = data;

    const rawText = data.text || (typeof data === "string" ? data : JSON.stringify(data, null, 2));
    currentResponseData.raw = rawText;

    // 1. Update Route Badge
    const difficulty = (data.difficulty || "Easy").toLowerCase();
    routeBadgePill.textContent = `${difficulty.charAt(0).toUpperCase() + difficulty.slice(1)} route`;
    routeBadgePill.className = `route-badge ${difficulty === 'medium' ? 'medium' : ''}`;

    // 2. Parse response into explanation + code
    parseAndRenderResponse(rawText);

    // 3. Update Stepper Timeline
    stepRoutingVal.textContent = `Classified ${difficulty}`;
    stepModelVal.textContent = data.model || "gpt-oss-20b";
    stepProviderSub.textContent = `via ${data.provider || "groq"}`;
    stepKeyVal.textContent = `Key ${data.key_index !== undefined ? data.key_index : 0}, rotated`;

    // 4. Update 2x2 Metric Tiles
    tileLatencyVal.textContent = `${(data.duration_ms ? (data.duration_ms / 1000).toFixed(1) : elapsedSec)} s`;
    const promptTok = data.prompt_tokens || 0;
    const compTok = data.completion_tokens || 0;
    tileTokensVal.textContent = promptTok + compTok;
    tilePromptVal.textContent = promptTok;
    tileCompVal.textContent = compTok;

    showToast(`Task executed successfully via ${data.provider || 'gateway'}!`, "success");

  } catch (err) {
    showToast(`Execution failed: ${err.message}`, "error");
    stepRoutingVal.textContent = "Error";
    stepModelVal.textContent = "Failed";
    stepProviderSub.textContent = "check logs";
  } finally {
    btnRunAgent.disabled = false;
    btnRunAgent.innerHTML = `<span>Run</span><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>`;
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function parseAndRenderResponse(rawText) {
  // 1. Populate raw view with the full untruncated text
  responseRawContent.textContent = rawText;

  // 2. Reset scroll position of the viewport to top
  if (responseScrollViewport) {
    responseScrollViewport.scrollTop = 0;
  }

  // 3. Render full markdown using marked (or safe fallback)
  let html = "";
  if (typeof marked !== "undefined" && typeof marked.parse === "function") {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true,
        pedantic: false
      });
      html = marked.parse(rawText);
    } catch (e) {
      console.warn("marked.parse failed, falling back to custom renderer:", e);
      html = fallbackMarkdownParse(rawText);
    }
  } else {
    html = fallbackMarkdownParse(rawText);
  }

  responseFormattedArea.innerHTML = html;

  // 4. Enhance code blocks inside responseFormattedArea with language tags and copy buttons
  enhanceCodeBlocks(responseFormattedArea);
}

function fallbackMarkdownParse(text) {
  const codeBlocks = [];
  let processed = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const placeholder = `___CODE_BLOCK_${codeBlocks.length}___`;
    codeBlocks.push({ lang: lang || "code", code });
    return placeholder;
  });

  processed = escapeHtml(processed);

  // Headers
  processed = processed.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  processed = processed.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  processed = processed.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Bold & Italic
  processed = processed.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  processed = processed.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Inline code
  processed = processed.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Line breaks & paragraphs
  processed = processed.replace(/\n\n+/g, "</p><p>");
  processed = `<p>${processed.replace(/\n/g, "<br>")}</p>`;

  // Restore code blocks
  codeBlocks.forEach((block, idx) => {
    const escapedCode = escapeHtml(block.code);
    const replacement = `<pre><code class="language-${block.lang}">${escapedCode}</code></pre>`;
    processed = processed.replace(`___CODE_BLOCK_${idx}___`, replacement);
  });

  return processed;
}

function enhanceCodeBlocks(container) {
  const preElements = container.querySelectorAll("pre");
  preElements.forEach((pre) => {
    // Prevent double wrapping
    if (pre.parentElement && pre.parentElement.classList.contains("code-block-box")) return;

    const code = pre.querySelector("code") || pre;
    const rawCodeText = code.textContent || "";

    // Extract language tag from class (e.g. language-python)
    let lang = "code";
    const classMatch = (code.className || "").match(/language-([a-zA-Z0-9_-]+)/);
    if (classMatch) {
      lang = classMatch[1];
    }

    const wrapper = document.createElement("div");
    wrapper.className = "code-block-box";

    const header = document.createElement("div");
    header.className = "code-block-header";
    header.innerHTML = `
      <span>${lang}</span>
      <button class="code-copy-btn" title="Copy code snippet">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span>Copy</span>
      </button>
    `;

    const copyBtn = header.querySelector(".code-copy-btn");
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(rawCodeText).then(() => {
        copyBtn.querySelector("span").textContent = "Copied!";
        showToast("Snippet copied!", "success");
        setTimeout(() => {
          copyBtn.querySelector("span").textContent = "Copy";
        }, 1800);
      });
    });

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(header);
    wrapper.appendChild(pre);
  });
}

// ----------------- Keys Tab -----------------

function setupKeysTab() {
  btnRefreshKeys.addEventListener("click", loadKeysData);

  btnModalCancel.addEventListener("click", closeModal);
  btnCloseModal.addEventListener("click", closeModal);
  keyModalBackdrop.addEventListener("click", (e) => {
    if (e.target === keyModalBackdrop) closeModal();
  });

  btnModalTest.addEventListener("click", testModalKey);
  btnModalSave.addEventListener("click", saveModalKeys);
}

async function loadKeysData() {
  try {
    const res = await fetch(`${API_BASE}/api/keys`);
    if (!res.ok) throw new Error("Failed to load key configurations");

    const data = await res.json();
    keyStatusData = data;

    renderKeysTable(data);
  } catch (err) {
    showToast(`Error loading keys: ${err.message}`, "error");
  }
}

function renderKeysTable(data) {
  const providers = data.providers;
  let totalKeys = 0;
  let readyKeys = 0;
  let coolingKeys = 0;

  providersTableTbody.innerHTML = "";

  const providerDescriptions = {
    groq: "GPT-OSS 20B and 120B, Qwen",
    gemini: "Flash-Lite and Flash models",
    cloudflare: "Workers AI, Qwen and GLM",
    nvidia: "NIM, Nemotron 3 models",
    ollama: "Self-hosted, OpenAI-compatible"
  };

  const providerNames = {
    groq: "Groq",
    gemini: "Gemini",
    cloudflare: "Cloudflare",
    nvidia: "Nvidia",
    ollama: "Ollama"
  };

  for (const [key, prov] of Object.entries(providers)) {
    totalKeys += prov.total_keys;

    prov.keys.forEach(k => {
      if (k.is_cooling) coolingKeys++;
      else readyKeys++;
    });

    const tr = document.createElement("tr");

    // Keys list bullets
    let keyBulletsHtml = "";
    if (prov.keys.length === 0) {
      keyBulletsHtml = `<span class="text-muted" style="font-size: 0.8rem;">No keys configured</span>`;
    } else {
      keyBulletsHtml = `
        <div class="key-bullet-list">
          ${prov.keys.map(k => `
            <div class="key-bullet-item">
              <span class="key-green-bullet">●</span>
              <span>#${k.index}</span>
              <span>${k.masked}</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    // Usage Today calculation
    const rpmUsed = prov.keys.reduce((acc, cur) => acc + cur.rpm_used, 0);
    const rpdUsed = prov.keys.reduce((acc, cur) => acc + cur.rpd_used, 0);
    const rpmLimit = prov.limits.rpm || 30;
    const rpdLimit = prov.limits.rpd || 1000;

    const rpmPercent = Math.min(100, Math.round((rpmUsed / rpmLimit) * 100));
    const rpdPercent = Math.min(100, Math.round((rpdUsed / rpdLimit) * 100));

    const isReady = prov.has_available;

    tr.innerHTML = `
      <td>
        <div class="provider-cell">
          <div class="provider-name-badge">
            <span class="prov-title">${providerNames[key] || key}</span>
            <span class="route-badge ${isReady ? '' : 'medium'}">${isReady ? 'Ready' : 'Cooling'}</span>
          </div>
          <span class="prov-models-desc">${providerDescriptions[key] || ''}</span>
        </div>
      </td>

      <td>
        <div class="key-bullets-cell">
          ${keyBulletsHtml}
        </div>
      </td>

      <td>
        <div class="usage-cell">
          <div class="usage-dual-group">
            <div class="usage-subgroup">
              <div class="usage-meta-text">
                <span>Per minute</span>
                <span><strong>${rpmUsed}</strong> / ${rpmLimit}</span>
              </div>
              <div class="slim-track">
                <div class="slim-fill" style="width: ${rpmPercent}%;"></div>
              </div>
            </div>
            <div class="usage-subgroup">
              <div class="usage-meta-text">
                <span>Per day</span>
                <span><strong>${rpdUsed}</strong> / ${rpdLimit}</span>
              </div>
              <div class="slim-track">
                <div class="slim-fill" style="width: ${rpdPercent}%;"></div>
              </div>
            </div>
          </div>
        </div>
      </td>

      <td class="actions-cell">
        <div class="action-buttons-group">
          <button class="btn-table-action btn-ping" data-prov="${key}">Test ping</button>
          <button class="btn-table-action manage-btn btn-manage" data-prov="${key}">Manage</button>
        </div>
      </td>
    `;

    providersTableTbody.appendChild(tr);
  }

  // Update Summary Box
  statTotalKeys.textContent = totalKeys;
  statReadyKeys.textContent = readyKeys;
  statCoolingKeys.textContent = coolingKeys;

  // Attach Table Action Handlers
  document.querySelectorAll(".btn-ping").forEach(btn => {
    btn.addEventListener("click", () => pingProvider(btn.dataset.prov));
  });

  document.querySelectorAll(".btn-manage").forEach(btn => {
    btn.addEventListener("click", () => openKeyModal(btn.dataset.prov));
  });
}

async function pingProvider(prov) {
  const provData = keyStatusData ? keyStatusData.providers[prov] : null;
  if (!provData || provData.keys.length === 0) {
    showToast(`No keys configured for ${prov}.`, "error");
    return;
  }

  const testKey = provData.keys[0].full_key;
  showToast(`Pinging ${prov.toUpperCase()} API...`, "info");

  try {
    const extra = provData.extra || {};
    const res = await fetch(`${API_BASE}/api/keys/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: prov,
        key: testKey,
        extra
      })
    });

    const data = await res.json();
    if (data.valid) {
      showToast(`✓ ${prov.toUpperCase()}: ${data.message}`, "success");
    } else {
      showToast(`✗ ${prov.toUpperCase()}: ${data.message}`, "error");
    }
  } catch (err) {
    showToast(`Ping failed: ${err.message}`, "error");
  }
}

// ----------------- Modal Dialog -----------------

function openKeyModal(providerName) {
  activeModalProvider = providerName;
  modalProviderTitle.textContent = `Configure ${providerName.toUpperCase()} Keys`;
  modalTestFeedback.className = "test-feedback hidden";

  const provData = keyStatusData ? keyStatusData.providers[providerName] : null;

  if (provData && provData.keys.length > 0) {
    modalKeysInput.value = provData.keys.map(k => k.full_key || "").join(",\n");
  } else {
    modalKeysInput.value = "";
  }

  // Provider specific extra fields
  if (providerName === "cloudflare") {
    modalExtraCloudflare.classList.remove("hidden");
    modalCfAccountId.value = (provData && provData.extra && provData.extra.account_id) || "";
  } else {
    modalExtraCloudflare.classList.add("hidden");
  }

  if (providerName === "ollama") {
    modalExtraOllama.classList.remove("hidden");
    modalOllamaBaseUrl.value = (provData && provData.extra && provData.extra.base_url) || "https://ollama.com/v1";
  } else {
    modalExtraOllama.classList.add("hidden");
  }

  keyModalBackdrop.classList.remove("hidden");
  modalKeysInput.focus();
}

function closeModal() {
  keyModalBackdrop.classList.add("hidden");
  activeModalProvider = null;
}

async function testModalKey() {
  if (!activeModalProvider) return;
  const rawText = modalKeysInput.value.trim();
  const keys = rawText.split(",").map(k => k.trim()).filter(k => k);

  if (keys.length === 0) {
    modalTestFeedback.textContent = "Please enter at least one key to test.";
    modalTestFeedback.className = "test-feedback failure";
    modalTestFeedback.classList.remove("hidden");
    return;
  }

  btnModalTest.disabled = true;
  btnModalTest.textContent = "Verifying...";

  try {
    const extra = {};
    if (activeModalProvider === "cloudflare") extra.account_id = modalCfAccountId.value.trim();
    if (activeModalProvider === "ollama") extra.base_url = modalOllamaBaseUrl.value.trim();

    const res = await fetch(`${API_BASE}/api/keys/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: activeModalProvider,
        key: keys[0],
        extra
      })
    });

    const data = await res.json();
    modalTestFeedback.textContent = data.message;
    modalTestFeedback.className = `test-feedback ${data.valid ? 'success' : 'failure'}`;
    modalTestFeedback.classList.remove("hidden");
  } catch (err) {
    modalTestFeedback.textContent = `Verification failed: ${err.message}`;
    modalTestFeedback.className = "test-feedback failure";
    modalTestFeedback.classList.remove("hidden");
  } finally {
    btnModalTest.disabled = false;
    btnModalTest.textContent = "Test Connection";
  }
}

async function saveModalKeys() {
  if (!activeModalProvider) return;

  const rawText = modalKeysInput.value.trim();
  const keys = rawText.split(/[\n,]+/).map(k => k.trim()).filter(k => k);

  const extra = {};
  if (activeModalProvider === "cloudflare") extra.account_id = modalCfAccountId.value.trim();
  if (activeModalProvider === "ollama") extra.base_url = modalOllamaBaseUrl.value.trim();

  btnModalSave.disabled = true;
  btnModalSave.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/api/keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: activeModalProvider,
        keys,
        extra
      })
    });

    if (!res.ok) throw new Error("Failed to save keys");

    showToast(`${activeModalProvider.toUpperCase()} pool updated & hot-reloaded!`, "success");
    closeModal();
    loadKeysData();
  } catch (err) {
    showToast(`Error saving: ${err.message}`, "error");
  } finally {
    btnModalSave.disabled = false;
    btnModalSave.textContent = "Save & Hot-Reload";
  }
}

// ----------------- Telemetry Tab -----------------

function setupTelemetryTab() {
  btnRefreshTelemetry.addEventListener("click", loadTelemetryData);

  // Filter Segment Buttons
  filterAllBtn.addEventListener("click", () => setTelemetryFilter("all"));
  filterSuccessBtn.addEventListener("click", () => setTelemetryFilter("success"));
  filterErrorsBtn.addEventListener("click", () => setTelemetryFilter("error"));

  // Provider Dropdown
  providerFilterSelect.addEventListener("change", (e) => {
    activeProviderFilter = e.target.value;
    renderFilteredTelemetry();
  });

  // Search Input
  modelSearchInput.addEventListener("input", (e) => {
    telemetrySearchQuery = e.target.value.toLowerCase().trim();
    renderFilteredTelemetry();
  });

  // Load More Button
  btnLoadMore.addEventListener("click", () => {
    telemetryPageSize += 10;
    renderFilteredTelemetry();
  });
}

function setTelemetryFilter(filterName) {
  activeTelemetryFilter = filterName;
  [filterAllBtn, filterSuccessBtn, filterErrorsBtn].forEach(b => b.classList.remove("active"));

  if (filterName === "all") filterAllBtn.classList.add("active");
  if (filterName === "success") filterSuccessBtn.classList.add("active");
  if (filterName === "error") filterErrorsBtn.classList.add("active");

  renderFilteredTelemetry();
}

async function loadTelemetryData() {
  try {
    const res = await fetch(`${API_BASE}/api/metrics?limit=150`);
    if (!res.ok) throw new Error("Failed to load telemetry");

    const data = await res.json();
    allTelemetryRecords = data.recent_calls || [];

    // Summary numbers
    const total = data.summary.total_calls || allTelemetryRecords.length;
    const ok = data.summary.ok_calls || 0;
    const errors = data.summary.error_calls || 0;
    const today = data.summary.today_calls || 0;

    teleTotalCalls.textContent = total;
    teleTodayCalls.textContent = today;
    teleOkCalls.textContent = ok;
    teleErrorCalls.textContent = errors;

    filterAllCount.textContent = total;
    filterSuccessCount.textContent = ok;
    filterErrorsCount.textContent = errors;

    // Segmented Progress Bar
    const successRate = total > 0 ? Math.round((ok / total) * 100) : 100;
    const errorRate = 100 - successRate;

    segBarGreen.style.width = `${successRate}%`;
    segBarCoral.style.width = `${errorRate}%`;
    segLabelSuccess.textContent = `${successRate}% success`;
    segLabelError.textContent = `${errorRate}% errors`;

    renderFilteredTelemetry();
  } catch (err) {
    showToast(`Error loading telemetry: ${err.message}`, "error");
  }
}

function renderFilteredTelemetry() {
  let filtered = allTelemetryRecords.filter(r => {
    // 1. Status Filter
    if (activeTelemetryFilter === "success" && r.status !== "ok") return false;
    if (activeTelemetryFilter === "error" && r.status === "ok") return false;

    // 2. Provider Filter
    if (activeProviderFilter !== "all" && r.provider.toLowerCase() !== activeProviderFilter.toLowerCase()) return false;

    // 3. Search Query
    if (telemetrySearchQuery) {
      const modelMatch = (r.model_name || "").toLowerCase().includes(telemetrySearchQuery);
      const provMatch = (r.provider || "").toLowerCase().includes(telemetrySearchQuery);
      if (!modelMatch && !provMatch) return false;
    }

    return true;
  });

  const displayed = filtered.slice(0, telemetryPageSize);
  showingCallsCaption.textContent = `Showing ${displayed.length} of ${filtered.length} calls`;

  if (displayed.length === 0) {
    telemetryTableTbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2.5rem 0;">No matching telemetry records found.</td></tr>`;
    return;
  }

  telemetryTableTbody.innerHTML = displayed.map(r => {
    const timeStr = new Date(r.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    const isOk = r.status === "ok";
    const statusText = isOk ? "200 OK" : (r.http_status ? `${r.http_status} error` : "500 error");
    const statusClass = isOk ? "ok" : "error";
    const totalTokens = (r.prompt_tokens || 0) + (r.completion_tokens || 0);

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.8rem;">${timeStr}</td>
        <td><strong>${r.provider}</strong></td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">${r.model_name || '--'}</td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">#${r.key_index}</td>
        <td><span class="status-pill-table ${statusClass}">${statusText}</span></td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">${r.prompt_tokens} / ${r.completion_tokens}</td>
        <td style="font-family: var(--font-mono); font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">${totalTokens}</td>
      </tr>
    `;
  }).join("");
}
