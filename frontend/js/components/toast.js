/**
 * AEGIS LLM GATEWAY - TOAST NOTIFICATION COMPONENT
 */

let container = null;

function getContainer() {
  if (!container) {
    container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }
  }
  return container;
}

/**
 * Display a toast notification
 * @param {string} message - Message to display
 * @param {"success"|"error"|"info"} type - Notification type
 * @param {number} duration - Display time in ms
 */
export function showToast(message, type = "info", duration = 3500) {
  const toastBox = getContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toastBox.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(20px)";
    setTimeout(() => toast.remove(), 250);
  }, duration);
}
