/**
 * AEGIS LLM GATEWAY - MASTER CLIENT BOOTSTRAP
 * Production modular entry point
 */

import { initNavbar } from './components/navbar.js';
import { initAgentPlayground } from './components/agent.js';
import { initKeysTab, loadKeysData } from './components/keys.js';
import { initTelemetryTab, loadTelemetryData } from './components/telemetry.js';

function onTabSwitched(tabName) {
  if (tabName === "keys") {
    loadKeysData();
  } else if (tabName === "telemetry") {
    loadTelemetryData();
  }
}

function bootstrap() {
  initNavbar(onTabSwitched);
  initAgentPlayground();
  initKeysTab();
  initTelemetryTab();

  // Load initial dataset in background
  loadKeysData();
  loadTelemetryData();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
