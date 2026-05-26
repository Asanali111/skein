// Wevex content script — claude.ai
//
// Site-specific selectors only. All cross-site logic lives in
// content_common.js, which exposes __WevexCommon.init(siteAdapter).
//
// claude.ai uses a ProseMirror contenteditable, not a real <textarea>.
// The class names ("ProseMirror", role="textbox") are reasonably stable
// but we probe a few selectors to absorb future churn.

(() => {
  function findPromptElement() {
    return (
      document.querySelector('div[contenteditable="true"].ProseMirror') ||
      document.querySelector('[contenteditable="true"][role="textbox"]') ||
      document.querySelector('div[contenteditable="true"]')
    );
  }

  function findSendButton() {
    return (
      document.querySelector('button[aria-label*="Send" i]') ||
      document.querySelector('button[data-testid*="send" i]') ||
      document.querySelector('button[type="submit"]')
    );
  }

  // Iter 35: find rendered assistant turns for the Save-to-Wevex button.
  // Claude wraps each assistant message body in a div carrying the
  // `font-claude-message` class. We anchor on the closest stable parent
  // that doesn't churn between streaming and final state.
  function findAssistantTurns() {
    const nodes = document.querySelectorAll(
      'div.font-claude-message, [data-testid="message-content"][data-message-author="assistant"]',
    );
    return Array.from(nodes);
  }

  if (!globalThis.__WevexCommon) {
    console.warn("[wevex] content_common.js not loaded; aborting claude.ai script");
    return;
  }

  globalThis.__WevexCommon.init({
    siteName: "claude.ai",
    findPromptElement,
    findSendButton,
    findAssistantTurns,
  });
})();
