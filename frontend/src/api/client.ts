export interface Health {
  status: string;
  version: string;
}

function isHealth(value: unknown): value is Health {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    typeof value.status === "string" &&
    "version" in value &&
    typeof value.version === "string"
  );
}

export async function fetchHealth(): Promise<Health> {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error(`/health responded with ${String(response.status)}`);
  }
  const body: unknown = await response.json();
  if (!isHealth(body)) {
    throw new Error("/health returned an unexpected body");
  }
  return body;
}
