import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Navbar } from "./components/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { Trades } from "./pages/Trades";
import { Settings } from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 30_000, // data dianggap fresh selama 30 detik
      refetchOnWindowFocus: false,
      refetchOnMount: false, // tidak refetch ulang saat komponen remount
    },
  },
});

type Page = "dashboard" | "trades" | "settings";

const NAV_LINKS: { id: Page; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "trades", label: "Trades" },
  { id: "settings", label: "Settings" },
];

function AppContent() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="min-h-screen bg-zinc-950">
      <div className="border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center">
          <div className="flex-1">
            <Navbar />
          </div>
          <div className="flex items-center gap-1 pr-6">
            {NAV_LINKS.map((link) => (
              <button
                key={link.id}
                onClick={() => setPage(link.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  page === link.id
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {link.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {page === "dashboard" && <Dashboard />}
      {page === "trades" && <Trades />}
      {page === "settings" && <Settings />}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
