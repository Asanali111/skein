// Skein content script — claude.ai
//
// Job: watch the prompt textarea. On submit (Enter without Shift, or click
// of the send button), pause, call Skein recall via the background worker,
// prepend the result as a `[Skein context]` block to the textarea content,
// then re-fire the submit.
//
// Detection strategy: claude.ai uses a contenteditable div (NOT a real
// <textarea>) for the prompt. We MutationObserver the body until we find it
// and rebind our listeners every time React re-renders the input area.
//
// Visible feedback (so the user knows it works):
//   1. Floating badge bottom-right: "Skein · project:foo · ✓ 129 fragments"
//      — turns red if daemon unreachable
//   2. A tiny inline "Skein → injecting…" toast above the prompt during
//      the ~50 ms recall round-trip
//   3. The user can literally see the injected `[Skein context]` block
//      appear at the top of their message before send
//   4. DevTools console logs at every step (filter by "[skein]")

(() => {
  const LOG = (...args) => console.info("[skein]", ...args);
  const WARN = (...args) => console.warn("[skein]", ...args);

  // ---- runtime state cached from background ---------------------------

  let cached = { enabled: true, activeScope: null, daemonUrl: null, bearerToken: null };

  async function refreshState() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: "getState" }, (r) => {
        if (r && r.ok) cached = r.state;
        resolve(cached);
      });
    });
  }

  // ---- floating badge -------------------------------------------------

  const badge = document.createElement("div");
  badge.className = "skein-badge";
  badge.innerHTML = `
    <span class="skein-dot"></span>
    <span class="skein-label">Skein</span>
    <span class="skein-detail">…</span>
  `;
  badge.title = "Click to open the Skein extension popup";
  badge.addEventListener("click", () => {
    // Can't open the popup programmatically (Chrome MV3 limitation); just
    // surface a hint in console + flash the badge so the user notices.
    LOG("click the toolbar icon to open settings");
    badge.classList.add("skein-flash");
    setTimeout(() => badge.classList.remove("skein-flash"), 400);
  });
  document.documentElement.appendChild(badge);

  function setBadge({ kind = "ok", label = "Skein", detail = "" } = {}) {
    badge.classList.remove("skein-ok", "skein-warn", "skein-err");
    badge.classList.add(`skein-${kind}`);
    badge.querySelector(".skein-label").textContent = label;
    badge.querySelector(".skein-detail").textContent = detail;
  }

  // ---- transient "injecting" toast above the prompt -------------------

  function flashToast(msg, ms = 1500) {
    const t = document.createElement("div");
    t.className = "skein-toast";
    t.textContent = msg;
    document.documentElement.appendChild(t);
    setTimeout(() => t.remove(), ms);
  }

  // ---- find the prompt input ------------------------------------------

  // claude.ai's prompt is a contenteditable <div> with class
  // "ProseMirror" (or similar — exact class names are volatile, so we
  // probe a few selectors). The send button is the only <button> with
  // aria-label="Send Message" or similar.
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

  // ---- text manipulation on a contenteditable -------------------------

  function getPromptText(el) {
    return el ? el.innerText || el.textContent || "" : "";
  }

  function setPromptText(el, text) {
    // ProseMirror requires us to dispatch InputEvent for React's controlled
    // state to pick it up. Direct textContent assignment alone won't fire
    // the change handlers claude.ai relies on. So we:
    //   1. Select all, delete
    //   2. Insert text via document.execCommand (still the highest-
    //      compatibility way to inject into contenteditable that
    //      ProseMirror notices)
    el.focus();
    document.execCommand("selectAll", false, null);
    document.execCommand("delete", false, null);
    document.execCommand("insertText", false, text);
  }

  // ---- the recall call -----------------------------------------------

  function callRecall(query) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { type: "recall", query, limit: 5 },
        (r) => resolve(r),
      );
    });
  }

  // Render the daemon's recall response into a tight context block.
  // The response shape from skein.mcp is:
  //   { content: [{ type: "text", text: "<rendered>" }] }
  // The "rendered" form is already designed for the LLM to read.
  function formatContextBlock(recallResult, originalQuery) {
    if (!recallResult || !recallResult.content || !recallResult.content[0]) {
      return null;
    }
    const text = recallResult.content[0].text;
    if (!text || !text.trim()) return null;
    if (/^no relevant context found/i.test(text.trim())) return null;
    if (/^no fragment in skein matches/i.test(text.trim())) return null;
    // The block is wrapped in [skein context] tags so claude.ai's model
    // can clearly separate injected context from the user's own words.
    return [
      `[Skein context — auto-injected by browser extension for query: "${originalQuery.slice(0, 80)}"]`,
      text.trim(),
      `[/Skein context]`,
      "",
      "",
    ].join("\n");
  }

  // ---- submit interception --------------------------------------------

  let interceptingNow = false;

  async function handleSubmitAttempt(originalEvent, source) {
    if (interceptingNow) return; // re-entry guard
    if (!cached.enabled) {
      LOG("disabled — passing through");
      return;
    }
    if (!cached.activeScope) {
      WARN("no active scope set in popup; passing through");
      flashToast("Skein: open the toolbar icon and pick a scope");
      return;
    }
    const promptEl = findPromptElement();
    if (!promptEl) {
      WARN("prompt element gone; passing through");
      return;
    }
    const original = getPromptText(promptEl).trim();
    if (!original || original.length < 4) {
      LOG("prompt too short; passing through");
      return;
    }
    // Already has a Skein block (e.g. user re-submitted after we injected);
    // don't double-inject.
    if (original.startsWith("[Skein context")) {
      LOG("already has Skein block; passing through");
      return;
    }

    // STOP this submit, do the recall, modify text, then re-trigger.
    LOG(`intercept (${source}) for query:`, original.slice(0, 80));
    originalEvent.preventDefault();
    originalEvent.stopImmediatePropagation();
    interceptingNow = true;
    flashToast("Skein → recalling context…");

    try {
      const r = await callRecall(original);
      if (!r || !r.ok) {
        WARN("recall failed; passing through:", r && r.error);
        flashToast(`Skein: recall failed (${r && r.error || "unknown"})`);
        // Re-trigger original submit (Enter keydown) on the prompt.
        retriggerSubmit(promptEl);
        return;
      }
      const block = formatContextBlock(r.result, original);
      if (!block) {
        LOG("no high-signal fragments; passing through");
        flashToast("Skein: no relevant context found");
        retriggerSubmit(promptEl);
        return;
      }
      LOG("injecting", block.length, "chars of context");
      setPromptText(promptEl, block + original);
      flashToast(`Skein → injected ${block.split("\n").length} lines`);
      // Wait a tick for React to re-render, then submit.
      setTimeout(() => retriggerSubmit(promptEl), 80);
    } catch (err) {
      WARN("error during intercept:", err);
      flashToast(`Skein error: ${err.message || err}`);
      retriggerSubmit(promptEl);
    } finally {
      // Release the re-entry guard a moment after the resubmit so it
      // doesn't catch our own simulated event.
      setTimeout(() => { interceptingNow = false; }, 300);
    }
  }

  function retriggerSubmit(promptEl) {
    const send = findSendButton();
    if (send && !send.disabled) {
      send.click();
      return;
    }
    // Fallback: dispatch a synthetic Enter keydown on the prompt.
    const ev = new KeyboardEvent("keydown", {
      key: "Enter", code: "Enter", keyCode: 13, which: 13,
      bubbles: true, cancelable: true,
    });
    promptEl.dispatchEvent(ev);
  }

  // ---- attach listeners -----------------------------------------------

  // Capture-phase so we run BEFORE claude.ai's own React handlers.
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey || e.metaKey || e.ctrlKey || e.altKey) return;
    const promptEl = findPromptElement();
    if (!promptEl || !promptEl.contains(e.target)) return;
    handleSubmitAttempt(e, "keydown:Enter");
  }, true);

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const send = findSendButton();
    if (btn !== send) return;
    handleSubmitAttempt(e, "click:sendButton");
  }, true);

  // ---- bootstrap ------------------------------------------------------

  async function bootstrap() {
    setBadge({ kind: "warn", detail: "initialising" });
    await refreshState();

    if (!cached.bearerToken) {
      // Ask background to pair now.
      LOG("no token yet; requesting pair");
      await new Promise((resolve) => chrome.runtime.sendMessage({ type: "pair" }, resolve));
      await refreshState();
    }

    // Try a project_briefing to confirm daemon is healthy AND get a
    // fragment count for the badge.
    chrome.runtime.sendMessage({ type: "projectBriefing" }, (r) => {
      if (r && r.ok) {
        const txt = (r.result && r.result.content && r.result.content[0] && r.result.content[0].text) || "";
        // Try to pull the fragment count out of the briefing text.
        const m = txt.match(/(\d+)\s+fragments?/i);
        const count = m ? `${m[1]} fragments` : "ready";
        setBadge({ kind: "ok", detail: `${cached.activeScope || "no scope"} · ${count}` });
      } else if (!cached.activeScope) {
        setBadge({ kind: "warn", detail: "pick a scope ▸ toolbar" });
      } else {
        setBadge({ kind: "err", detail: `daemon unreachable — ${r && r.error || "?"}` });
      }
    });
  }

  // React-heavy SPAs may finish rendering long after document_idle. Give
  // claude.ai a couple of seconds to settle, then bootstrap.
  setTimeout(bootstrap, 800);

  // Keep cached state fresh — popup changes should reflect here without
  // a page reload.
  chrome.storage.onChanged.addListener((changes) => {
    LOG("state changed:", Object.keys(changes));
    refreshState();
  });

  LOG("content script loaded for", location.host);
})();
