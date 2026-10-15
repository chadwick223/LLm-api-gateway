/**
 * AEGIS LLM GATEWAY - MARKDOWN UTILITIES
 * Renders rich markdown with code block copy buttons and safe fallbacks
 */

import { showToast } from '../components/toast.js';

export function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function parseAndRenderMarkdown(rawText, formattedArea, rawArea) {
  if (rawArea) {
    rawArea.textContent = rawText;
  }

  let html = "";
  if (typeof window.marked !== "undefined" && typeof window.marked.parse === "function") {
    try {
      window.marked.setOptions({
        gfm: true,
        breaks: true,
        pedantic: false
      });
      html = window.marked.parse(rawText);
    } catch (e) {
      console.warn("marked.parse failed, falling back to regex parser:", e);
      html = fallbackMarkdownParse(rawText);
    }
  } else {
    html = fallbackMarkdownParse(rawText);
  }

  if (formattedArea) {
    formattedArea.innerHTML = html;
    enhanceCodeBlocks(formattedArea);
  }

  return html;
}

export function fallbackMarkdownParse(text) {
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

export function enhanceCodeBlocks(container) {
  const preElements = container.querySelectorAll("pre");
  preElements.forEach((pre) => {
    if (pre.parentElement && pre.parentElement.classList.contains("code-block-box")) return;

    const code = pre.querySelector("code") || pre;
    const rawCodeText = code.textContent || "";

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
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
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
