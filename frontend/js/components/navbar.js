/**
 * AEGIS LLM GATEWAY - NAVBAR & ROUTER STATUS COMPONENT
 */

import { state } from '../config.js';
import { fetchHealth } from '../api.js';

let navTabs = null;
let tabPanes = {};
let modelStatusPill = null;
let modelStatusText = null;
let onTabChangeCallback = null;

export function initNavbar(onTabChange) {
  onTabChangeCallback = onTabChange;
  navTabs = document.getElementById("main-nav-tabs");
  modelStatusPill = document.getElementById("model-status-pill");
  modelStatusText = document.getElementById("model-status-text");

  tabPanes = {
    agent: document.getElementById("tab-agent"),
    keys: document.getElementById("tab-keys"),
    telemetry: document.getElementById("tab-telemetry")
  };

  if (!navTabs) return;

  navTabs.addEventListener("click", (e) => {
    const btn = e.target.closest(".nav-pill-btn");
    if (!btn) return;

    const tabName = btn.dataset.tab;
    if (!tabName || tabName === state.currentTab) return;

    switchTab(tabName);
  });

  // Initial health check & periodic polling
  checkRouterHealth();
  setInterval(checkRouterHealth, 30000);
}

export function switchTab(tabName) {
  state.currentTab = tabName;

  // Update navbar pill buttons
  document.querySelectorAll(".nav-pill-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.tab === tabName);
  });

  // Update active tab pane
  Object.keys(tabPanes).forEach((key) => {
    const pane = tabPanes[key];
    if (pane) {
      pane.classList.toggle("active", key === tabName);
    }
  });

  if (typeof onTabChangeCallback === "function") {
    onTabChangeCallback(tabName);
  }
}

export async function checkRouterHealth() {
  if (!modelStatusText) return;

  try {
    const data = await fetchHealth();
    if (data.status === "ready") {
      modelStatusText.textContent = "Router ready";
      if (modelStatusPill) modelStatusPill.classList.remove("offline");
    } else {
      modelStatusText.textContent = "Loading...";
      if (modelStatusPill) modelStatusPill.classList.remove("offline");
    }
  } catch (err) {
    modelStatusText.textContent = "Offline";
    if (modelStatusPill) modelStatusPill.classList.add("offline");
  }
}
