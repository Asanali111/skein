export default function Footer() {
  return (
    <footer className="border-t border-divider py-12">
      <div className="max-w-content mx-auto px-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between text-sm text-muted">
        <p>MIT licensed · No telemetry · Local-first</p>
        <p className="flex flex-wrap gap-x-5 gap-y-1">
          <a
            href="https://github.com/Asanali111/skein"
            target="_blank"
            rel="noopener noreferrer"
            className="brand-link"
          >
            GitHub
          </a>
          <span className="text-divider">·</span>
          <span>
            Built by{" "}
            <a
              href="https://github.com/Asanali111"
              target="_blank"
              rel="noopener noreferrer"
              className="brand-link"
            >
              @asanali
            </a>
          </span>
        </p>
      </div>
    </footer>
  );
}
