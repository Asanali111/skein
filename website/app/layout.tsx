import type { Metadata } from "next";
import { Inter, Source_Serif_4, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Skein — the local context bus for every coding LLM",
  description:
    "One memory, shared across Claude Code, Cursor, Codex, Gemini CLI, and more. Local-first. MIT-licensed. Native MCP.",
  metadataBase: new URL("https://skein.dev"),
  openGraph: {
    title: "Skein",
    description:
      "The local context bus for every coding LLM. One memory, shared across Claude Code, Cursor, Codex, Gemini CLI, and more.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${mono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
