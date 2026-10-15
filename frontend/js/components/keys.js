/**
 * AEGIS LLM GATEWAY - API KEYS AND POOLS COMPONENT
 */

import { state, PROVIDER_NAMES, PROVIDER_DESCRIPTIONS } from '../config.js';
import { fetchKeys, testKey, saveKeys } from '../api.js';
import { showToast } from './toast.js';

let btnRefreshKeys = null;
let statTotalKeys = null;
let statReadyKeys = null;
let statCoolingKeys = null;
let statDbStore = null;
let providersTableTbody = null;

// Modal Elements
let keyModalBackdrop = null;
let modalProviderTitle = null;
let modalKeysInput = null;
let modalExtraCloudflare = null;
let modalCfAccountId = null;
let modalExtraOllama = null;
let modalOllamaBaseUrl = null;
let modalTestFeedback = null;
let btnModalTest = null;
let btnModalCancel = null;
let btnModalSave = null;
let btnCloseModal = null;

export function initKeysTab() {
  btnRefreshKeys = document.getElementById("btn-refresh-keys");
  statTotalKeys = document.getElementById("stat-total-keys");
  statReadyKeys = document.getElementById("stat-ready-keys");
  statCoolingKeys = document.getElementById("stat-cooling-keys");
  statDbStore = document.getElementById("stat-db-store");
  providersTableTbody = document.getElementById("providers-table-tbody");

  keyModalBackdrop = document.getElementById("key-modal-backdrop");
  modalProviderTitle = document.getElementById("modal-provider-title");
  modalKeysInput = document.getElementById("modal-keys-input");
  modalExtraCloudflare = document.getElementById("modal-extra-group-cloudflare");
  modalCfAccountId = document.getElementById("modal-cf-account-id");
  modalExtraOllama = document.getElementById("modal-extra-group-ollama");
  modalOllamaBaseUrl = document.getElementById("modal-ollama-base-url");
  modalTestFeedback = document.getElementById("modal-test-feedback");
  btnModalTest = document.getElementById("btn-modal-test");
  btnModalCancel = document.getElementById("btn-modal-cancel");
  btnModalSave = document.getElementById("btn-modal-save");
  btnCloseModal = document.getElementById("btn-close-modal");

  if (btnRefreshKeys) {
    btnRefreshKeys.addEventListener("click", loadKeysData);
  }

  // Modal Handlers
  if (btnModalCancel) btnModalCancel.addEventListener("click", closeModal);
  if (btnCloseModal) btnCloseModal.addEventListener("click", closeModal);
  if (keyModalBackdrop) {
    keyModalBackdrop.addEventListener("click", (e) => {
      if (e.target === keyModalBackdrop) closeModal();
    });
  }

  if (btnModalTest) btnModalTest.addEventListener("click", testModalKey);
  if (btnModalSave) btnModalSave.addEventListener("click", saveModalKeys);
}

export async function loadKeysData() {
  try {
    const data = await fetchKeys();
    state.keyStatusData = data;
    renderKeysTable(data);
  } catch (err) {
    showToast(`Error loading keys: ${err.message}`, "error");
  }
}

