/** Registers the service worker after the page has loaded, so it never competes with first paint. */
export function registerServiceWorker(): void {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch((error: unknown) => {
      console.error(error);
    });
  });
}
