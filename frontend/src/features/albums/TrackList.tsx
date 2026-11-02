import { Link } from "react-router-dom";

import type { Track } from "../../api/library";
import { formatDuration } from "../../lib/format";

/** Tracks grouped by disc, in disc order. A missing disc tag counts as disc 1. */
function groupByDisc(tracks: Track[]): [number, Track[]][] {
  const discs = new Map<number, Track[]>();
  for (const track of tracks) {
    const disc = track.disc ?? 1;
    discs.set(disc, [...(discs.get(disc) ?? []), track]);
  }
  return [...discs.entries()].sort(([a], [b]) => a - b);
}

function TrackTable({ tracks }: { tracks: Track[] }) {
  return (
    <table className="track-table">
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Title</th>
          <th scope="col">Duration</th>
          <th scope="col">Lyrics</th>
        </tr>
      </thead>
      <tbody>
        {tracks.map((track) => (
          <tr key={track.id}>
            <td className="track-number">{track.number === null ? "–" : String(track.number)}</td>
            <td>
              <Link to={`/tracks/${String(track.id)}`}>{track.title ?? "Untitled track"}</Link>
            </td>
            <td className="track-duration">{formatDuration(track.duration_seconds)}</td>
            <td className="track-lyrics">{track.has_lyrics ? "Lyrics" : ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function TrackList({ tracks }: { tracks: Track[] }) {
  const discs = groupByDisc(tracks);
  if (discs.length === 1) return <TrackTable tracks={tracks} />;
  return (
    <>
      {discs.map(([disc, discTracks]) => (
        <section key={disc}>
          <h2>{`Disc ${String(disc)}`}</h2>
          <TrackTable tracks={discTracks} />
        </section>
      ))}
    </>
  );
}