export function renderKeysTable(data) {
  if (!providersTableTbody) return;

  const providers = data.providers || {};
  let totalKeys = 0;
  let readyKeys = 0;
  let coolingKeys = 0;

  providersTableTbody.innerHTML = "";

  for (const [key, prov] of Object.entries(providers)) {
    totalKeys += prov.total_keys || 0;

    (prov.keys || []).forEach((k) => {
      if (k.is_cooling) coolingKeys++;
      else readyKeys++;
    });

    const tr = document.createElement("tr");

    // Masked Key Pool Bullets
    let keyBulletsHtml = "";
    if (!prov.keys || prov.keys.length === 0) {
      keyBulletsHtml = `<span class="text-muted" style="font-size: 0.8rem;">No keys configured</span>`;
    } else {
      keyBulletsHtml = `
        <div class="key-bullet-list">
          ${prov.keys.map((k) => `
            <div class="key-bullet-item">
              <span class="key-green-bullet ${k.is_cooling ? 'cooling' : ''}">●</span>
              <span>#${k.index}</span>
              <span>${k.masked}</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    // Usage Today Calculation
    const rpmUsed = (prov.keys || []).reduce((acc, cur) => acc + (cur.rpm_used || 0), 0);
    const rpdUsed = (prov.keys || []).reduce((acc, cur) => acc + (cur.rpd_used || 0), 0);
    const rpmLimit = (prov.limits && prov.limits.rpm) || 30;
    const rpdLimit = (prov.limits && prov.limits.rpd) || 1000;

    const rpmPercent = Math.min(100, Math.round((rpmUsed / rpmLimit) * 100));
    const rpdPercent = Math.min(100, Math.round((rpdUsed / rpdLimit) * 100));

    const isReady = prov.has_available;

    tr.innerHTML = `
      <td>
        <div class="provider-cell">
          <div class="provider-name-badge">
            <span class="prov-title">${PROVIDER_NAMES[key] || key}</span>
            <span class="route-badge ${isReady ? '' : 'medium'}">${isReady ? 'Ready' : 'Cooling'}</span>
          </div>
          <span class="prov-models-desc">${PROVIDER_DESCRIPTIONS[key] || ''}</span>
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

  // Update Summary Metrics
  if (statTotalKeys) statTotalKeys.textContent = totalKeys;
  if (statReadyKeys) statReadyKeys.textContent = readyKeys;
  if (statCoolingKeys) statCoolingKeys.textContent = coolingKeys;
  if (statDbStore) statDbStore.textContent = data.database_connected ? "Neon DB (Connected)" : "In-Memory";

  // Attach Table Action Button Listeners
  providersTableTbody.querySelectorAll(".btn-ping").forEach((btn) => {
    btn.addEventListener("click", () => pingProvider(btn.dataset.prov));
  });

  providersTableTbody.querySelectorAll(".btn-manage").forEach((btn) => {
    btn.addEventListener("click", () => openKeyModal(btn.dataset.prov));
  });
}

export async function pingProvider(prov) {
  const provData = state.keyStatusData ? state.keyStatusData.providers[prov] : null;
  if (!provData || provData.total_keys === 0) {
    showToast(`No keys configured for ${prov.toUpperCase()}.`, "error");
    return;
  }

  showToast(`Pinging ${prov.toUpperCase()} API...`, "info");

  try {
    const extra = provData.extra || {};
    const data = await testKey(prov, null, extra);

    if (data.valid) {
      showToast(`✓ ${prov.toUpperCase()}: ${data.message}`, "success");
    } else {
      showToast(`✗ ${prov.toUpperCase()}: ${data.message}`, "error");
    }
  } catch (err) {
    showToast(`Ping failed: ${err.message}`, "error");
  }
}

export function openKeyModal(providerName) {
  state.activeModalProvider = providerName;
  if (!modalProviderTitle || !keyModalBackdrop) return;

  modalProviderTitle.textContent = `Configure ${providerName.toUpperCase()} Keys`;
  if (modalTestFeedback) modalTestFeedback.className = "test-feedback hidden";

  const provData = state.keyStatusData ? state.keyStatusData.providers[providerName] : null;

  if (modalKeysInput) {
    if (provData && provData.keys && provData.keys.length > 0) {
      modalKeysInput.value = "";
      modalKeysInput.placeholder = `Currently configured: ${provData.total_keys} key(s) (${provData.keys.map(k => k.masked).join(", ")}).\nEnter new comma-separated keys here to update.`;
    } else {
      modalKeysInput.value = "";
      modalKeysInput.placeholder = "key_1, key_2, key_3...";
    }
  }

  // Provider specific extra inputs
  if (providerName === "cloudflare") {
    if (modalExtraCloudflare) modalExtraCloudflare.classList.remove("hidden");
    if (modalCfAccountId) modalCfAccountId.value = (provData && provData.extra && provData.extra.account_id) || "";
  } else {
    if (modalExtraCloudflare) modalExtraCloudflare.classList.add("hidden");
  }

  if (providerName === "ollama") {
    if (modalExtraOllama) modalExtraOllama.classList.remove("hidden");
    if (modalOllamaBaseUrl) modalOllamaBaseUrl.value = (provData && provData.extra && provData.extra.base_url) || "https://ollama.com/v1";
  } else {
    if (modalExtraOllama) modalExtraOllama.classList.add("hidden");
  }

  keyModalBackdrop.classList.remove("hidden");
  if (modalKeysInput) modalKeysInput.focus();
}

export function closeModal() {
  if (keyModalBackdrop) keyModalBackdrop.classList.add("hidden");
  state.activeModalProvider = null;
}

export async function testModalKey() {
  if (!state.activeModalProvider) return;
  const rawText = modalKeysInput ? modalKeysInput.value.trim() : "";
  const keys = rawText.split(/[\n,]+/).map((k) => k.trim()).filter((k) => k);

  if (keys.length === 0) {
    // If input is empty, test current active key in pool
    const provData = state.keyStatusData ? state.keyStatusData.providers[state.activeModalProvider] : null;
    if (!provData || provData.total_keys === 0) {
      if (modalTestFeedback) {
        modalTestFeedback.textContent = "Please enter an API key to test.";
        modalTestFeedback.className = "test-feedback failure";
        modalTestFeedback.classList.remove("hidden");
      }
      return;
    }
  }

  if (btnModalTest) {
    btnModalTest.disabled = true;
    btnModalTest.textContent = "Verifying...";
  }

  try {
    const extra = {};
    if (state.activeModalProvider === "cloudflare" && modalCfAccountId) {
      extra.account_id = modalCfAccountId.value.trim();
    }
    if (state.activeModalProvider === "ollama" && modalOllamaBaseUrl) {
      extra.base_url = modalOllamaBaseUrl.value.trim();
    }

    const testKeyToUse = keys.length > 0 ? keys[0] : null;
    const data = await testKey(state.activeModalProvider, testKeyToUse, extra);

    if (modalTestFeedback) {
      modalTestFeedback.textContent = data.message;
      modalTestFeedback.className = `test-feedback ${data.valid ? 'success' : 'failure'}`;
      modalTestFeedback.classList.remove("hidden");
    }
  } catch (err) {
    if (modalTestFeedback) {
      modalTestFeedback.textContent = `Verification failed: ${err.message}`;
      modalTestFeedback.className = "test-feedback failure";
      modalTestFeedback.classList.remove("hidden");
    }
  } finally {
    if (btnModalTest) {
      btnModalTest.disabled = false;
      btnModalTest.textContent = "Test Connection";
    }
  }
}

export async function saveModalKeys() {
  if (!state.activeModalProvider) return;

  const rawText = modalKeysInput ? modalKeysInput.value.trim() : "";
  const keys = rawText.split(/[\n,]+/).map((k) => k.trim()).filter((k) => k);

  const extra = {};
  if (state.activeModalProvider === "cloudflare" && modalCfAccountId) {
    extra.account_id = modalCfAccountId.value.trim();
  }
  if (state.activeModalProvider === "ollama" && modalOllamaBaseUrl) {
    extra.base_url = modalOllamaBaseUrl.value.trim();
  }

  if (keys.length === 0 && (!extra.account_id && !extra.base_url)) {
    showToast("Please enter at least one key to save.", "error");
    return;
  }

  if (btnModalSave) {
    btnModalSave.disabled = true;
    btnModalSave.textContent = "Saving...";
  }

  try {
    await saveKeys(state.activeModalProvider, keys, extra);
    showToast(`${state.activeModalProvider.toUpperCase()} pool updated & hot-reloaded!`, "success");
    closeModal();
    loadKeysData();
  } catch (err) {
    showToast(`Error saving: ${err.message}`, "error");
  } finally {
    if (btnModalSave) {
      btnModalSave.disabled = false;
      btnModalSave.textContent = "Save & Hot-Reload";
    }
  }
}
