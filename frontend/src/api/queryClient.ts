import { QueryClient } from "@tanstack/react-query";

import { NotFoundError } from "./library";

const MAX_RETRIES = 2;

/** A missing item stays missing, so only other failures are worth asking for again. */
export function shouldRetry(failureCount: number, error: Error): boolean {
  return !(error instanceof NotFoundError) && failureCount < MAX_RETRIES;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: shouldRetry } } });
}
