/**
 * AEGIS LLM GATEWAY - TELEMETRY & LOGS COMPONENT
 */

import { state } from '../config.js';
import { fetchMetrics } from '../api.js';
import { showToast } from './toast.js';

let btnRefreshTelemetry = null;
let teleTotalCalls = null;
let teleTodayCalls = null;
let teleOkCalls = null;
let teleErrorCalls = null;

let segBarGreen = null;
let segBarCoral = null;
let segLabelSuccess = null;
let segLabelError = null;

let filterAllBtn = null;
let filterSuccessBtn = null;
let filterErrorsBtn = null;
let filterAllCount = null;
let filterSuccessCount = null;
let filterErrorsCount = null;

let providerFilterSelect = null;
let modelSearchInput = null;
let telemetryTableTbody = null;
let showingCallsCaption = null;
let btnLoadMore = null;

export function initTelemetryTab() {
  btnRefreshTelemetry = document.getElementById("btn-refresh-telemetry");
  teleTotalCalls = document.getElementById("tele-total-calls");
  teleTodayCalls = document.getElementById("tele-today-calls");
  teleOkCalls = document.getElementById("tele-ok-calls");
  teleErrorCalls = document.getElementById("tele-error-calls");

  segBarGreen = document.getElementById("seg-bar-green");
  segBarCoral = document.getElementById("seg-bar-coral");
  segLabelSuccess = document.getElementById("seg-label-success");
  segLabelError = document.getElementById("seg-label-error");

  filterAllBtn = document.getElementById("filter-all-btn");
  filterSuccessBtn = document.getElementById("filter-success-btn");
  filterErrorsBtn = document.getElementById("filter-errors-btn");
  filterAllCount = document.getElementById("filter-all-count");
  filterSuccessCount = document.getElementById("filter-success-count");
  filterErrorsCount = document.getElementById("filter-errors-count");

  providerFilterSelect = document.getElementById("provider-filter-select");
  modelSearchInput = document.getElementById("model-search-input");
  telemetryTableTbody = document.getElementById("telemetry-table-tbody");
  showingCallsCaption = document.getElementById("showing-calls-caption");
  btnLoadMore = document.getElementById("btn-load-more");

  if (btnRefreshTelemetry) {
    btnRefreshTelemetry.addEventListener("click", loadTelemetryData);
  }

  // Filter segment buttons
  if (filterAllBtn) filterAllBtn.addEventListener("click", () => setTelemetryFilter("all"));
  if (filterSuccessBtn) filterSuccessBtn.addEventListener("click", () => setTelemetryFilter("success"));
  if (filterErrorsBtn) filterErrorsBtn.addEventListener("click", () => setTelemetryFilter("error"));

  // Provider dropdown
  if (providerFilterSelect) {
    providerFilterSelect.addEventListener("change", (e) => {
      state.activeProviderFilter = e.target.value;
      renderFilteredTelemetry();
    });
  }

  // Search input
  if (modelSearchInput) {
    modelSearchInput.addEventListener("input", (e) => {
      state.telemetrySearchQuery = e.target.value.toLowerCase().trim();
      renderFilteredTelemetry();
    });
  }

  // Load more button
  if (btnLoadMore) {
    btnLoadMore.addEventListener("click", () => {
      state.telemetryPageSize += 10;
      renderFilteredTelemetry();
    });
  }
}

export function setTelemetryFilter(filterName) {
  state.activeTelemetryFilter = filterName;

  [filterAllBtn, filterSuccessBtn, filterErrorsBtn].forEach((b) => {
    if (b) b.classList.remove("active");
  });

  if (filterName === "all" && filterAllBtn) filterAllBtn.classList.add("active");
  if (filterName === "success" && filterSuccessBtn) filterSuccessBtn.classList.add("active");
  if (filterName === "error" && filterErrorsBtn) filterErrorsBtn.classList.add("active");

  renderFilteredTelemetry();
}

export async function loadTelemetryData() {
  try {
    const data = await fetchMetrics(150);
    state.allTelemetryRecords = data.recent_calls || [];

    const summary = data.summary || {};
    const total = summary.total_calls !== undefined ? summary.total_calls : state.allTelemetryRecords.length;
    const ok = summary.ok_calls || 0;
    const errors = summary.error_calls || 0;
    const today = summary.today_calls || 0;

    if (teleTotalCalls) teleTotalCalls.textContent = total;
    if (teleTodayCalls) teleTodayCalls.textContent = today;
    if (teleOkCalls) teleOkCalls.textContent = ok;
    if (teleErrorCalls) teleErrorCalls.textContent = errors;

    if (filterAllCount) filterAllCount.textContent = total;
    if (filterSuccessCount) filterSuccessCount.textContent = ok;
    if (filterErrorsCount) filterErrorsCount.textContent = errors;

    // Segmented Progress Bar calculation
    const successRate = total > 0 ? Math.round((ok / total) * 100) : 100;
    const errorRate = 100 - successRate;

    if (segBarGreen) segBarGreen.style.width = `${successRate}%`;
    if (segBarCoral) segBarCoral.style.width = `${errorRate}%`;
    if (segLabelSuccess) segLabelSuccess.textContent = `${successRate}% success`;
    if (segLabelError) segLabelError.textContent = `${errorRate}% errors`;

    renderFilteredTelemetry();
  } catch (err) {
    showToast(`Error loading telemetry: ${err.message}`, "error");
  }
}

export function renderFilteredTelemetry() {
  if (!telemetryTableTbody) return;

  const filtered = state.allTelemetryRecords.filter((r) => {
    // 1. Status Filter
    if (state.activeTelemetryFilter === "success" && r.status !== "ok") return false;
    if (state.activeTelemetryFilter === "error" && r.status === "ok") return false;

    // 2. Provider Filter
    if (state.activeProviderFilter !== "all" && (r.provider || "").toLowerCase() !== state.activeProviderFilter.toLowerCase()) {
      return false;
    }

    // 3. Search Query
    if (state.telemetrySearchQuery) {
      const modelMatch = (r.model_name || "").toLowerCase().includes(state.telemetrySearchQuery);
      const provMatch = (r.provider || "").toLowerCase().includes(state.telemetrySearchQuery);
      if (!modelMatch && !provMatch) return false;
    }

    return true;
  });

  const displayed = filtered.slice(0, state.telemetryPageSize);
  if (showingCallsCaption) {
    showingCallsCaption.textContent = `Showing ${displayed.length} of ${filtered.length} calls`;
  }

  if (displayed.length === 0) {
    telemetryTableTbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2.5rem 0;">No matching telemetry records found.</td></tr>`;
    return;
  }

  telemetryTableTbody.innerHTML = displayed.map((r) => {
    const timeStr = new Date(r.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    const isOk = r.status === "ok";
    const statusText = isOk ? "200 OK" : (r.http_status ? `${r.http_status} error` : "500 error");
    const statusClass = isOk ? "ok" : "error";
    const promptTok = r.prompt_tokens || 0;
    const compTok = r.completion_tokens || 0;
    const totalTokens = promptTok + compTok;

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.8rem;">${timeStr}</td>
        <td><strong>${r.provider}</strong></td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">${r.model_name || '--'}</td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">#${r.key_index}</td>
        <td><span class="status-pill-table ${statusClass}">${statusText}</span></td>
        <td style="font-family: var(--font-mono); font-size: 0.82rem;">${promptTok} / ${compTok}</td>
        <td style="font-family: var(--font-mono); font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">${totalTokens}</td>
      </tr>
    `;
  }).join("");
}
