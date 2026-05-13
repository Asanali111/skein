"use client";

import { useState } from "react";

const INSTALL = `pip install skein
cd your-project
skein up`;

export default function InstallBlock() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(INSTALL);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // noop
    }
  };

  return (
    <section className="py-24 md:py-32 border-t border-divider">
      <div className="max-w-content mx-auto px-6">
        <h2 className="font-serif text-3xl md:text-5xl font-medium tracking-tight text-fg">
          Install in five seconds.
        </h2>

        <div className="mt-10 relative rounded-lg border border-divider bg-fg text-bg/95 font-mono text-sm md:text-base shadow-sm overflow-hidden">
          <div className="flex items-center justify-between border-b border-white/10 px-5 py-2">
            <span className="text-xs uppercase tracking-[0.18em] text-bg/60">
              shell
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="text-xs uppercase tracking-wider text-bg/70 hover:text-brand transition"
              aria-label="Copy install commands"
            >
              {copied ? "copied" : "copy"}
            </button>
          </div>
          <pre className="px-5 py-5 leading-relaxed whitespace-pre overflow-x-auto">
            {INSTALL.split("\n").map((line, i) => (
              <div key={i}>
                <span className="text-brand select-none">$ </span>
                {line}
              </div>
            ))}
          </pre>
        </div>

        <p className="mt-6 max-w-2xl text-base text-muted leading-relaxed">
          Detects every installed LLM client (Claude Code, Cursor, Codex, Gemini
          CLI, Antigravity, opencode, VS Code). Writes their MCP configs. Starts
          the daemon. Around five seconds.
        </p>
        <p className="mt-2 text-sm text-muted">
          Need help?{" "}
          <code className="font-mono text-sm text-fg">skein doctor</code> checks
          everything.
        </p>
      </div>
    </section>
  );
}
