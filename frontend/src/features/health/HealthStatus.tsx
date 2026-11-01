import { useQuery } from "@tanstack/react-query";

import { fetchHealth } from "../../api/client";

export function HealthStatus() {
  const health = useQuery({ queryKey: ["health"], queryFn: fetchHealth });

  if (health.isPending) {
    return <p role="status">Checking the server…</p>;
  }
  if (health.isError) {
    return <p role="alert">Could not reach the server. Check that the backend is running.</p>;
  }
  return (
    <div>
      <p>{`Server is ${health.data.status}`}</p>
      <p>{`Version ${health.data.version}`}</p>
    </div>
  );
}
