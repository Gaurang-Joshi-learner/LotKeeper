import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import { ToastProvider } from "./components/Toasts";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: true, staleTime: 5_000 } },
});

// Demo build (VITE_DEMO=1): in-browser fake API + MemoryRouter (a hosted preview can't use URL paths).
const DEMO = !!import.meta.env.VITE_DEMO;
const Router = DEMO ? MemoryRouter : BrowserRouter;

async function boot() {
  if (DEMO) (await import("./demo/mockApi")).installMockApi();
  render();
}

function render() {
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Router>
        <ToastProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ToastProvider>
      </Router>
    </QueryClientProvider>
  </React.StrictMode>,
);
}

boot();
