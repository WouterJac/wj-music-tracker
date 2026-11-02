import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { registerServiceWorker } from "./pwa/register";
import "./styles.css";

// Only in a production build: in development the worker would serve stale files.
if (import.meta.env.PROD) registerServiceWorker();

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
