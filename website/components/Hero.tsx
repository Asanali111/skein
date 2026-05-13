"use client";

import { useState } from "react";

const INSTALL_CMD = "pip install skein && skein up";

const CLIENTS = [
  "Claude Code",
  "Cursor",
  "Codex",
  "Gemini CLI",
  "Antigravity",
  "opencode",
  "VS Code / Copilot",
];

export default function Hero() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(INSTALL_CMD);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable — silent fallback.
    }
  };

  return (
    <section className="pt-24 pb-32 md:pt-32 md:pb-40 fade-in">
      <div className="max-w-content mx-auto px-6 text-center">
        <h1 className="font-serif text-5xl sm:text-6xl md:text-hero font-medium tracking-tight text-fg">
          Skein
        </h1>

        <p className="mt-8 md:mt-10 mx-auto max-w-2xl font-serif text-xl md:text-2xl leading-snug text-fg">
          The local context bus for every coding LLM.
        </p>
        <p className="mt-3 mx-auto max-w-xl text-base md:text-lg text-muted">
          One memory, shared across Claude Code, Cursor, Codex, Gemini CLI, and more.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4">
          <button
            type="button"
            onClick={handleCopy}
            className="group flex items-center gap-3 rounded-md border border-divider bg-white px-5 py-3 font-mono text-sm md:text-base text-fg shadow-sm transition hover:border-brand/40 hover:shadow"
            aria-label="Copy install command"
          >
            <span className="text-brand">$</span>
            <span>{INSTALL_CMD}</span>
            <span className="ml-1 text-xs uppercase tracking-wider text-muted group-hover:text-brand">
              {copied ? "copied" : "copy"}
            </span>
          </button>

          <a
            href="https://github.com/Asanali111/skein"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-muted brand-link"
          >
            View on GitHub →
          </a>
        </div>

        <div className="mt-20">
          <p className="text-xs uppercase tracking-[0.18em] text-muted">
            Wires up automatically with
          </p>
          <ul className="mt-5 flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-sm text-fg/80">
            {CLIENTS.map((c, i) => (
              <li key={c} className="flex items-center gap-6">
                <span>{c}</span>
                {i < CLIENTS.length - 1 && (
                  <span aria-hidden className="text-divider">
                    ·
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
