const TOOLS = ["Claude Code", "Cursor", "Codex"];

function MemoryIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
    >
      <rect
        x="3"
        y="6"
        width="18"
        height="12"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.4"
        fill={filled ? "currentColor" : "none"}
        fillOpacity={filled ? 0.12 : 0}
      />
      <path
        d="M7 6V4M11 6V4M15 6V4M19 6V4M7 20v-2M11 20v-2M15 20v-2M19 20v-2"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ToolBox({
  label,
  connected,
}: {
  label: string;
  connected: boolean;
}) {
  return (
    <div
      className={`flex flex-col items-center gap-2 rounded-md border px-4 py-4 text-sm transition ${
        connected
          ? "border-brand/30 bg-white text-fg"
          : "border-divider bg-white text-fg"
      }`}
    >
      <span className="font-medium">{label}</span>
      <span className={connected ? "text-brand" : "text-muted/60"}>
        <MemoryIcon filled={connected} />
      </span>
    </div>
  );
}

export default function Problem() {
  return (
    <section className="py-24 md:py-32 border-t border-divider">
      <div className="max-w-content mx-auto px-6">
        <h2 className="font-serif text-3xl md:text-5xl font-medium tracking-tight text-fg">
          Every LLM tool has its own memory.
          <br />
          <span className="text-muted">They don&rsquo;t talk.</span>
        </h2>

        <p className="mt-6 max-w-2xl text-lg text-muted">
          You explain caching to Claude Code. Then to Cursor. Then to Codex.
          Every switch resets the context.
        </p>

        <div className="mt-16 grid gap-12 md:grid-cols-2 md:gap-10">
          {/* Before */}
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-muted mb-5">
              Before
            </p>
            <div className="rounded-lg border border-divider bg-bg/50 p-6">
              <div className="grid grid-cols-3 gap-3">
                {TOOLS.map((t) => (
                  <ToolBox key={t} label={t} connected={false} />
                ))}
              </div>
              <p className="mt-5 text-center text-xs text-muted">
                Three siloed memories. Nothing is shared.
              </p>
            </div>
          </div>

          {/* After */}
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-brand mb-5">
              With Skein
            </p>
            <div className="rounded-lg border border-brand/30 bg-bg/50 p-6">
              <div className="grid grid-cols-3 gap-3">
                {TOOLS.map((t) => (
                  <ToolBox key={t} label={t} connected={true} />
                ))}
              </div>

              <div className="relative mt-4 flex justify-center">
                {/* Connecting lines via SVG */}
                <svg
                  viewBox="0 0 300 60"
                  className="h-12 w-full max-w-[300px]"
                  aria-hidden="true"
                >
                  <line
                    x1="50"
                    y1="0"
                    x2="150"
                    y2="50"
                    stroke="#d97757"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                  <line
                    x1="150"
                    y1="0"
                    x2="150"
                    y2="50"
                    stroke="#d97757"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                  <line
                    x1="250"
                    y1="0"
                    x2="150"
                    y2="50"
                    stroke="#d97757"
                    strokeWidth="1"
                    opacity="0.5"
                  />
                </svg>
              </div>

              <div className="flex justify-center">
                <div className="rounded-md border border-brand bg-white px-5 py-2 text-sm font-medium text-brand shadow-sm">
                  Skein
                </div>
              </div>
              <p className="mt-5 text-center text-xs text-muted">
                One memory. Read it from anywhere.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
