# Skein browser extension — experimental

A browser extension that injects local Skein context into prompts on
**claude.ai**, **chatgpt.com**, and **gemini.google.com**. Lives on
the `experiment/browser-extension` branch only — does **not** affect
the main `skein up` workflow.

Iter 30 shipped the claude.ai prototype. Iter 33 extracted the shared
hot-path logic into `content_common.js` and added content scripts for
ChatGPT and Gemini. Three sites, one shared core — future relevance /
recall fixes (like iter 32's token-waste skip) land in one file and
all three sites inherit.

## How to test it

### 1. Start an experimental daemon on port 8766

Your normal daemon on port 8765 keeps running and keeps serving Claude
Code / Cursor / Codex without interruption. The extension talks to
port 8766 by default.

```bash
cd ~/Documents/company-brain-experiment
PYTHONPATH=$(pwd) /Users/ameliomar/.skein/venv/bin/python3.12 \
    -m skein serve --port 8766 --host 127.0.0.1 > /tmp/skein_exp.log 2>&1 &

# verify it's up
curl -s http://127.0.0.1:8766/health
# → {"status":"ok","fragment_count":129,...}
```

If you'd rather have the extension talk to your prod daemon on 8765,
open the extension toolbar popup after install and change the
**Daemon** field to `http://127.0.0.1:8765`. But the production daemon
doesn't have the `/v1/pair-browser` endpoint yet — that ships on this
branch only — so pairing would fail. Use 8766 for now.

### 2. Load the extension in Chrome

1. Open `chrome://extensions` in Chrome (or `edge://extensions`,
   `brave://extensions` — anything Chromium-based works).
2. Toggle **Developer mode** on (top-right corner).
3. Click **Load unpacked**.
4. Pick this directory: `~/Documents/company-brain-experiment/extension/`.
5. Chrome should show "Skein for browser LLMs (experimental) · 0.0.1"
   in the extension list with a small purple-and-white S icon.

### 3. Pair + pick a scope

1. Click the Skein extension icon in the Chrome toolbar — opens the popup.
2. **Status** at the top should turn green:
   `✓ paired · N scope(s) available`.
   If it's red ("daemon unreachable"), the experimental daemon isn't
   running on 8766 — go back to step 1.
3. **Scope** dropdown — pick the project you want context for
   (e.g. `project:ameliomar`).
4. The **Inject context on send** checkbox is on by default. Leave it.
5. Click **Test recall** to confirm end-to-end works. You should see
   recall results render in the box below.

### 4. Use it on claude.ai / chatgpt.com / gemini.google.com

1. Open whichever site you want to test in a new tab:
   - `https://claude.ai/new`
   - `https://chatgpt.com/`
   - `https://gemini.google.com/app`
2. **Bottom-right corner** — you should see a dark floating badge:
   `● Skein  · project:ameliomar · 129 fragments`.
   Green dot = paired and ready. Yellow = no scope picked (open the
   popup). Red = daemon unreachable.
3. Open DevTools (Cmd-Opt-I) → Console tab → filter by `[skein]`.
   You'll see log lines as the extension boots.
4. Type a real question — something the LLM might benefit from project
   context for. e.g. *"how does the daemon handle the launchd race?"*
5. **Hit Enter (or click Send).**

What you should see happen, in this order:

- A small blue toast above the badge: `Skein → recalling context…`
- Within ~50 ms, a second toast: `Skein → injected N lines`
- The text in your message box updates — you can literally see a
  `[Skein context — auto-injected by browser extension ...]` block
  prepended to your original prompt.
- The message submits to Claude with the injected context attached.
- Claude responds using the context. Look for it referencing project
  decisions, file paths, or numbers it couldn't have known otherwise.

### 5. Verifying it's actually working (not just rendering)

Three independent signals:

**Signal 1 — DevTools console.**
Open Console, filter `[skein]`. You should see a chain like:
```
[skein] content script loaded for claude.ai
[skein] paired ✓ daemon= http://127.0.0.1:8766
[skein] intercept (keydown:Enter) for query: how does the daemon handle …
[skein] injecting 412 chars of context
```

**Signal 2 — daemon log.**
```bash
tail -f /tmp/skein_exp.log
```
You'll see `POST /v1/pair-browser` and `POST /mcp` lines fire each time
you submit a prompt.

**Signal 3 — Claude's response quality.**
Ask something only Skein could know (e.g. *"what did I decide about
the kickstart -k flag?"*). Without the extension, Claude has zero
context. With the extension on, Claude should answer specifically,
because the iter-28 perf decision fragment got injected.

## Turning it off

- **Per-message**: hold Shift+Enter to add a newline instead of submitting;
  the interceptor only fires on bare Enter. (Plus the toggle in popup.)
- **Per-session**: toolbar icon → uncheck **Inject context on send**.
- **Entirely**: `chrome://extensions` → toggle Skein off, or **Remove**.

## What's missing

This is still a prototype. Known limits:

- **No write-back.** The LLM's response isn't captured anywhere. A
  future iter will add a "Save to Skein" button on hover over assistant
  messages.
- **No streaming-aware feedback.** The "injected" toast disappears
  after 1.5 s; for long responses you can't go back and see exactly
  what got injected. (Console logs are the audit trail.)
- **DOM selector drift.** ChatGPT and Gemini ship UI changes
  frequently — selectors are written defensively (multiple fallbacks
  per site) but a hard breaking change will require a selector update.
  Check the DevTools console for `[skein] prompt element gone` if
  injection silently stops.

## What's safe

- Every request goes to `127.0.0.1` only. The extension makes zero
  outbound calls to anything except your local daemon.
- The extension reads your prompt text (it has to, to know what to
  recall) but never sends it anywhere except the daemon.
- The bearer token is stored in `chrome.storage.local`, sandboxed to
  this extension. Other websites can't read it.

## Tearing it down

```bash
# 1. Remove from Chrome
chrome://extensions → Skein → Remove

# 2. Stop the experimental daemon
pkill -f "skein serve --port 8766"

# 3. If you decide to abandon the experiment entirely:
cd ~/Documents/company-brain
git worktree remove ../company-brain-experiment
git branch -D experiment/browser-extension
git push origin --delete experiment/browser-extension
```

Your real daemon at port 8765 and all of `main` stay untouched the
entire time.
