import { useQuery } from "@tanstack/react-query";

import { fetchStats, type Bucket, type LibraryStats } from "../../api/library";
import { BarChart } from "../../components/BarChart";
import { QueryState } from "../../components/QueryState";
import { Skeleton } from "../../components/Skeleton";
import { formatTotalDuration } from "../../lib/format";

export function StatsPage() {
  const stats = useQuery({ queryKey: ["stats"], queryFn: fetchStats });
  return (
    <>
      <h1>Statistics</h1>
      <QueryState
        query={stats}
        noun="statistics"
        skeleton={<Skeleton label="Loading statistics" className="tiles" count={4} />}
        isEmpty={(data) => data.tracks === 0}
        empty={
          <p>
            No tracks yet. Run <code>wj-music scan</code> to read your music folder.
          </p>
        }
      >
        {(data) => <Dashboard stats={data} />}
      </QueryState>
    </>
  );
}

function Dashboard({ stats }: { stats: LibraryStats }) {
  const hiresShare = Math.round((stats.hires_tracks / stats.tracks) * 100);
  const hiresNote = `${String(stats.hires_tracks)} hi-res ${stats.hires_tracks === 1 ? "track" : "tracks"}`;
  return (
    <>
      <section aria-labelledby="totals-heading">
        <h2 id="totals-heading" className="visually-hidden">
          Totals
        </h2>
        <dl className="tiles">
          <Tile label="Tracks" value={String(stats.tracks)} />
          <Tile label="Albums" value={String(stats.albums)} />
          <Tile label="Artists" value={String(stats.artists)} />
          <Tile label="Playing time" value={formatTotalDuration(stats.total_duration_seconds)} />
          <Tile label="Hi-res share" value={`${String(hiresShare)}%`} note={hiresNote} />
        </dl>
      </section>
      <section className="charts" aria-label="Charts">
        <Chart title="Albums by decade" unit="album" items={stats.albums_by_decade} />
        <Chart title="Albums by year" unit="album" items={stats.albums_by_year} />
        <Chart title="Tracks by format" unit="track" items={stats.tracks_by_format} />
        <Chart title="Tracks by channels" unit="track" items={stats.tracks_by_channels} />
        <Chart title="Tracks by genre" unit="track" items={stats.tracks_by_genre} />
        <Chart title="Tracks per album" unit="album" items={stats.albums_by_track_count} />
        <Chart title="Album length" unit="album" items={stats.albums_by_length} />
        <BarChart
          title="Top artists"
          unit="track"
          items={stats.top_artists.map((artist) => ({
            label: artist.name,
            count: artist.tracks,
            href: `/artists/${String(artist.id)}`,
          }))}
        />
      </section>
    </>
  );
}

function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="tile">
      <dt>{label}</dt>
      <dd>
        <span className="tile-value">{value}</span>
        {note && <span className="tile-note">{note}</span>}
      </dd>
    </div>
  );
}

/** A chart is skipped when it has nothing to show, for example genres when no file is tagged. */
function Chart({ title, unit, items }: { title: string; unit: string; items: Bucket[] }) {
  return items.length === 0 ? null : <BarChart title={title} unit={unit} items={items} />;
}
