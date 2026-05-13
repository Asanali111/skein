const COLUMNS = [
  "Local-first",
  "MIT licensed",
  "Native MCP",
  "Cross-tool out of the box",
  "Decision supersede chain",
];

const ROWS: Array<{ name: string; values: Array<boolean | "tbd"> }> = [
  { name: "Skein", values: [true, true, true, true, true] },
  { name: "Mem0", values: ["tbd", "tbd", "tbd", "tbd", "tbd"] },
  { name: "Letta", values: ["tbd", "tbd", "tbd", "tbd", "tbd"] },
  { name: "Hindsight", values: ["tbd", "tbd", "tbd", "tbd", "tbd"] },
];

function Cell({ value }: { value: boolean | "tbd" }) {
  if (value === true) {
    return (
      <span className="text-brand" aria-label="yes">
        ✓
      </span>
    );
  }
  if (value === false) {
    return (
      <span className="text-muted/60" aria-label="no">
        —
      </span>
    );
  }
  return (
    <span className="text-muted/60 text-xs" aria-label="to be determined">
      tbd
    </span>
  );
}

export default function Comparison() {
  return (
    <section className="py-24 md:py-32 border-t border-divider">
      <div className="max-w-content mx-auto px-6">
        <h2 className="font-serif text-3xl md:text-5xl font-medium tracking-tight text-fg">
          How Skein stacks up.
        </h2>
        <p className="mt-6 max-w-2xl text-lg text-muted">
          Head-to-head benchmarks against Mem0, Letta, and Hindsight are coming.
          We&rsquo;re only filling in cells we can defend with numbers.
        </p>

        <div className="mt-12 overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-divider">
                <th className="py-3 pr-4 font-medium text-muted text-xs uppercase tracking-[0.12em]">
                  Tool
                </th>
                {COLUMNS.map((c) => (
                  <th
                    key={c}
                    className="py-3 px-3 font-medium text-muted text-xs uppercase tracking-[0.12em] text-center"
                  >
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row, i) => (
                <tr
                  key={row.name}
                  className={
                    i === 0
                      ? "border-b border-divider bg-bg/40 font-medium"
                      : "border-b border-divider/60"
                  }
                >
                  <td className="py-4 pr-4 text-fg">{row.name}</td>
                  {row.values.map((v, idx) => (
                    <td key={idx} className="py-4 px-3 text-center text-base">
                      <Cell value={v} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-xs text-muted">
          Honest no-knowledge over made-up numbers. Bench results land soon.
        </p>
      </div>
    </section>
  );
}
