/** A positive whole number from a URL parameter, or undefined when absent or invalid. */
export function toPositiveInt(value: string | null): number | undefined {
  if (value === null) return undefined;
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : undefined;
}

/** Builds the next search params, dropping empty values so URLs stay short and clean. */
export function withParam(
  current: URLSearchParams,
  changes: Record<string, string | number | undefined>,
): URLSearchParams {
  const next = new URLSearchParams(current);
  for (const [key, value] of Object.entries(changes)) {
    if (value === undefined || value === "") next.delete(key);
    else next.set(key, String(value));
  }
  return next;
}
