function TranscriptLine({
  num,
  tool,
  highlight = false,
}: {
  num: number;
  tool: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-3 font-mono text-xs md:text-sm">
      <span className="text-muted/70 w-5 shrink-0">{num}.</span>
      <span className={highlight ? "text-brand font-medium" : "text-fg/80"}>
        {tool}
      </span>
    </div>
  );
}

export default function DogfoodCallout() {
  return (
    <section className="py-24 md:py-32 border-t border-divider">
      <div className="max-w-content mx-auto px-6">
        <p className="text-xs uppercase tracking-[0.18em] text-brand mb-4">
          Iter 18 · verified
        </p>
        <h2 className="font-serif text-3xl md:text-5xl font-medium tracking-tight text-fg">
          Claude Sonnet now reaches for Skein first.
        </h2>
        <p className="mt-6 max-w-2xl text-lg text-muted">
          A real headless <span className="font-mono text-sm">claude -p</span>{" "}
          run against this project. With Skein installed, Sonnet picks the
          context bus over <span className="font-mono text-sm">read_file</span>{" "}
          before any source file is opened.
        </p>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {/* Without */}
          <div className="rounded-lg border border-divider bg-white p-6">
            <p className="text-xs uppercase tracking-[0.18em] text-muted mb-4">
              Without Skein
            </p>
            <div className="space-y-2">
              <TranscriptLine num={1} tool="read_file  README.md" />
              <TranscriptLine num={2} tool="read_file  AGENTS.md" />
              <TranscriptLine num={3} tool="list_dir   skein/" />
              <TranscriptLine num={4} tool="read_file  pyproject.toml" />
              <TranscriptLine num={5} tool="read_file  storage.py" />
              <TranscriptLine num={6} tool="grep       TODO|FIXME" />
            </div>
            <p className="mt-5 text-xs text-muted">
              Six round-trips. ~3000+ tokens. Misses the <em>why</em>.
            </p>
          </div>

          {/* With */}
          <div className="rounded-lg border border-brand/40 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.18em] text-brand mb-4">
              With Skein
            </p>
            <div className="space-y-2">
              <TranscriptLine num={1} tool="ToolSearch" />
              <TranscriptLine
                num={2}
                tool="mcp__skein__project_briefing"
                highlight
              />
              <TranscriptLine num={3} tool="mcp__skein__recall" highlight />
            </div>

            <blockquote className="mt-6 border-l-2 border-brand/40 pl-4 font-serif italic text-sm text-fg/90">
              &ldquo;Let me start by calling the Skein tools as instructed.&rdquo;
              <footer className="mt-2 not-italic font-sans text-xs text-muted">
                — Sonnet&rsquo;s first thinking block, verbatim
              </footer>
            </blockquote>
          </div>
        </div>

        <p className="mt-8 text-sm text-muted">
          Stream-json transcript reproducible from{" "}
          <code className="font-mono text-xs">docs/dogfood-iter-18.md</code>.
        </p>
      </div>
    </section>
  );
}
