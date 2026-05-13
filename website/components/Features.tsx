const FEATURES = [
  {
    title: "Hybrid recall",
    body: "BM25 + vector + RRF. Top-K in under 100ms, around 30 tokens per fragment. One recall typically replaces five read_file calls.",
  },
  {
    title: "Decision archaeology",
    body: "Supersede chains let you trace why a decision changed, across tools, across sessions, across weeks.",
  },
  {
    title: "Cross-tool handoff",
    body: "Write a decision in Claude Code. Recall it in Cursor a week later. Same scope, same memory.",
  },
  {
    title: "Zero-config bootstrap",
    body: "skein up detects every installed LLM client (Claude Code, Cursor, Codex, Gemini CLI, Antigravity, opencode, VS Code) and wires it. Five seconds.",
  },
];

export default function Features() {
  return (
    <section className="py-24 md:py-32 border-t border-divider">
      <div className="max-w-content mx-auto px-6">
        <h2 className="font-serif text-3xl md:text-5xl font-medium tracking-tight text-fg">
          What Skein gives you.
        </h2>

        <div className="mt-14 grid gap-x-10 gap-y-12 md:grid-cols-2">
          {FEATURES.map((f) => (
            <div key={f.title}>
              <h3 className="font-serif text-xl md:text-2xl font-medium text-fg">
                {f.title}
              </h3>
              <p className="mt-3 text-base text-muted leading-relaxed">
                {f.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
