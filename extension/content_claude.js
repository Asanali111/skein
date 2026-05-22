// Skein content script — claude.ai
//
// Site-specific selectors only. All cross-site logic lives in
// content_common.js, which exposes __SkeinCommon.init(siteAdapter).
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

  if (!globalThis.__SkeinCommon) {
    console.warn("[skein] content_common.js not loaded; aborting claude.ai script");
    return;
  }

  globalThis.__SkeinCommon.init({
    siteName: "claude.ai",
    findPromptElement,
    findSendButton,
  });
})();
