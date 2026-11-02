import { useSyncExternalStore } from "react";

const TOKEN_KEY = "wj-music-token";

let pairingNeeded = false;
const listeners = new Set<() => void>();

function notify(): void {
  listeners.forEach((listener) => {
    listener();
  });
}

function setPairingNeeded(value: boolean): void {
  if (pairingNeeded === value) return;
  pairingNeeded = value;
  notify();
}

// Storage can be blocked (private windows, site data off), so every access is guarded. Without it
// the app simply asks to pair again on each visit.
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Kept for this page load only, through the request that follows.
  }
}

function forgetToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing stored, nothing to forget.
  }
}

/** Forgets the token and the need to pair. */
export function clearAuth(): void {
  forgetToken();
  setPairingNeeded(false);
}

export function isPairingNeeded(): boolean {
  return pairingNeeded;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function usePairingNeeded(): boolean {
  return useSyncExternalStore(subscribe, isPairingNeeded);
}

/**
 * fetch for the API. Sends the access token when there is one. A 401 means the server wants
 * a token this browser does not have (or no longer has), so the app shows the pairing screen.
 */
export async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const token = getToken();
  let response: Response;
  if (token === null) {
    response = init === undefined ? await fetch(input) : await fetch(input, init);
  } else {
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${token}`);
    response = await fetch(input, { ...init, headers });
  }
  if (response.status === 401) {
    forgetToken();
    setPairingNeeded(true);
  }
  return response;
}

/** Trades the one-time code from `wj-music pair` for the access token, and keeps the token. */
export async function pair(code: string): Promise<void> {
  const response = await fetch("/api/pair", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (response.status === 401) {
    throw new Error("That code is wrong or has expired. Run wj-music pair for a new one.");
  }
  if (response.status === 429) {
    throw new Error("Too many attempts. Wait a minute and try again.");
  }
  const body: unknown = response.ok ? await response.json() : null;
  if (
    typeof body !== "object" ||
    body === null ||
    !("token" in body) ||
    typeof body.token !== "string"
  ) {
    throw new Error("Could not pair. Check that the server is running.");
  }
  setToken(body.token);
  setPairingNeeded(false);
}
