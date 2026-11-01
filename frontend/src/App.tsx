import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { HealthStatus } from "./features/health/HealthStatus";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <main>
        <h1>WJ Music Tracker</h1>
        <HealthStatus />
      </main>
    </QueryClientProvider>
  );
}
