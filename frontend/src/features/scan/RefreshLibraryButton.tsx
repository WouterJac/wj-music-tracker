import { useMutation, useQueryClient } from "@tanstack/react-query";

import { runScan, type ScanSummary } from "../../api/library";

/** A short account of what the scan found. */
function describe(summary: ScanSummary): string {
  const library = `Library: ${String(summary.tracks)} tracks, ${String(summary.albums)} albums, ${String(summary.artists)} artists.`;
  const changes =
    summary.added + summary.changed + summary.removed === 0
      ? "Nothing changed."
      : `Added ${String(summary.added)}, changed ${String(summary.changed)}, removed ${String(summary.removed)}.`;
  const unreadable =
    summary.errors > 0
      ? ` ${String(summary.errors)} ${summary.errors === 1 ? "file" : "files"} could not be read.`
      : "";
  return `${changes}${unreadable} ${library}`;
}

export function RefreshLibraryButton() {
  const queryClient = useQueryClient();
  const scan = useMutation({
    mutationFn: runScan,
    // Whatever is on screen may now be out of date, so every query is refetched.
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  return (
    <div className="refresh-library">
      <button
        type="button"
        disabled={scan.isPending}
        onClick={() => {
          scan.mutate();
        }}
      >
        {scan.isPending ? "Scanning…" : "Refresh library"}
      </button>
      {scan.isSuccess && <p role="status">{describe(scan.data)}</p>}
      {scan.isError && <p role="alert">{scan.error.message}</p>}
    </div>
  );
}
