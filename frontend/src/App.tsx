import { useState, Suspense, lazy } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Navbar } from "./components/Navbar";
const Dashboard = lazy(() =>
  import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
);
const Trades = lazy(() =>
  import("./pages/Trades").then((m) => ({ default: m.Trades })),
);
const Settings = lazy(() =>
  import("./pages/Settings").then((m) => ({ default: m.Settings })),
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
      refetchOnWindowFocus: false,
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
      {/* Navbar dengan nav links */}
      <div className="border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center">
          <div className="flex-1">
            <Navbar />
          </div>
          {/* Nav links */}
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

      {/* Page content */}
      <Suspense fallback={<div className="p-4">Loading...</div>}>
        {page === "dashboard" && <Dashboard />}
        {page === "trades" && <Trades />}
        {page === "settings" && <Settings />}
      </Suspense>
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
