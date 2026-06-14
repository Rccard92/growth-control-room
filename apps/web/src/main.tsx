import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import "@xyflow/react/dist/style.css";
import "./styles/tokens.css";
import "./styles/ui.css";
import "./index.css";
import "./styles/foundation.css";
import "./styles/shopify-dashboard.css";
import "./styles/content-seo.css";
import "./styles/brand-intelligence.css";
import "./styles/date-range-selector.css";
import "./styles/ai-usage.css";
import { App } from "./App";
import { queryClient } from "./lib/queryClient";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
