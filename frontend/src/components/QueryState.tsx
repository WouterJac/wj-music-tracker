import type { UseQueryResult } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";

import { NotFoundError } from "../api/library";

interface QueryStateProps<T> {
  query: UseQueryResult<T>;
  /** What is being loaded, in plain words, for the error message ("albums"). */
  noun: string;
  skeleton: ReactNode;
  /** Shown instead of the error when the server says the item does not exist. */
  notFound?: ReactNode;
  isEmpty: (data: T) => boolean;
  empty: ReactNode;
  children: (data: T) => ReactNode;
}

/** Renders the four states every data view needs: loading, error with retry, empty, success. */
export function QueryState<T>({
  query,
  noun,
  skeleton,
  notFound,
  isEmpty,
  empty,
  children,
}: QueryStateProps<T>) {
  const { error } = query;
  useEffect(() => {
    // The raw error is for developers; the screen shows a short message.
    if (error && !(error instanceof NotFoundError)) console.error(error);
  }, [error]);

  if (query.isPending) return skeleton;
  if (query.isError) {
    if (notFound && query.error instanceof NotFoundError) {
      return <div className="state">{notFound}</div>;
    }
    return (
      <div className="state state-error" role="alert">
        <p>{`Could not load ${noun}. Check that the backend is running.`}</p>
        <button type="button" onClick={() => void query.refetch()}>
          Try again
        </button>
      </div>
    );
  }
  if (isEmpty(query.data)) return <div className="state">{empty}</div>;
  return <>{children(query.data)}</>;
}
