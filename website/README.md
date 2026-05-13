# Skein landing site

Static Next.js 14 (App Router) marketing site for [Skein](https://github.com/Asanali111/skein).

## Develop

```bash
npm install
npm run dev
```

Then open http://localhost:3000.

## Build

```bash
npm run build
```

Produces `.next/` (deployable to Vercel with zero config).

## Stack

- Next.js 14 (App Router)
- React 18 + TypeScript
- TailwindCSS 3 with custom palette tokens (`bg`, `fg`, `muted`, `brand`, `divider`)
- Fonts loaded via `next/font/google`: Source Serif 4 (headings), Inter (body), JetBrains Mono (code)

## Structure

```
website/
  app/
    layout.tsx       # Fonts + metadata
    page.tsx         # Composes sections
    globals.css      # Tailwind + a couple of CSS vars
  components/
    Hero.tsx
    Problem.tsx
    DogfoodCallout.tsx
    Features.tsx
    InstallBlock.tsx
    Comparison.tsx
    Footer.tsx
```

## Deployment

Vercel auto-detects Next.js. No env vars required.

To deploy manually:

```bash
npm run build
npx vercel --prod
```

## Conventions

- All marketing claims are defensible. Numbers come from `docs/dogfood-iter-18.md` and `HANDOFF.md`.
- No analytics, no trackers, no third-party scripts.
- Fonts loaded via `next/font` only — no runtime CDN font requests.
