import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChemSearch — Chemical Reaction Workspace",
  description: "Deterministic reaction simulation, ReactionT5 prediction, and RDKit structure visualization.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
