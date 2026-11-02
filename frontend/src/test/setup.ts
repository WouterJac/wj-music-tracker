import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import { clearAuth } from "../api/auth";

// Vitest globals are off, so Testing Library cannot register its own cleanup.
afterEach(cleanup);
// A token or pairing request from one test must not leak into the next.
afterEach(clearAuth);
