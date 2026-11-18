import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IntelliGate — Enterprise Multi-Provider LLM Gateway",
  description: "Unified AI Infrastructure, Intelligent Routing, Distributed Rate Limiting & Cost Governance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}

